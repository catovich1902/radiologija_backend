from django.contrib import admin
from .models import Pacijent, Doktor, Termin, Pregled

@admin.register(Pacijent)
class PacijentAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'telefon', 'adresa', 'pol']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']

@admin.register(Doktor)
class DoktorAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'specijalnost', 'telefon']

@admin.register(Termin)
class TerminAdmin(admin.ModelAdmin):
    list_display = ['datum_vreme', 'trajanje_minuta', 'slobodan']
    list_filter = ['slobodan']
    list_editable = ['slobodan']

@admin.register(Pregled)
class PregledAdmin(admin.ModelAdmin):
    list_display = ['pacijent', 'doktor', 'vrsta_pregleda', 'status', 'kreiran']
    list_filter = ['vrsta_pregleda', 'status']
    search_fields = ['pacijent__user__first_name', 'pacijent__user__last_name']