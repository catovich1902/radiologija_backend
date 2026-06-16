from django.core.management.base import BaseCommand
from termini.models import Termin
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Generiše termine za narednih N dana'

    def add_arguments(self, parser):
        parser.add_argument('--dana', type=int, default=30)

    def handle(self, *args, **options):
        kreirano = 0
        preskoceno = 0
        danas = datetime.now().date()

        for i in range(options['dana']):
            datum = danas + timedelta(days=i)
            if datum.weekday() >= 5:
                continue

            for sat in range(8, 16):
                for minut in [0, 30]:
                    termin, kreiran = Termin.objects.get_or_create(
                        datum_vreme=datetime(datum.year, datum.month, datum.day, sat, minut),
                        defaults={'trajanje_minuta': 30, 'slobodan': True}
                    )
                    if kreiran:
                        kreirano += 1
                    else:
                        preskoceno += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ Kreirano {kreirano} novih, preskočeno {preskoceno} postojećih.'
        ))