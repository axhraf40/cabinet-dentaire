from django.core.management.base import BaseCommand
from gestion_cabinet.models import InformationCabinet

class Command(BaseCommand):
    help = 'Initialise ou met à jour les informations du cabinet'

    def handle(self, *args, **kwargs):
        # L'URL de l'iframe Google Maps pour Avenue Fal Ould Oumeir, Agdal, Rabat
        maps_url = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3307.5721398756363!2d-6.862752684771897!3d34.00237728061825!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xda76c8b3a496bbb%3A0x866594654a2e0aa8!2sAv.%20Fal%20Ould%20Oumeir%2C%20Rabat%2C%20Morocco!5e0!3m2!1sen!2s!4v1709657543774!5m2!1sen!2s"

        cabinet_info, created = InformationCabinet.objects.get_or_create(
            defaults={
                'nom': 'Cabinet Dentaire Agdal',
                'adresse': '15 Avenue Fal Ould Oumeir, Agdal, Rabat, Maroc',
                'telephone': '+212 5377-45678',
                'email': 'contact@cabinet-dentaire-agdal.ma',
                'google_maps_url': maps_url,
                'description': 'Cabinet dentaire moderne situé au cœur d\'Agdal, Rabat. Notre équipe de professionnels est à votre service pour tous vos soins dentaires.',
                'horaires': '''Lundi - Vendredi : 9h00 - 19h00
Samedi : 9h00 - 13h00
Dimanche : Fermé'''
            }
        )

        if not created:
            # Mise à jour des informations existantes
            cabinet_info.nom = 'Cabinet Dentaire Agdal'
            cabinet_info.adresse = '15 Avenue Fal Ould Oumeir, Agdal, Rabat, Maroc'
            cabinet_info.telephone = '+212 5377-45678'
            cabinet_info.email = 'contact@cabinet-dentaire-agdal.ma'
            cabinet_info.google_maps_url = maps_url
            cabinet_info.description = 'Cabinet dentaire moderne situé au cœur d\'Agdal, Rabat. Notre équipe de professionnels est à votre service pour tous vos soins dentaires.'
            cabinet_info.horaires = '''Lundi - Vendredi : 9h00 - 19h00
Samedi : 9h00 - 13h00
Dimanche : Fermé'''
            cabinet_info.save()

        self.stdout.write(
            self.style.SUCCESS('Les informations du cabinet ont été {} avec succès'.format(
                'créées' if created else 'mises à jour'
            ))
        ) 