from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import Patient, Dentiste, Secretaire, RendezVous, Consultation, Facture, Produit, MouvementStock, CustomUser, User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, time, timedelta

class UserRegistrationForm(UserCreationForm):
    phone_regex = RegexValidator(
        regex=r'^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$',
        message="Le numéro de téléphone doit être au format français (ex: 0612345678, 06.12.34.56.78, +33612345678)"
    )

    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Choisissez un nom d'utilisateur"
        })
    )

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre prénom'
        })
    )

    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom'
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@email.com'
        })
    )

    telephone = forms.CharField(
        validators=[phone_regex],
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+33612345678 ou 0612345678'
        })
    )

    date_naissance = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    adresse = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Votre adresse complète'
        })
    )

    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choisissez un mot de passe'
        })
    )

    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez votre mot de passe'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'telephone', 'date_naissance', 'adresse', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'PATIENT'  # Définir automatiquement le rôle comme PATIENT
        user.telephone = self.cleaned_data['telephone']
        user.date_naissance = self.cleaned_data['date_naissance']
        user.adresse = self.cleaned_data['adresse']
        
        if commit:
            user.save()
            # Créer le profil patient
            Patient.objects.create(
                user=user,
                telephone=user.telephone,
                date_naissance=user.date_naissance,
                adresse=user.adresse
            )
        return user

class RendezVousPatientForm(forms.ModelForm):
    date_heure = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        label="Date et heure"
    )

    class Meta:
        model = RendezVous
        fields = ['dentiste', 'date_heure', 'motif']
        widgets = {
            'dentiste': forms.Select(attrs={'class': 'form-control'}),
            'motif': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dentiste'].queryset = Dentiste.objects.all()
        self.fields['dentiste'].label = "Dentiste *"
        self.fields['motif'].label = "Motif de la consultation *"
        
        # Si l'utilisateur est un patient, remplir automatiquement le champ patient
        if user and hasattr(user, 'patient_profile'):
            self.instance.patient = user.patient_profile
        elif user and (hasattr(user, 'secretaire_profile') or hasattr(user, 'dentiste_profile')):
            # Pour les secrétaires et dentistes, vérifier s'il y a un patient dans les paramètres GET
            patient_id = kwargs.get('initial', {}).get('patient')
            if patient_id:
                try:
                    self.instance.patient = Patient.objects.get(id=patient_id)
                except Patient.DoesNotExist:
                    pass

    def clean_date_heure(self):
        date_heure = self.cleaned_data.get('date_heure')
        dentiste = self.cleaned_data.get('dentiste')
        
        if not date_heure:
            raise ValidationError("La date et l'heure sont requises.")

        # 1. Vérifier si la date n'est pas dans le passé
        now = timezone.now()
        if date_heure < now:
            raise ValidationError("Vous ne pouvez pas prendre un rendez-vous dans le passé.")

        # 2. Vérifier si c'est un jour de semaine (pas le week-end)
        if date_heure.weekday() >= 5:  # 5 = Samedi, 6 = Dimanche
            raise ValidationError("Les rendez-vous ne sont pas possibles le week-end.")

        # 3. Vérifier les heures d'ouverture (8h-18h)
        heure = date_heure.time()
        if heure < time(8, 0) or heure > time(18, 0):
            raise ValidationError("Les rendez-vous sont possibles uniquement entre 8h et 18h.")

        # 4. Vérifier les créneaux de 30 minutes
        if heure.minute not in [0, 30]:
            raise ValidationError("Les rendez-vous doivent commencer à l'heure ou à la demi-heure.")

        if dentiste:
            # 5. Vérifier les chevauchements avec d'autres rendez-vous
            debut_creneau = date_heure
            fin_creneau = debut_creneau + timedelta(minutes=30)
            
            rdv_existants = RendezVous.objects.filter(
                dentiste=dentiste,
                date_heure__lt=fin_creneau,
                date_heure__gt=debut_creneau - timedelta(minutes=30),
                statut__in=['PROGRAMME', 'EN_COURS']  # Ne pas compter les RDV annulés ou terminés
            ).exclude(id=self.instance.id if self.instance else None)

            if rdv_existants.exists():
                raise ValidationError("Ce créneau est déjà réservé pour ce dentiste.")

        return date_heure

class RendezVousSecretaireForm(forms.ModelForm):
    class Meta:
        model = RendezVous
        fields = ['montant']
        widgets = {
            'montant': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['diagnostic', 'traitement']
        widgets = {
            'diagnostic': forms.Textarea(attrs={'rows': 4}),
            'traitement': forms.Textarea(attrs={'rows': 4}),
        }

class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = ['montant', 'mode_paiement']
        widgets = {
            'montant': forms.NumberInput(attrs={'step': '0.01'}),
        }

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['nom', 'description', 'quantite', 'seuil_alerte', 'prix_unitaire']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'prix_unitaire': forms.NumberInput(attrs={'step': '0.01'}),
        }

class MouvementStockForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ['produit', 'type_mouvement', 'quantite']
        widgets = {
            'quantite': forms.NumberInput(attrs={'min': 1}),
        }

class DentisteForm(forms.ModelForm):
    class Meta:
        model = Dentiste
        fields = ['specialite', 'telephone']

class SecretaireForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@email.com'
        })
    )
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe'
        }),
        help_text='Laissez vide pour conserver le mot de passe actuel'
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez le nouveau mot de passe'
        })
    )

    class Meta:
        model = Secretaire
        fields = ['telephone']
        widgets = {
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+33612345678 ou 0612345678'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password or confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data

    def save(self, commit=True):
        secretaire = super().save(commit=False)
        if commit:
            # Mettre à jour l'email
            secretaire.user.email = self.cleaned_data['email']
            
            # Mettre à jour le mot de passe si fourni
            new_password = self.cleaned_data.get('new_password')
            if new_password:
                secretaire.user.set_password(new_password)
            
            secretaire.user.save()
            secretaire.save()
        return secretaire

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telephone', 'date_naissance', 'adresse', 'photo_profil']
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['telephone'].validators = [UserRegistrationForm.phone_regex]

# Nouveau formulaire pour la création de secrétaire (réservé aux dentistes)
class SecretaireRegistrationForm(UserCreationForm):
    phone_regex = RegexValidator(
        regex=r'^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$',
        message="Le numéro de téléphone doit être au format français"
    )

    username = forms.CharField(max_length=150, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    telephone = forms.CharField(validators=[phone_regex], max_length=15, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'telephone', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'SECRETAIRE'
        if commit:
            user.save()
            Secretaire.objects.create(
                user=user,
                telephone=self.cleaned_data['telephone']
            )
        return user

class AdminPasswordChangeForm(forms.Form):
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirmation du nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data["new_password1"])
        if commit:
            self.user.save()
        return self.user

class PatientUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@email.com'
        })
    )
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe'
        }),
        help_text='Laissez vide pour conserver le mot de passe actuel'
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez le nouveau mot de passe'
        })
    )

    class Meta:
        model = Patient
        fields = ['telephone', 'date_naissance', 'adresse']
        widgets = {
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+33612345678 ou 0612345678'
            }),
            'date_naissance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password or confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data

    def save(self, commit=True):
        patient = super().save(commit=False)
        if commit:
            # Mettre à jour l'email
            patient.user.email = self.cleaned_data['email']
            
            # Mettre à jour le mot de passe si fourni
            new_password = self.cleaned_data.get('new_password')
            if new_password:
                patient.user.set_password(new_password)
            
            patient.user.save()
            patient.save()
        return patient 