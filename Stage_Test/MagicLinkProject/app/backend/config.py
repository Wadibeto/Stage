import os
from firebase_admin import credentials, firestore, initialize_app
import json
import firebase_admin
from firebase_admin import credentials
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Vérifier si les variables sont bien chargées
print("SMTP_SERVER:", os.getenv("SMTP_SERVER"))
print("SMTP_EMAIL:", os.getenv("SMTP_EMAIL"))
print("SMTP_PASSWORD:", os.getenv("SMTP_PASSWORD"))

# Détermine le chemin absolu vers ton fichier JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "../../firebase/credentials/eternal-sylph-449610-r3-eb8969081109.json")

# Vérifie que le fichier existe avant de l'utiliser
if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
    raise ValueError(f"Fichier Firebase introuvable : {FIREBASE_CREDENTIALS_PATH}")

# Initialisation Firebase
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
TOKEN_EXPIRATION = int(os.getenv("TOKEN_EXPIRATION", 3600))

# Configuration SMTP
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Plus de valeur en dur