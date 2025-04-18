# Cabinet Médical - Gestion

## Description
Application de gestion pour un cabinet médical permettant de:
- Gérer la liste des patients
- Suivre les rendez-vous et les visites
- Enregistrer les paiements
- Générer des rapports
- Gérer les utilisateurs et les permissions

## Base de données
### Structure de la base de données
La base de données est implémentée avec SQLite et utilise plusieurs tables pour stocker les données pertinentes:

1. `users`:
   - Gère les comptes utilisateur (administrateurs, médecins, assistants)
   - Inclut des champs pour:
     - `user_id` (clé primaire)
     - `username` (nom d'utilisateur unique)
     - `password_hash` (mot de passe haché)
     - `role` (rôle de l'utilisateur: Admin, Médecin, Assistant)
     - `active` (statut de compte)

2. `patients`:
   - Stocke les informations des patients
   - Inclut des champs pour:
     - `patient_id` (clé primaire)
     - `name` (nom complet du patient)
     - `phone_number` (numéro de téléphone, optionnel)
     - `birth_date` (date de naissance)
     - `gender` (sexe)
     - `notes` (remarques médicales)

3. `visits`:
   - Suivi des visites des patients
   - Inclut des champs pour:
     - `visit_id` (clé primaire)
     - `patient_id` (clé étrangère vers patients)
     - `doctor_id` (clé étrangère vers users)
     - `visit_date` (date de la visite)
     - `checkout_at` (heure de fin de consultation)
     - `total_paid` (montant payé)
     - `status` (statut de la visite: En attente, En consultation, Terminée)

4. `services`:
   - Liste des services médicaux offerts
   - Inclut des champs pour:
     - `service_id` (clé primaire)
     - `name` (nom du service)
     - `price` (prix en DA)
     - `description` (description détaillée)
     - `active` (statut du service)

5. `visit_services`:
   - Relève les services fournis pendant une consultation
   - Inclut des champs pour:
     - `visit_service_id` (clé primaire)
     - `visit_id` (clé étrangère vers visits)
     - `service_id` (clé étrangère vers services)
     - `quantity` (quantité utilisée)
     - `total` (montant total pour ce service)

### Relations entre les tables
Les tables sont liées entre elles via des clés étrangères pour permettre une gestion一条龙 des données médicales et financières. Par exemple:
- Une `visit` est liée à un `patient` et éventuellement à un `doctor` via des clés étrangères.
- Les `services` utilisés pendant une consultation sont stockés dans `visit_services`, avec des liens vers la `visit` et le `service` concerned.

### Exemple de structure SQL
```sql
-- Table des utilisateurs
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Admin', 'Médecin', 'Assistant')),
    active BOOLEAN DEFAULT TRUE
);

-- Table des patients
CREATE TABLE patients (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone_number TEXT,
    birth_date TEXT,
    gender TEXT,
    notes TEXT
);

-- Table des visites
CREATE TABLE visits (
    visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER,
    visit_date TEXT NOT NULL,
    checkout_at TEXT,
    total_paid INTEGER DEFAULT 0,
    status TEXT NOT NULL CHECK (status IN ('En attente', 'En consultation', 'Terminée')),
    FOREIGN KEY(doctor_id) REFERENCES users(user_id)
);

-- Table des services
CREATE TABLE services (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE
);

-- Table des services utilisés
CREATE TABLE visit_services (
    visit_service_id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    total INTEGER NOT NULL,
    FOREIGN KEY(visit_id) REFERENCES visits(visit_id),
    FOREIGN KEY(service_id) REFERENCES services(service_id)
);
```

Cette structure permet une gestion efficiente des données, en liant étroitement les informations sur les patients, les visites, les services et les utilisateurs.

## Technologies utilisées
### Langages et bibliothèques
- Python
  - Tkinter pour l'interface graphique
  - SQLite pour la base de données
  - Babel pour la gestion des locales (français)
  - PIL ( Pillow ) pour la gestion des images
  - Matplotlib pour les graphiques

### Architecture
- Modèle MVC (Modèle-Vue-Contrôleur)
- Base de données SQLite
- Gestion des transactions via un système de comptabilité intégré
- Interface utilisateur orientée objets avec Tkinter

## Configuration et Installation

### Prérequis
- Python 3.10 ou version supérieure
- Les dépendances peuvent être installées via pip:
```bash
pip install -r requirements.txt
```

### Base de données
La base de données est stockée dans le fichier `medical_office.db` dans le répertoire actuel.

## Utilisation
### Lancement de l'application
```bash
python app.py
```

### Interface utilisateur principale
1. Connexion:
   - Interface de connexion pour les utilisateurs (admin, médecin, assistant)
   - Gestion des comptes via la sidebar

2. Gestion des patients:
   - Liste des patients avec recherche
   - Ajout/modification des patients
   - Historique des visites

3. Suivi des rendez-vous:
   - Liste d'attente
   - Appel des patients
   - Gestion du temps de consultation

4. Gestion des paiements:
   - Enregistrement des paiements
   - Facturation
   - Suivi des paiements

5. Rapports:
   - Statistiques sur les visites
   - Rapports financiers
   - Historique des consultations

## Développement
### Structure du projet
```
cabinet_medical/
├── app.py                 # Point d'entrée principal
├── database.py           # Gestion de la base de données
├── ui/                   # Interface utilisateur
│   ├── patient_list_dialog.py
│   ├── payment_gui.py
│   └── ...
├── migrations/          # Migrations de base de données
├── accounting/          # Gestion des finances
└── reports/             # Génération de rapports
```

### Contributing
Tous les contributeurs doivent:
1. Créer une branche pour leurs modifications
2. Faire des commits clairs et des push
3. Créer une Pull Request contre la branche principale
#   w a i t i n g - r o o m  
 #   G e s t i o n - s a l l e - a t t e n t e  
 #   G e s t i o n - s a l l e - a t t e n t e  
 