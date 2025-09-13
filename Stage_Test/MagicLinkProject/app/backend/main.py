from flask import Flask, request, jsonify, make_response  # Flask pour créer l'application web, request pour gérer les requêtes HTTP, jsonify pour retourner des réponses JSON, make_response pour créer des réponses HTTP personnalisées
import secrets  # Pour générer des chaînes aléatoires sécurisées
from datetime import datetime, timedelta, timezone  # Pour manipuler les dates et heures
import jwt  # Pour encoder et décoder les tokens JWT (JSON Web Tokens)
from config import db, SECRET_KEY, TOKEN_EXPIRATION  # Importation des configurations de la base de données, de la clé secrète et de la durée d'expiration du token
from utils import send_email  # Fonction personnalisée pour envoyer des emails
import os  # Pour interagir avec le système d'exploitation (variables d'environnement, etc.)
from dotenv import load_dotenv  # Pour charger les variables d'environnement depuis un fichier .env

# Chargement des variables d'environnement
load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")  # URL de l'API, par défaut "http://localhost:8000"

# Création de l'application Flask
app = Flask(__name__)

# Route pour envoyer un "magic link" par email
@app.route("/send-magic-link", methods=["POST"])
def send_magic_link():
    # Récupération des données JSON de la requête
    data = request.get_json()
    email = data.get("email")  # Extraction de l'email

    # Vérification que l'email est bien fourni
    if not email:
        return jsonify({"error": "Email is required"}), 400  # Retourne une erreur 400 si l'email est manquant

    try:
        # Génération d'un code magique sécurisé
        magic_code = secrets.token_hex(16)
        
        # Enregistrement du code magique et de la date de génération dans la base de données
        db.collection("users").document(email).set({
            "magic_code": magic_code,
            "generated_at": datetime.now(timezone.utc)
        }, merge=True)
        
        # Envoi du code magique par email
        send_email(email, magic_code)
        
        # Retourne un message de succès
        return jsonify({"message": "Magic Link sent!"})
    except Exception as e:
        # En cas d'erreur, retourne une erreur 500 avec le message d'erreur
        return jsonify({"error": f"Error sending magic link: {str(e)}"}), 500

# Route pour valider le "magic link"
@app.route("/validate-magic-link", methods=["POST"])
def validate_magic_link():
    # Récupération des données JSON de la requête
    data = request.get_json()
    email = data.get("email")
    code = data.get("code")

    # Vérification que l'email et le code sont bien fournis
    if not email or not code:
        return jsonify({"error": "Email and code are required"}), 400  # Retourne une erreur 400 si l'email ou le code est manquant

    try:
        # Récupération des données de l'utilisateur depuis la base de données
        user_ref = db.collection("users").document(email)
        user_data = user_ref.get()

        # Vérification que l'utilisateur existe
        if not user_data.exists:
            return jsonify({"error": "Email not found"}), 404  # Retourne une erreur 404 si l'email n'est pas trouvé

        # Récupération du code magique stocké
        stored_code = user_data.to_dict().get("magic_code")
        
        # Vérification que le code fourni correspond au code stocké
        if stored_code != code:
            return jsonify({"error": "Invalid code"}), 401  # Retourne une erreur 401 si le code est invalide

        # Calcul de la date d'expiration de la session
        session_expiry = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_EXPIRATION)
        
        # Génération d'un token JWT contenant l'email et la date d'expiration
        token = jwt.encode({"email": email, "exp": session_expiry.timestamp()}, SECRET_KEY, algorithm="HS256")

        # Mise à jour des données de l'utilisateur dans la base de données
        user_ref.set({
            "session_expiry": session_expiry.timestamp(),
            "authenticated": True
        }, merge=True)

        # Création d'une réponse HTTP avec un message de succès
        response = make_response(jsonify({"message": "Authentication successful", "session_expiry": session_expiry.timestamp()}))
        
        # Ajout du token JWT dans un cookie HTTPOnly sécurisé
        response.set_cookie(
            "session_token", token, httponly=True, 
            max_age=TOKEN_EXPIRATION, secure=os.getenv("FLASK_ENV") == "production",
            samesite='Strict'
        )
        return response
    except Exception as e:
        # En cas d'erreur, retourne une erreur 500 avec le message d'erreur
        return jsonify({"error": f"Error validating magic link: {str(e)}"}), 500

