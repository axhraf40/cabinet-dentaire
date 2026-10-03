from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from .models import *
from .forms import *
from .decorators import patient_required, dentiste_required, secretaire_required, role_required
import stripe
from django.conf import settings
from django.db import models
from datetime import datetime, time
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from datetime import datetime, timedelta

def home(request):
    specialites = SpecialiteCabinet.objects.all()
    membres_equipe = MembreEquipe.objects.all()
    info_cabinet = InformationCabinet.objects.first()
    return render(request, 'gestion_cabinet/home.html', {
        'specialites': specialites,
        'membres_equipe': membres_equipe,
        'info_cabinet': info_cabinet
    })

def contact(request):
    info_cabinet = InformationCabinet.objects.first()
    return render(request, 'gestion_cabinet/contact.html', {
        'info_cabinet': info_cabinet
    })

def services(request):
    specialites = SpecialiteCabinet.objects.all()
    return render(request, 'gestion_cabinet/services.html', {
        'specialites': specialites
    })

def equipe(request):
    membres_equipe = MembreEquipe.objects.all()
    return render(request, 'gestion_cabinet/equipe.html', {
        'membres_equipe': membres_equipe
    })

@login_required
def dashboard(request):
    context = {}
    
    if request.user.is_patient:
        rendez_vous = RendezVous.objects.filter(patient=request.user.patient_profile).order_by('-date_heure')
        factures = Facture.objects.filter(consultation__rendez_vous__patient=request.user.patient_profile)
        context.update({
            'rendez_vous': rendez_vous,
            'factures': factures
        })
    elif request.user.is_dentiste:
        rendez_vous = RendezVous.objects.filter(dentiste=request.user.dentiste_profile).order_by('-date_heure')
        consultations = Consultation.objects.filter(rendez_vous__dentiste=request.user.dentiste_profile)
        context.update({
            'rendez_vous': rendez_vous,
            'consultations': consultations
        })
    elif request.user.is_secretaire:
        rendez_vous = RendezVous.objects.all().order_by('-date_heure')
        factures_en_attente = Facture.objects.filter(statut='EN_ATTENTE')
        produits_stock_faible = Produit.objects.filter(quantite__lte=models.F('seuil_alerte'))
        context.update({
            'rendez_vous': rendez_vous,
            'factures_en_attente': factures_en_attente,
            'produits_stock_faible': produits_stock_faible
        })
    
    return render(request, 'gestion_cabinet/dashboard.html', context)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre compte a été créé avec succès ! Vous pouvez maintenant vous connecter.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'gestion_cabinet/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès !')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'gestion_cabinet/profile.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Votre mot de passe a été modifié avec succès !')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'gestion_cabinet/change_password.html', {'form': form})

@login_required
@role_required(['DENTISTE', 'SECRETAIRE'])
def patient_list(request):
    patients = Patient.objects.all()
    return render(request, 'gestion_cabinet/patient_list.html', {'patients': patients})

@login_required
@role_required(['DENTISTE', 'SECRETAIRE'])
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    rendez_vous = RendezVous.objects.filter(patient=patient).order_by('-date_heure')
    consultations = Consultation.objects.filter(rendez_vous__patient=patient).order_by('-date_consultation')
    factures = Facture.objects.filter(consultation__rendez_vous__patient=patient).order_by('-date_emission')
    
    # Debug logs
    print(f"Patient ID: {patient_id}")
    print(f"Nombre de rendez-vous: {rendez_vous.count()}")
    print(f"Nombre de consultations: {consultations.count()}")
    print(f"Nombre de factures: {factures.count()}")
    print(f"Role de l'utilisateur: {request.user.role}")
    
    # Calculer le total des factures
    total_factures = sum(facture.montant for facture in factures)
    
    context = {
        'patient': patient,
        'rendez_vous': rendez_vous,
        'consultations': consultations,
        'factures': factures,
        'total_factures': total_factures,
        'user_role': request.user.role  # Ajouter le rôle de l'utilisateur au contexte
    }
    return render(request, 'gestion_cabinet/patient_detail.html', context)

