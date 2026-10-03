from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
from datetime import datetime, time, timedelta
import random
import string

class User(AbstractUser):
    ROLES = [
        ('PATIENT', 'Patient'),
        ('DENTISTE', 'Dentiste'),
        ('SECRETAIRE', 'Secrétaire'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLES, default='PATIENT')
    telephone = models.CharField(max_length=15, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    adresse = models.TextField(blank=True)
    photo_profil = models.ImageField(upload_to='photos_profil/', null=True, blank=True)
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    def __str__(self):
        return self.get_full_name() or self.username
    
    @property
    def role_display(self):
        return dict(self.ROLES).get(self.role, '')
    
    @property
    def is_patient(self):
        return hasattr(self, 'patient_profile')
    
    @property
    def is_dentiste(self):
        return hasattr(self, 'dentiste_profile')
    
    @property
    def is_secretaire(self):
        return hasattr(self, 'secretaire_profile')
    
    def save(self, *args, **kwargs):
        if self.is_patient:
            self.role = 'PATIENT'
        elif self.is_dentiste:
            self.role = 'DENTISTE'
        elif self.is_secretaire:
            self.role = 'SECRETAIRE'
        super().save(*args, **kwargs)

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_naissance = models.DateField()
    telephone = models.CharField(max_length=15)
    adresse = models.TextField()
    date_inscription = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cabinet_patient'
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Dentiste(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dentiste_profile')
    specialite = models.CharField(max_length=100)
    telephone = models.CharField(max_length=15)
    
    class Meta:
        db_table = 'cabinet_dentiste'
    
    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

class Secretaire(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='secretaire_profile')
    telephone = models.CharField(max_length=15)
    
    class Meta:
        db_table = 'cabinet_secretaire'
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class RendezVous(models.Model):
    STATUT_CHOICES = [
        ('PROGRAMME', 'Programmé'),
        ('TERMINE', 'Terminé'),
        ('ANNULE', 'Annulé'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    dentiste = models.ForeignKey(Dentiste, on_delete=models.CASCADE)
    date_heure = models.DateTimeField()
    motif = models.CharField(max_length=200)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='PROGRAMME')
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cabinet_rendez_vous'
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
        ordering = ['-date_heure']
    
    def __str__(self):
        return f"RDV - {self.patient} avec Dr. {self.dentiste} le {self.date_heure}"

class Consultation(models.Model):
    rendez_vous = models.OneToOneField(RendezVous, on_delete=models.CASCADE)
    diagnostic = models.TextField()
    traitement = models.TextField()
    date_consultation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cabinet_consultation'
    
    def __str__(self):
        return f"Consultation - {self.rendez_vous.patient} le {self.date_consultation}"

class Facture(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('PAYE', 'Payé'),
        ('ECHEC', 'Échec'),
    ]
    
    MODE_PAIEMENT_CHOICES = [
        ('CARTE', 'Carte bancaire'),
        ('ESPECES', 'Espèces'),
        ('CHEQUE', 'Chèque'),
        ('VIREMENT', 'Virement'),
    ]
    
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_emission = models.DateTimeField(auto_now_add=True)
    date_paiement = models.DateTimeField(null=True, blank=True)
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    
    class Meta:
        db_table = 'cabinet_facture'
    
    def __str__(self):
        return f"Facture {self.id} - {self.consultation.rendez_vous.patient}"

class Produit(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField()
    quantite = models.IntegerField()
    seuil_alerte = models.IntegerField()
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'cabinet_produit'
    
    def __str__(self):
        return self.nom
    
    def stock_faible(self):
        return self.quantite <= self.seuil_alerte

class MouvementStock(models.Model):
    TYPE_MOUVEMENT = [
        ('ENTREE', 'Entrée'),
        ('SORTIE', 'Sortie'),
    ]
    
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    type_mouvement = models.CharField(max_length=10, choices=TYPE_MOUVEMENT)
    quantite = models.IntegerField()
    date_mouvement = models.DateTimeField(auto_now_add=True)
    effectue_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'cabinet_mouvement_stock'
    
    def __str__(self):
        return f"{self.type_mouvement} - {self.produit.nom} - {self.quantite}"

class MembreEquipe(models.Model):
    nom = models.CharField(max_length=100)
    titre = models.CharField(max_length=100)
    specialite = models.CharField(max_length=200)
    description = models.TextField()
    photo = models.ImageField(upload_to='staff_photos/')
    ordre_affichage = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'cabinet_membre_equipe'
        verbose_name = "Membre de l'équipe"
        verbose_name_plural = "Membres de l'équipe"
        ordering = ['ordre_affichage']
    
    def __str__(self):
        return self.nom

class InformationCabinet(models.Model):
    nom = models.CharField(max_length=200)
    adresse = models.TextField()
    telephone = models.CharField(max_length=15)
    email = models.EmailField()
    google_maps_url = models.URLField(help_text="URL de l'iframe Google Maps")
    description = models.TextField()
    horaires = models.TextField(help_text="Horaires d'ouverture du cabinet")
    
    class Meta:
        db_table = 'cabinet_information'
        verbose_name = 'Information du cabinet'
        verbose_name_plural = 'Informations du cabinet'
    
    def __str__(self):
        return self.nom

class SpecialiteCabinet(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='specialites_images/')
    ordre_affichage = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'cabinet_specialite'
        verbose_name = 'Spécialité'
        verbose_name_plural = 'Spécialités'
        ordering = ['ordre_affichage']
    
    def __str__(self):
        return self.nom
