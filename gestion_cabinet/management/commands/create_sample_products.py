from django.core.management.base import BaseCommand
from gestion_cabinet.models import Produit

class Command(BaseCommand):
    help = 'Crée des produits exemple pour le stock'

    def handle(self, *args, **kwargs):
        products = [
            {
                'nom': 'Gants médicaux (boîte)',
                'description': 'Boîte de 100 gants en latex, taille M',
                'quantite': 50,
                'seuil_alerte': 10,
                'prix_unitaire': 8.99
            },
            {
                'nom': 'Masques chirurgicaux',
                'description': 'Boîte de 50 masques chirurgicaux à usage unique',
                'quantite': 100,
                'seuil_alerte': 20,
                'prix_unitaire': 12.50
            },
            {
                'nom': 'Anesthésiant local',
                'description': 'Carpules d\'anesthésiant local 1.8ml',
                'quantite': 200,
                'seuil_alerte': 50,
                'prix_unitaire': 0.95
            },
            {
                'nom': 'Composite dentaire',
                'description': 'Composite photopolymérisable A2, seringue 4g',
                'quantite': 30,
                'seuil_alerte': 5,
                'prix_unitaire': 25.00
            },
            {
                'nom': 'Aiguilles dentaires',
                'description': 'Boîte de 100 aiguilles stériles 27G',
                'quantite': 40,
                'seuil_alerte': 8,
                'prix_unitaire': 15.99
            },
            {
                'nom': 'Rouleaux de coton',
                'description': 'Paquet de 1000 rouleaux de coton dentaire',
                'quantite': 25,
                'seuil_alerte': 5,
                'prix_unitaire': 9.99
            },
            {
                'nom': 'Désinfectant surfaces',
                'description': 'Spray désinfectant pour surfaces, 1L',
                'quantite': 15,
                'seuil_alerte': 3,
                'prix_unitaire': 11.50
            },
            {
                'nom': 'Bavoirs jetables',
                'description': 'Boîte de 500 bavoirs jetables',
                'quantite': 20,
                'seuil_alerte': 4,
                'prix_unitaire': 35.00
            }
        ]

        for product in products:
            Produit.objects.get_or_create(
                nom=product['nom'],
                defaults={
                    'description': product['description'],
                    'quantite': product['quantite'],
                    'seuil_alerte': product['seuil_alerte'],
                    'prix_unitaire': product['prix_unitaire']
                }
            )

        self.stdout.write(self.style.SUCCESS('Produits exemple créés avec succès!')) 