from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import (
    User, Patient, Dentiste, Secretaire, RendezVous, Consultation, Facture, Produit,
)

PASSWORD = 'Xyz!12345abc'


def prochain_jour_ouvre_10h():
    dt = timezone.localtime() + timedelta(days=1)
    while dt.weekday() >= 5:
        dt += timedelta(days=1)
    return dt.replace(hour=10, minute=0, second=0, microsecond=0)


class ParcoursPrincipalTests(TestCase):
    """Teste le parcours complet : patient -> dentiste -> secrétaire."""

    def setUp(self):
        dentiste_user = User.objects.create_user('dent1', password=PASSWORD, first_name='D', last_name='Dent')
        self.dentiste = Dentiste.objects.create(user=dentiste_user, specialite='Ortho', telephone='0611111111')
        secretaire_user = User.objects.create_user('sec1', password=PASSWORD, first_name='S', last_name='Sec')
        Secretaire.objects.create(user=secretaire_user, telephone='0622222222')
        Produit.objects.create(nom='Gants', description='Taille M', quantite=10, seuil_alerte=2, prix_unitaire='0.15')

    def login(self, username):
        self.client.logout()
        self.assertTrue(self.client.login(username=username, password=PASSWORD))

    def assertPages(self, urls, status=200):
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status)

    def test_pages_publiques(self):
        self.assertPages(['/', '/login/', '/register/'])

    def test_parcours_complet(self):
        # Inscription patient
        response = self.client.post('/register/', {
            'username': 'pat1', 'first_name': 'Ali', 'last_name': 'Test', 'email': 'p@example.com',
            'telephone': '0612345678', 'date_naissance': '1990-01-01', 'adresse': 'rue x',
            'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertRedirects(response, '/login/')
        patient = Patient.objects.get(user__username='pat1')

        # Patient : prise de rendez-vous
        self.login('pat1')
        self.assertPages(['/dashboard/', '/profile/', '/rendez-vous/', '/rendez-vous/nouveau/', '/change-password/'])
        self.client.post('/rendez-vous/nouveau/', {
            'dentiste': self.dentiste.id,
            'date_heure': prochain_jour_ouvre_10h().strftime('%Y-%m-%dT%H:%M'),
            'motif': 'Douleur',
        })
        rdv = RendezVous.objects.get(patient=patient)

        # Patient : pas d'accès aux pages du personnel
        for url in ['/patients/', '/stock/', '/secretaires/']:
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), '/dashboard/', fetch_redirect_response=False)

        # Dentiste : consultation -> facture automatique
        self.login('dent1')
        self.assertPages(['/dashboard/', '/patients/', f'/patient/{patient.id}/', '/rendez-vous/',
                          '/secretaires/', '/secretaire/nouveau/', f'/consultation/nouveau/{rdv.id}/'])
        self.client.post(f'/consultation/nouveau/{rdv.id}/', {'diagnostic': 'Carie', 'traitement': 'Plombage'})
        self.assertTrue(Consultation.objects.filter(rendez_vous=rdv).exists())
        facture = Facture.objects.get(consultation__rendez_vous=rdv)
        self.assertPages([f'/facture/{facture.id}/'])

        # Patient : voit sa facture
        self.login('pat1')
        self.assertPages([f'/facture/{facture.id}/', f'/paiement/{facture.id}/initier/'])

        # Secrétaire : patients, montant/paiement du RDV, stock
        self.login('sec1')
        self.assertPages(['/dashboard/', '/patients/', '/patient/nouveau/', f'/patient/{patient.id}/modifier/',
                          f'/patient/{patient.id}/mot-de-passe/', '/stock/', '/stock/produit/nouveau/',
                          '/stock/mouvement/nouveau/', '/rendez-vous/', f'/rendez-vous/{rdv.id}/montant/'])
        self.client.post(f'/rendez-vous/{rdv.id}/montant/', {'montant': '300'})
        self.client.post(f'/rendez-vous/{rdv.id}/payer/')
        rdv.refresh_from_db()
        self.assertEqual(rdv.montant, 300)
        self.assertEqual(rdv.statut_paiement, 'REGLE')

        produit = Produit.objects.get()
        self.client.post('/stock/mouvement/nouveau/', {'produit': produit.id, 'type_mouvement': 'ENTREE', 'quantite': 5})
        produit.refresh_from_db()
        self.assertEqual(produit.quantite, 15)
