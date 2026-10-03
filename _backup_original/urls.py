from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Pages principales
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('equipe/', views.equipe, name='equipe'),
    
    # Authentification
    path('login/', auth_views.LoginView.as_view(template_name='gestion_cabinet/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Gestion des patients
    path('patients/', views.patient_list, name='patient_list'),
    path('patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patient/<int:patient_id>/modifier/', views.patient_update, name='patient_update'),
    path('patient/<int:patient_id>/supprimer/', views.patient_delete, name='patient_delete'),
    
    # Gestion des dentistes
    path('dentistes/', views.dentiste_list, name='dentiste_list'),
    path('dentiste/<int:dentiste_id>/', views.dentiste_detail, name='dentiste_detail'),
    path('dentiste/nouveau/', views.dentiste_create, name='dentiste_create'),
    path('dentiste/<int:dentiste_id>/modifier/', views.dentiste_update, name='dentiste_update'),
    path('dentiste/<int:dentiste_id>/supprimer/', views.dentiste_delete, name='dentiste_delete'),
    
    # Gestion des secrétaires
    path('secretaires/', views.secretaire_list, name='secretaire_list'),
    path('secretaire/nouveau/', views.secretaire_create, name='secretaire_create'),
    path('secretaire/<int:secretaire_id>/modifier/', views.secretaire_update, name='secretaire_update'),
    path('secretaire/<int:secretaire_id>/supprimer/', views.secretaire_delete, name='secretaire_delete'),
    
    # Gestion des rendez-vous
    path('rendez-vous/', views.rendez_vous_list, name='rendez_vous_list'),
    path('rendez-vous/nouveau/', views.rendez_vous_create, name='rendez_vous_create'),
    path('rendez-vous/<int:pk>/', views.rendez_vous_detail, name='rendez_vous_detail'),
    path('rendez-vous/<int:pk>/modifier/', views.rendez_vous_update, name='rendez_vous_update'),
    path('rendez-vous/<int:pk>/annuler/', views.rendez_vous_cancel, name='rendez_vous_cancel'),
    path('rendez-vous/<int:rdv_id>/payer/', views.marquer_rdv_paye, name='marquer_rdv_paye'),
    path('rendez-vous/<int:rdv_id>/montant/', views.definir_montant_rdv, name='definir_montant_rdv'),
    
    # Consultations
    path('consultation/nouveau/<int:rendez_vous_id>/', views.consultation_create, name='consultation_create'),
    path('consultation/<int:pk>/', views.consultation_detail, name='consultation_detail'),
    path('consultation/<int:pk>/modifier/', views.consultation_update, name='consultation_update'),
    
    # Factures
    path('facture/nouveau/<int:consultation_id>/', views.facture_create, name='facture_create'),
    path('facture/<int:pk>/', views.facture_detail, name='facture_detail'),
    path('facture/<int:pk>/modifier/', views.facture_update, name='facture_update'),
    path('facture/<int:pk>/payer/', views.facture_payer, name='facture_payer'),
    
    # Stock
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/produit/nouveau/', views.stock_create, name='stock_create'),
    path('stock/produit/<int:pk>/modifier/', views.stock_update, name='stock_update'),
    path('stock/produit/<int:pk>/supprimer/', views.stock_delete, name='stock_delete'),
    
    # Mouvements de stock
    path('stock/mouvement/nouveau/', views.mouvement_stock_create, name='mouvement_stock_create'),
    
    # Paiements
    path('paiement/<int:facture_id>/initier/', views.initier_paiement, name='initier_paiement'),
    path('paiement/<int:facture_id>/cb/', views.process_paiement_cb, name='process_paiement_cb'),
    path('paiement/<int:facture_id>/especes/', views.process_paiement_especes, name='process_paiement_especes'),
    path('paiement/<int:facture_id>/success/', views.paiement_success, name='paiement_success'),
] 