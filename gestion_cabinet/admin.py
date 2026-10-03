from django.contrib import admin
from .models import (
    User, Patient, Dentiste, Secretaire, RendezVous, 
    Consultation, Facture, Produit, MouvementStock,
    MembreEquipe, InformationCabinet, SpecialiteCabinet
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role')
    list_filter = ('role',)
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'telephone', 'date_naissance')
    search_fields = ('user__username', 'user__email', 'telephone')

@admin.register(Dentiste)
class DentisteAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialite', 'telephone')
    search_fields = ('user__username', 'user__email', 'specialite')

@admin.register(Secretaire)
class SecretaireAdmin(admin.ModelAdmin):
    list_display = ('user', 'telephone')
    search_fields = ('user__username', 'user__email', 'telephone')

@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ('patient', 'dentiste', 'date_heure', 'motif', 'statut')
    list_filter = ('statut', 'date_heure')
    search_fields = ('patient__user__username', 'dentiste__user__username', 'motif')

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('rendez_vous', 'date_consultation')
    search_fields = ('rendez_vous__patient__user__username', 'diagnostic', 'traitement')

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'montant', 'date_emission', 'statut')
    list_filter = ('statut', 'mode_paiement')
    search_fields = ('consultation__rendez_vous__patient__user__username',)

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'quantite', 'seuil_alerte', 'prix_unitaire')
    search_fields = ('nom', 'description')

@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('produit', 'type_mouvement', 'quantite', 'date_mouvement', 'effectue_par')
    list_filter = ('type_mouvement', 'date_mouvement')
    search_fields = ('produit__nom', 'effectue_par__username')

@admin.register(MembreEquipe)
class MembreEquipeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'titre', 'specialite', 'ordre_affichage')
    list_editable = ('ordre_affichage',)
    search_fields = ('nom', 'titre', 'specialite')
    ordering = ('ordre_affichage',)

@admin.register(InformationCabinet)
class InformationCabinetAdmin(admin.ModelAdmin):
    list_display = ('nom', 'telephone', 'email')
    search_fields = ('nom', 'adresse', 'email')

    def has_add_permission(self, request):
        # Vérifier s'il existe déjà une instance
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

@admin.register(SpecialiteCabinet)
class SpecialiteCabinetAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ordre_affichage')
    list_editable = ('ordre_affichage',)
    search_fields = ('nom', 'description')
    ordering = ('ordre_affichage',)
