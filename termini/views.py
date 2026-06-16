from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from .models import Pacijent, Doktor, Termin, Pregled
from .serializers import (
    PregledSerializer, TerminSerializer, ZakazivanjeSerializer,
    RegistracijaSerializer, DoktorSerializer, PacijentSerializer
)


def get_user_type(user):
    if hasattr(user, 'pacijent'): return 'pacijent'
    if hasattr(user, 'doktor'): return 'doktor'
    return 'admin'


def token_response(user, created_status=status.HTTP_200_OK):
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user_type': get_user_type(user),
        'ime': user.first_name,
        'prezime': user.last_name,
        'username': user.username,
    }, status=created_status)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def registracija(request):
    serializer = RegistracijaSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    user = User.objects.create_user(
        username=data['username'], password=data['password'],
        first_name=data['first_name'], last_name=data['last_name'],
        email=data['email']
    )
    Pacijent.objects.create(
    user=user,
    telefon=data['telefon'],
    datum_rodjenja=data.get('datum_rodjenja'),
    adresa=data.get('adresa', ''),
    pol=data.get('pol', '')  # ← dodaj ovo
    )
    return token_response(user, status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    user = authenticate(
        username=request.data.get('username'),
        password=request.data.get('password')
    )
    if not user:
        return Response({'error': 'Pogrešno korisničko ime ili lozinka'}, status=status.HTTP_401_UNAUTHORIZED)
    return token_response(user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    return Response({'message': 'Uspešno ste se odjavili'})


@api_view(['GET'])
@permission_classes([AllowAny])
def lista_termina(request):
    termini = Termin.objects.filter(slobodan=True, datum_vreme__gte=timezone.now())
    return Response(TerminSerializer(termini, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def zakazi_pregled(request):
    if not hasattr(request.user, 'pacijent'):
        return Response({'error': 'Samo pacijenti mogu zakazivati preglede'}, status=status.HTTP_403_FORBIDDEN)

    serializer = ZakazivanjeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    try:
        termin = Termin.objects.get(id=data['termin_id'], slobodan=True)
    except Termin.DoesNotExist:
        return Response({'error': 'Termin nije dostupan'}, status=status.HTTP_400_BAD_REQUEST)

    pregled = Pregled.objects.create(
        pacijent=request.user.pacijent,
        doktor=Doktor.objects.first(),
        termin=termin,
        vrsta_pregleda=data['vrsta_pregleda'],
        napomena=data.get('napomena', '')
    )
    termin.slobodan = False
    termin.save()
    return Response(PregledSerializer(pregled).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def otkazi_pregled(request, pregled_id):
    try:
        pregled = Pregled.objects.get(id=pregled_id, pacijent=request.user.pacijent, status='zakazan')
    except Pregled.DoesNotExist:
        return Response({'error': 'Pregled nije pronađen'}, status=status.HTTP_404_NOT_FOUND)

    pregled.status = 'otkazan'
    pregled.save()
    pregled.termin.slobodan = True
    pregled.termin.save()
    return Response({'message': 'Pregled je otkazan'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def moji_pregledi(request):
    if not hasattr(request.user, 'pacijent'):
        return Response({'error': 'Pristup zabranjen'}, status=status.HTTP_403_FORBIDDEN)
    pregledi = Pregled.objects.filter(pacijent=request.user.pacijent)
    return Response(PregledSerializer(pregledi, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doktor_dashboard(request):
    if not hasattr(request.user, 'doktor'):
        return Response({'error': 'Pristup zabranjen'}, status=status.HTTP_403_FORBIDDEN)

    danas = date.today()
    svi = Pregled.objects.filter(
        doktor=request.user.doktor,
        termin__datum_vreme__date__gte=danas,
        status='zakazan'
    ).order_by('termin__datum_vreme')

    return Response({
        'datum': danas.strftime('%d.%m.%Y'),
        'ukupno_danas': svi.filter(termin__datum_vreme__date=danas).count(),
        'ukupno_predstojecci': svi.count(),
        'pregledi': PregledSerializer(svi, many=True).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def moj_profil(request):
    user = request.user
    user_type = get_user_type(user)
    extra = PacijentSerializer(user.pacijent).data if user_type == 'pacijent' else \
            DoktorSerializer(user.doktor).data if user_type == 'doktor' else {}

    return Response({
        'id': user.id, 'username': user.username,
        'ime': user.first_name, 'prezime': user.last_name,
        'email': user.email, 'user_type': user_type, 'profil': extra
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def zaboravljena_lozinka(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email je obavezan'}, status=status.HTTP_400_BAD_REQUEST)

    poruka = {'message': 'Ako email postoji u sistemu, poslaćemo vam link za reset lozinke.'}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(poruka)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_link = f"{settings.FRONTEND_URL}/reset-lozinka/{uid}/{token}"

    send_mail(
        subject='Reset lozinke — Radiološka ordinacija Dr. Martinović',
        message=f'Poštovani,\n\nKliknite na sledeći link da resetujete lozinku:\n{reset_link}\n\nLink je važeći 24 sata.\n\nAko niste tražili reset, ignorišite ovaj email.\n\nRadiološka ordinacija Dr. Martinović',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    return Response(poruka)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_lozinke(request):
    uid = request.data.get('uid')
    token = request.data.get('token')
    nova_lozinka = request.data.get('nova_lozinka')

    if not all([uid, token, nova_lozinka]):
        return Response({'error': 'Svi podaci su obavezni'}, status=status.HTTP_400_BAD_REQUEST)
    if len(nova_lozinka) < 6:
        return Response({'error': 'Lozinka mora imati minimum 6 karaktera'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
    except (TypeError, ValueError, User.DoesNotExist):
        return Response({'error': 'Nevažeći link'}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({'error': 'Link je istekao ili je nevažeći'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(nova_lozinka)
    user.save()
    try:
        user.auth_token.delete()
    except Exception:
        pass
    return Response({'message': 'Lozinka je uspešno promenjena!'})


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def promeni_lozinku(request):
    stara = request.data.get('stara_lozinka')
    nova = request.data.get('nova_lozinka')
    ponovi = request.data.get('ponovi_lozinku')

    if not all([stara, nova, ponovi]):
        return Response({'error': 'Sva polja su obavezna'}, status=status.HTTP_400_BAD_REQUEST)
    if not request.user.check_password(stara):
        return Response({'error': 'Stara lozinka nije ispravna'}, status=status.HTTP_400_BAD_REQUEST)
    if nova != ponovi:
        return Response({'error': 'Nove lozinke se ne poklapaju'}, status=status.HTTP_400_BAD_REQUEST)
    if len(nova) < 6:
        return Response({'error': 'Lozinka mora imati minimum 6 karaktera'}, status=status.HTTP_400_BAD_REQUEST)
    if stara == nova:
        return Response({'error': 'Nova lozinka mora biti drugačija od stare'}, status=status.HTTP_400_BAD_REQUEST)

    request.user.set_password(nova)
    request.user.save()
    request.user.auth_token.delete()
    token, _ = Token.objects.get_or_create(user=request.user)
    return Response({'message': 'Lozinka je uspešno promenjena!', 'token': token.key})