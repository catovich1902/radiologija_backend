from django.db import models
from django.contrib.auth.models import User


class Pacijent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pacijent')
    telefon = models.CharField(max_length=20)
    datum_rodjenja = models.DateField(null=True, blank=True)
    adresa = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    class Meta:
        verbose_name = "Pacijent"
        verbose_name_plural = "Pacijenti"
    POL_CHOICES = [('Muški', 'Muški'), ('Ženski', 'Ženski')]
    pol = models.CharField(max_length=10, choices=POL_CHOICES, blank=True)


class Doktor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specijalnost = models.CharField(max_length=100, default='Radiolog')
    telefon = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Dr {self.user.first_name} {self.user.last_name}"

    class Meta:
        verbose_name = "Doktor"
        verbose_name_plural = "Doktori"


class Termin(models.Model):
    datum_vreme = models.DateTimeField()
    trajanje_minuta = models.IntegerField(default=30)
    slobodan = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.datum_vreme.strftime('%d.%m.%Y %H:%M')} — {'Slobodan' if self.slobodan else 'Zauzet'}"

    class Meta:
        verbose_name = "Termin"
        verbose_name_plural = "Termini"
        ordering = ['datum_vreme']


class Pregled(models.Model):
    VRSTE_PREGLEDA = [('RTG', 'Rendgen'), ('UZV', 'Ultrazvuk'), ('CT', 'CT Sken'), ('MRI', 'Magnetna rezonanca')]
    STATUS_CHOICES = [('zakazan', 'Zakazan'), ('zavrsen', 'Završen'), ('otkazan', 'Otkazan')]
    CENE = {'RTG': 2500, 'UZV': 3500, 'CT': 8000, 'MRI': 12000}

    pacijent = models.ForeignKey(Pacijent, on_delete=models.CASCADE, related_name='pregledi')
    doktor = models.ForeignKey(Doktor, on_delete=models.SET_NULL, null=True, related_name='pregledi')
    termin = models.OneToOneField(Termin, on_delete=models.CASCADE)
    vrsta_pregleda = models.CharField(max_length=10, choices=VRSTE_PREGLEDA)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='zakazan')
    napomena = models.TextField(blank=True)
    kreiran = models.DateTimeField(auto_now_add=True)

    @property
    def cena(self):
        return self.CENE.get(self.vrsta_pregleda, 0)

    def __str__(self):
        return f"{self.pacijent} — {self.vrsta_pregleda} — {self.termin.datum_vreme.strftime('%d.%m.%Y %H:%M')}"

    class Meta:
        verbose_name = "Pregled"
        verbose_name_plural = "Pregledi"
        ordering = ['-termin__datum_vreme']