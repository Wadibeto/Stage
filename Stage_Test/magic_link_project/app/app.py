import streamlit as st
import requests
import jwt
import datetime
import os

# Clé secrète pour signer les tokens JWT (à remplacer par une vraie clé secrète en production)
SECRET_KEY = "votre_cle_secrete_tres_longue_et_complexe"

def create_magic_link(email):
    # Créer un token JWT
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    token = jwt.encode({"email": email, "exp": expiration}, SECRET_KEY, algorithm="HS256")
    
    # Dans un vrai scénario, vous enverriez ce lien par email
    magic_link = f"http://localhost:8501/verify?token={token}"
    return magic_link

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload['email']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def main():
    st.title("Magic Link Demo")

    # Vérifier si un token est présent dans l'URL
    token = st.experimental_get_query_params().get("token")
    if token:
        email = verify_token(token[0])
        if email:
            st.success(f"Authentification réussie pour {email}")
        else:
            st.error("Lien invalide ou expiré")
    else:
        email = st.text_input("Entrez votre adresse e-mail")
        if st.button("Envoyer Magic Link"):
            magic_link = create_magic_link(email)
            st.success(f"Magic Link créé : {magic_link}")
            st.info("Dans un vrai scénario, ce lien serait envoyé par email.")

if __name__ == "__main__":
    main()