# Route pour vérifier l'état de la session
@app.route("/session-status", methods=["GET"])
def session_status():
    # Récupération du token JWT depuis les cookies
    token = request.cookies.get("session_token")
    
    # Vérification que le token est bien présent
    if not token:
        return jsonify({"status": "expired"}), 401  # Retourne une erreur 401 si le token est manquant

    try:
        # Décodage du token JWT pour vérifier son contenu
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload["email"]
        
        # Récupération des données de l'utilisateur depuis la base de données
        user_ref = db.collection("users").document(email)
        user_data = user_ref.get()
        
        # Vérification que l'utilisateur existe
        if not user_data.exists:
            return jsonify({"status": "expired"}), 401  # Retourne une erreur 401 si l'utilisateur n'existe pas

        # Vérification que la session n'a pas expiré
        if datetime.now(timezone.utc).timestamp() >= user_data.to_dict().get("session_expiry", 0):
            return jsonify({"status": "expired"}), 401  # Retourne une erreur 401 si la session est expirée

        # Retourne un message indiquant que la session est active
        return jsonify({"status": "active", "email": email})
    except jwt.ExpiredSignatureError:
        return jsonify({"status": "expired"}), 401  # Retourne une erreur 401 si le token est expiré
    except jwt.InvalidTokenError:
        return jsonify({"status": "invalid"}), 401  # Retourne une erreur 401 si le token est invalide
    except Exception as e:
        return jsonify({"error": f"Error checking session: {str(e)}"}), 500  # Retourne une erreur 500 en cas d'erreur inattendue

# Route pour rafraîchir la session
@app.route("/refresh-session", methods=["POST"])
def refresh_session():
    # Récupération du token JWT depuis les cookies
    token = request.cookies.get("session_token")
    
    # Vérification que le token est bien présent
    if not token:
        return jsonify({"error": "Session expired or missing"}), 401  # Retourne une erreur 401 si le token est manquant

    try:
        # Décodage du token JWT pour vérifier son contenu
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload["email"]

        # Calcul de la nouvelle date d'expiration de la session
        session_expiry = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_EXPIRATION)
        
        # Génération d'un nouveau token JWT
        new_token = jwt.encode({"email": email, "exp": session_expiry.timestamp()}, SECRET_KEY, algorithm="HS256")

        # Mise à jour des données de l'utilisateur dans la base de données
        user_ref = db.collection("users").document(email)
        user_ref.set({
            "session_expiry": session_expiry.timestamp(),
            "authenticated": True
        }, merge=True)

        # Création d'une réponse HTTP avec un message de succès
        response = make_response(jsonify({"message": "Session refreshed", "session_expiry": session_expiry.timestamp()}))
        
        # Ajout du nouveau token JWT dans un cookie HTTPOnly sécurisé
        response.set_cookie(
            "session_token", new_token, httponly=True, 
            max_age=TOKEN_EXPIRATION, secure=os.getenv("FLASK_ENV") == "production",
            samesite='Strict'
        )
        return response
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return jsonify({"error": "Session expired"}), 401  # Retourne une erreur 401 si le token est expiré ou invalide
    except Exception as e:
        return jsonify({"error": f"Error refreshing session: {str(e)}"}), 500  # Retourne une erreur 500 en cas d'erreur inattendue

# Route pour déconnecter l'utilisateur
@app.route("/logout", methods=["POST"])
def logout():
    # Création d'une réponse HTTP avec un message de succès
    response = make_response(jsonify({"message": "Logout successful"}))
    
    # Suppression du cookie de session
    response.delete_cookie("session_token")
    return response

# Point d'entrée de l'application
if __name__ == "__main__":
    # Utilisation de Waitress pour servir l'application en production
    from waitress import serve
    port = int(os.getenv("PORT", 8080))  # Récupération du port depuis les variables d'environnement, par défaut 8080
    serve(app, host="0.0.0.0", port=port)  # Démarrage du serveur sur toutes les interfaces réseau et sur le port spécifié