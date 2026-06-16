from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Pacijent, Doktor, Termin, Pregled


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class PacijentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Pacijent
        fields = ['id', 'user', 'telefon', 'datum_rodjenja', 'adresa', 'pol']


class DoktorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Doktor
        fields = ['id', 'user', 'specijalnost', 'telefon', 'bio']


class TerminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Termin
        fields = ['id', 'datum_vreme', 'trajanje_minuta', 'slobodan']


class PregledSerializer(serializers.ModelSerializer):
    pacijent = PacijentSerializer(read_only=True)
    termin = TerminSerializer(read_only=True)
    vrsta_pregleda_display = serializers.CharField(source='get_vrsta_pregleda_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cena = serializers.IntegerField(read_only=True)

    class Meta:
        model = Pregled
        fields = ['id', 'pacijent', 'termin', 'vrsta_pregleda', 'vrsta_pregleda_display', 'status', 'status_display', 'napomena', 'cena', 'kreiran']


class ZakazivanjeSerializer(serializers.Serializer):
    termin_id = serializers.IntegerField()
    vrsta_pregleda = serializers.ChoiceField(choices=['RTG', 'UZV', 'CT', 'MRI'])
    napomena = serializers.CharField(required=False, allow_blank=True)


class RegistracijaSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(min_length=6)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    telefon = serializers.CharField()
    datum_rodjenja = serializers.DateField(required=False)
    adresa = serializers.CharField(required=False, allow_blank=True)
    pol = serializers.ChoiceField(choices=['Muški', 'Ženski'], required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Korisničko ime već postoji!")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email već postoji!")
        return value