@login_required
@secretaire_required
def patient_update(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=patient.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Le profil du patient a été mis à jour avec succès !')
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = UserProfileForm(instance=patient.user)
    return render(request, 'gestion_cabinet/patient_form.html', {'form': form, 'patient': patient})

@login_required
@secretaire_required
def patient_delete(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    if request.method == 'POST':
        patient.user.delete()  # Supprime également le patient grâce à la relation OneToOne
        messages.success(request, 'Le patient a été supprimé avec succès !')
        return redirect('patient_list')
    return render(request, 'gestion_cabinet/patient_confirm_delete.html', {'patient': patient})

@login_required
@secretaire_required
def dentiste_list(request):
    dentistes = Dentiste.objects.all()
    return render(request, 'gestion_cabinet/dentiste_list.html', {'dentistes': dentistes})

@login_required
@secretaire_required
def dentiste_detail(request, dentiste_id):
    dentiste = get_object_or_404(Dentiste, id=dentiste_id)
    rendez_vous = RendezVous.objects.filter(dentiste=dentiste).order_by('-date_heure')
    consultations = Consultation.objects.filter(rendez_vous__dentiste=dentiste).order_by('-date_consultation')
    return render(request, 'gestion_cabinet/dentiste_detail.html', {
        'dentiste': dentiste,
        'rendez_vous': rendez_vous,
        'consultations': consultations
    })

@login_required
@secretaire_required
def dentiste_create(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'DENTISTE'
            user.save()
            Dentiste.objects.create(
                user=user,
                telephone=form.cleaned_data['telephone'],
                specialite=form.cleaned_data['specialite']
            )
            messages.success(request, 'Le dentiste a été créé avec succès !')
            return redirect('dentiste_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'gestion_cabinet/dentiste_form.html', {'form': form})

@login_required
@secretaire_required
def dentiste_update(request, dentiste_id):
    dentiste = get_object_or_404(Dentiste, id=dentiste_id)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=dentiste.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Le profil du dentiste a été mis à jour avec succès !')
            return redirect('dentiste_detail', dentiste_id=dentiste.id)
    else:
        form = UserProfileForm(instance=dentiste.user)
    return render(request, 'gestion_cabinet/dentiste_form.html', {'form': form, 'dentiste': dentiste})

@login_required
@secretaire_required
def dentiste_delete(request, dentiste_id):
    dentiste = get_object_or_404(Dentiste, id=dentiste_id)
    if request.method == 'POST':
        dentiste.user.delete()  # Supprime également le dentiste grâce à la relation OneToOne
        messages.success(request, 'Le dentiste a été supprimé avec succès !')
        return redirect('dentiste_list')
    return render(request, 'gestion_cabinet/dentiste_confirm_delete.html', {'dentiste': dentiste})

@login_required
@secretaire_required
def secretaire_list(request):
    secretaires = Secretaire.objects.all()
    return render(request, 'gestion_cabinet/secretaire_list.html', {'secretaires': secretaires})

@login_required
@secretaire_required
def secretaire_create(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'SECRETAIRE'
            user.save()
            Secretaire.objects.create(
                user=user,
                telephone=form.cleaned_data['telephone']
            )
            messages.success(request, 'La secrétaire a été créée avec succès !')
            return redirect('secretaire_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'gestion_cabinet/secretaire_form.html', {'form': form})

@login_required
@secretaire_required
def secretaire_update(request, secretaire_id):
    secretaire = get_object_or_404(Secretaire, id=secretaire_id)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=secretaire.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Le profil de la secrétaire a été mis à jour avec succès !')
            return redirect('secretaire_list')
    else:
        form = UserProfileForm(instance=secretaire.user)
    return render(request, 'gestion_cabinet/secretaire_form.html', {'form': form, 'secretaire': secretaire})

@login_required
@secretaire_required
def secretaire_delete(request, secretaire_id):
    secretaire = get_object_or_404(Secretaire, id=secretaire_id)
    if request.method == 'POST':
        secretaire.user.delete()  # Supprime également la secrétaire grâce à la relation OneToOne
        messages.success(request, 'La secrétaire a été supprimée avec succès !')
        return redirect('secretaire_list')
    return render(request, 'gestion_cabinet/secretaire_confirm_delete.html', {
        'secretaire': secretaire,
        'message': "Êtes-vous sûr de vouloir supprimer ce compte secrétaire ? Cette action est irréversible."
    })

@login_required
def rendez_vous_list(request):
    if request.user.is_patient:
        rendez_vous = RendezVous.objects.filter(patient=request.user.patient_profile)
    elif request.user.is_dentiste:
        rendez_vous = RendezVous.objects.filter(dentiste=request.user.dentiste_profile)
    else:  # Secrétaire
        rendez_vous = RendezVous.objects.all()
    
    rendez_vous = rendez_vous.order_by('-date_heure')
    return render(request, 'gestion_cabinet/rendez_vous_list.html', {'rendez_vous': rendez_vous})

@login_required
def rendez_vous_create(request):
    if request.method == 'POST':
        form = RendezVousPatientForm(request.POST, user=request.user)
        if form.is_valid():
            rendez_vous = form.save()
            messages.success(request, 'Le rendez-vous a été créé avec succès !')
            return redirect('rendez_vous_list')
    else:
        form = RendezVousPatientForm(user=request.user)
    return render(request, 'gestion_cabinet/rendez_vous_form.html', {'form': form})

@login_required
def rendez_vous_detail(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    if request.user.is_patient and request.user.patient_profile != rendez_vous.patient:
        messages.error(request, "Vous n'avez pas accès à ce rendez-vous.")
        return redirect('rendez_vous_list')
    return render(request, 'gestion_cabinet/rendez_vous_detail.html', {'rendez_vous': rendez_vous})

@login_required
@role_required(['DENTISTE', 'SECRETAIRE'])
def rendez_vous_update(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    if request.method == 'POST':
        form = RendezVousPatientForm(request.POST, instance=rendez_vous, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Le rendez-vous a été mis à jour avec succès !')
            return redirect('rendez_vous_detail', pk=rendez_vous.pk)
    else:
        form = RendezVousPatientForm(instance=rendez_vous, user=request.user)
    return render(request, 'gestion_cabinet/rendez_vous_form.html', {'form': form, 'rendez_vous': rendez_vous})

@login_required
@role_required(['DENTISTE', 'SECRETAIRE'])
def rendez_vous_cancel(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    if request.method == 'POST':
        rendez_vous.statut = 'ANNULE'
        rendez_vous.save()
        messages.success(request, 'Le rendez-vous a été annulé avec succès !')
        return redirect('rendez_vous_list')
    return render(request, 'gestion_cabinet/rendez_vous_confirm_cancel.html', {'rendez_vous': rendez_vous})

@login_required
@dentiste_required
def consultation_create(request, rendez_vous_id):
    rendez_vous = get_object_or_404(RendezVous, id=rendez_vous_id, dentiste=request.user.dentiste_profile)
    
    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.rendez_vous = rendez_vous
            consultation.save()
            rendez_vous.statut = 'TERMINE'
            rendez_vous.save()
            
            # Créer automatiquement une facture
            facture = Facture.objects.create(
                consultation=consultation,
                montant=0,  # Le montant sera défini plus tard par la secrétaire
                statut='EN_ATTENTE'
            )
            
            messages.success(request, 'Consultation enregistrée avec succès !')
            return redirect('consultation_detail', pk=consultation.pk)
    else:
        form = ConsultationForm()
    
    historique_consultations = Consultation.objects.filter(
        rendez_vous__patient=rendez_vous.patient
    ).exclude(
        rendez_vous=rendez_vous
    ).order_by('-date_consultation')
    
    return render(request, 'gestion_cabinet/consultation_form.html', {
        'form': form,
        'rendez_vous': rendez_vous,
        'historique_consultations': historique_consultations
    })

@login_required
@role_required(['DENTISTE', 'SECRETAIRE'])
def consultation_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    return render(request, 'gestion_cabinet/consultation_detail.html', {'consultation': consultation})

@login_required
@dentiste_required
def consultation_update(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    if request.method == 'POST':
        form = ConsultationForm(request.POST, instance=consultation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Consultation mise à jour avec succès !')
            return redirect('consultation_detail', pk=consultation.pk)
    else:
        form = ConsultationForm(instance=consultation)
    return render(request, 'gestion_cabinet/consultation_form.html', {
        'form': form,
        'rendez_vous': consultation.rendez_vous
    })

@login_required
@secretaire_required
def facture_create(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    if request.method == 'POST':
        form = FactureForm(request.POST)
        if form.is_valid():
            facture = form.save(commit=False)
            facture.consultation = consultation
            facture.save()
            messages.success(request, 'Facture créée avec succès !')
            return redirect('facture_detail', pk=facture.pk)
    else:
        form = FactureForm()
    
    return render(request, 'gestion_cabinet/facture_form.html', {
        'form': form,
        'consultation': consultation
    })

@login_required
def facture_detail(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    if hasattr(request.user, 'patient_profile'):
        if request.user.patient_profile != facture.consultation.rendez_vous.patient:
            messages.error(request, "Vous n'avez pas accès à cette facture.")
            return redirect('dashboard')
    elif not (hasattr(request.user, 'secretaire_profile') or hasattr(request.user, 'dentiste_profile')):
        messages.error(request, "Vous n'avez pas accès à cette facture.")
        return redirect('dashboard')
    
    return render(request, 'gestion_cabinet/facture_detail.html', {'facture': facture})

@login_required
@secretaire_required
def facture_update(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    
    if request.method == 'POST':
        form = FactureForm(request.POST, instance=facture)
        if form.is_valid():
            form.save()
            messages.success(request, 'Facture mise à jour avec succès !')
            return redirect('facture_detail', pk=facture.pk)
    else:
        form = FactureForm(instance=facture)
    
    return render(request, 'gestion_cabinet/facture_form.html', {
        'form': form,
        'consultation': facture.consultation,
        'is_update': True
    })

@login_required
@secretaire_required
def facture_payer(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    
    if facture.statut != 'PAYE':
        facture.statut = 'PAYE'
        facture.date_paiement = timezone.now()
        facture.save()
        messages.success(request, 'La facture a été marquée comme payée.')
    
    return redirect('patient_detail', patient_id=facture.consultation.rendez_vous.patient.id)

@login_required
def initier_paiement(request, facture_id):
    facture = get_object_or_404(Facture, id=facture_id)
    
    # Vérifier que l'utilisateur est soit le patient concerné, soit une secrétaire
    if not (hasattr(request.user, 'secretaire') or 
            (hasattr(request.user, 'patient') and request.user.patient == facture.consultation.rendez_vous.patient)):
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette facture.")
        return redirect('dashboard')
    
    return render(request, 'gestion_cabinet/initier_paiement.html', {
        'facture': facture
    })

@login_required
def process_paiement_cb(request, facture_id):
    facture = get_object_or_404(Facture, id=facture_id)
    
    if not (hasattr(request.user, 'secretaire') or 
            (hasattr(request.user, 'patient') and request.user.patient == facture.consultation.rendez_vous.patient)):
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette facture.")
        return redirect('dashboard')

    stripe.api_key = settings.STRIPE_SECRET_KEY

    if request.method == 'POST':
        try:
            # Créer l'intention de paiement
            intent = stripe.PaymentIntent.create(
                amount=int(facture.montant * 100),  # Stripe utilise les centimes
                currency='eur',
                metadata={'facture_id': facture.id}
            )
            
            return render(request, 'gestion_cabinet/process_paiement_cb.html', {
                'facture': facture,
                'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                'client_secret': intent.client_secret
            })
            
        except Exception as e:
            messages.error(request, "Une erreur est survenue lors de l'initialisation du paiement.")
            return redirect('facture_detail', facture_id=facture.id)
    
    return redirect('initier_paiement', facture_id=facture.id)

@login_required
def process_paiement_especes(request, facture_id):
    facture = get_object_or_404(Facture, id=facture_id)
    
    if not (hasattr(request.user, 'secretaire') or 
            (hasattr(request.user, 'patient') and request.user.patient == facture.consultation.rendez_vous.patient)):
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette facture.")
        return redirect('dashboard')

    if request.method == 'POST':
        facture.mode_paiement = 'ESPECES'
        facture.statut = 'EN_ATTENTE'
        facture.save()
        messages.info(request, f"Veuillez préparer {facture.montant}€ en espèces pour votre prochain rendez-vous.")
        return redirect('facture_detail', facture_id=facture.id)
    
    return redirect('initier_paiement', facture_id=facture.id)

@login_required
def paiement_success(request, facture_id):
    facture = get_object_or_404(Facture, id=facture_id)
    
    if not (hasattr(request.user, 'secretaire') or 
            (hasattr(request.user, 'patient') and request.user.patient == facture.consultation.rendez_vous.patient)):
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette facture.")
        return redirect('dashboard')

    facture.statut = 'PAYE'
    facture.date_paiement = timezone.now()
    facture.save()
    
    messages.success(request, "Paiement effectué avec succès !")
    return redirect('facture_detail', facture_id=facture.id)

@login_required
@secretaire_required
def stock_list(request):
    produits = Produit.objects.all()
    return render(request, 'gestion_cabinet/stock_list.html', {'produits': produits})

@login_required
@secretaire_required
def stock_create(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produit ajouté avec succès !')
            return redirect('stock_list')
    else:
        form = ProduitForm()
    return render(request, 'gestion_cabinet/stock_form.html', {'form': form})

@login_required
@secretaire_required
def stock_update(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        form = ProduitForm(request.POST, instance=produit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produit mis à jour avec succès !')
            return redirect('stock_list')
    else:
        form = ProduitForm(instance=produit)
    return render(request, 'gestion_cabinet/stock_form.html', {'form': form, 'produit': produit})

@login_required
@secretaire_required
def stock_delete(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        produit.delete()
        messages.success(request, 'Produit supprimé avec succès !')
        return redirect('stock_list')
    return render(request, 'gestion_cabinet/stock_confirm_delete.html', {'produit': produit})

@login_required
@secretaire_required
def mouvement_stock_create(request):
    if request.method == 'POST':
        form = MouvementStockForm(request.POST)
        if form.is_valid():
            mouvement = form.save(commit=False)
            mouvement.effectue_par = request.user
            
            produit = mouvement.produit
            if mouvement.type_mouvement == 'ENTREE':
                produit.quantite += mouvement.quantite
            else:  # SORTIE
                if produit.quantite < mouvement.quantite:
                    messages.error(request, 'Stock insuffisant pour effectuer cette sortie.')
                    return redirect('stock_list')
                produit.quantite -= mouvement.quantite
            
            produit.save()
            mouvement.save()
            
            messages.success(request, 'Mouvement de stock enregistré avec succès !')
            return redirect('stock_list')
    else:
        form = MouvementStockForm()
    return render(request, 'gestion_cabinet/mouvement_stock_form.html', {'form': form})
