# File: MagicLinkProject/terraform/modules/cloud_function/function_files/auth0_function/main.py
import os
import json
import requests
import functions_framework
from flask import request, jsonify, g
from functools import wraps
from jose import jwt

# Configuration via variables d'environnement
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "dev-nkfmhxcx7ip44wwh.us.auth0.com")
API_IDENTIFIER = os.getenv("API_IDENTIFIER", "https://dev-nkfmhxcx7ip44wwh.us.auth0.com/api/v2/")
ALGORITHMS = ["RS256"]

# Fonction pour valider le token JWT
def verify_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token manquant ou mal formaté"}), 401

        token = auth_header.split("Bearer ")[1]

        try:
            # Récupération de la clé publique Auth0
            jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
            jwks = requests.get(jwks_url).json()
            header = jwt.get_unverified_header(token)
            
            rsa_key = next(
                (key for key in jwks["keys"] if key["kid"] == header["kid"]), None
            )

            if not rsa_key:
                return jsonify({"error": "Clé de signature non trouvée"}), 401

            # Vérification du token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_IDENTIFIER,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )

            g.user = payload
            return f(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expiré"}), 401
        except jwt.JWTClaimsError:
            return jsonify({"error": "Mauvaises claims dans le token"}), 401
        except Exception as e:
            return jsonify({"error": f"Erreur de validation du token: {str(e)}"}), 401

    return decorated

# Route protégée pour récupérer les infos d'un utilisateur
@functions_framework.http
@verify_token
def auth0_function(request):
    return jsonify({"user": g.user})
