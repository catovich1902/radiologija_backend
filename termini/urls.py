from django.urls import path
from . import views

urlpatterns = [
    path('registracija/', views.registracija, name='registracija'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profil/', views.moj_profil, name='profil'),
    path('termini/', views.lista_termina, name='lista_termina'),
    path('zakazi/', views.zakazi_pregled, name='zakazi_pregled'),
    path('moji-pregledi/', views.moji_pregledi, name='moji_pregledi'),
    path('otkazi/<int:pregled_id>/', views.otkazi_pregled, name='otkazi_pregled'),
    path('doktor/dashboard/', views.doktor_dashboard, name='doktor_dashboard'),
    path('zaboravljena-lozinka/', views.zaboravljena_lozinka, name='zaboravljena_lozinka'),
    path('reset-lozinke/', views.reset_lozinke, name='reset_lozinke'),
    path('promeni-lozinku/', views.promeni_lozinku, name='promeni_lozinku'),
]