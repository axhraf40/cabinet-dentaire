# Cabinet Dentaire

Application web de gestion d'un cabinet dentaire, développée avec Django 5.2.

## Fonctionnalités

- **Patients** : inscription, prise de rendez-vous, profil, consultation des factures.
- **Dentistes** : tableau de bord, dossiers patients, consultations (facture créée automatiquement), gestion des secrétaires.
- **Secrétaires** : gestion des patients, montant et paiement des rendez-vous, factures, stock et mouvements de stock.
- Paiement par carte via Stripe (optionnel).

## Structure

```
cabinet_dentaire/   configuration du projet Django (settings, urls)
gestion_cabinet/    application principale (modèles, vues, formulaires, tests)
templates/          pages HTML
static/             CSS, JS, images
lancer.bat          lancement en un clic sous Windows
```

## Installation

### Windows (rapide)

Double-cliquer sur `lancer.bat`. Il crée l'environnement virtuel, installe les dépendances, prépare la base de données et ouvre http://127.0.0.1:8000.

### Manuel

```bash
python -m venv venv
# Windows : venv\Scripts\activate    Linux/macOS : source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # puis remplir les valeurs si besoin
python manage.py migrate
python manage.py init_cabinet_info
python manage.py create_sample_products
python manage.py createsuperuser
python manage.py runserver
```

Les comptes **dentiste** et **secrétaire** se créent depuis l'administration (`/admin`) avec le compte superutilisateur.

## Configuration

Les variables sont lues depuis un fichier `.env` (voir `.env.example`). Ce fichier n'est **jamais** versionné.

| Variable | Rôle |
|---|---|
| `DJANGO_SECRET_KEY` | Clé secrète Django (obligatoire en production) |
| `DJANGO_DEBUG` | `True` en développement, `False` en production |
| `DJANGO_ALLOWED_HOSTS` | Hôtes autorisés, séparés par des virgules |
| `STRIPE_PUBLIC_KEY` / `STRIPE_SECRET_KEY` | Clés Stripe pour le paiement par carte |

## Tests

```bash
python manage.py test gestion_cabinet
```

## Limites connues

Les pages `/contact/`, `/services/`, `/equipe/`, `/dentistes/` et le détail d'un rendez-vous n'ont pas encore de template HTML. Aucun lien du site n'y mène.
