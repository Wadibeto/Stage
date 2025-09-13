import os
from dotenv import load_dotenv
import streamlit as st
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Charger les variables d'environnement depuis le fichier .env
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")
API_URL = os.getenv("API_URL", "http://localhost:8000")
SESSION_REFRESH_INTERVAL = 60  # Rafraîchir la session toutes les 60 secondes

def init_session_state():
    """Initialise les variables d'état de session Streamlit."""
    if "email" not in st.session_state:
        st.session_state.email = ""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "session_expiry" not in st.session_state:
        st.session_state.session_expiry = None
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = datetime.now(timezone.utc)
    if "cookies" not in st.session_state:
        st.session_state.cookies = None

def reset_session():
    """Réinitialise toutes les variables de session."""
    st.session_state.authenticated = False
    st.session_state.email = ""
    st.session_state.session_expiry = None
    st.session_state.last_activity = datetime.now(timezone.utc)
    st.session_state.cookies = None

def check_session():
    """Vérifie si la session actuelle est toujours valide."""
    if st.session_state.authenticated and st.session_state.cookies:
        try:
            response = requests.post(f"{API_URL}/check-session", cookies=st.session_state.cookies)
            if response.status_code == 200:
                data = response.json()
                session_expiry = data.get("session_expiry")
                if session_expiry is None:
                    reset_session()
                    return False
                st.session_state.session_expiry = datetime.fromtimestamp(session_expiry, timezone.utc)
                st.session_state.last_activity = datetime.now(timezone.utc)
                st.session_state.email = data.get("email")
                return True
            else:
                reset_session()
                return False
        except requests.RequestException:
            return False
    return False

def refresh_session():
    """Rafraîchit la session actuelle si elle est toujours valide."""
    if st.session_state.authenticated and st.session_state.cookies:
        try:
            response = requests.post(f"{API_URL}/refresh-session", cookies=st.session_state.cookies)
            if response.status_code == 200:
                data = response.json()
                session_expiry = data.get("session_expiry")
                if session_expiry is None:
                    return False
                st.session_state.session_expiry = datetime.fromtimestamp(session_expiry, timezone.utc)
                st.session_state.cookies = requests.utils.dict_from_cookiejar(response.cookies)
                st.session_state.last_activity = datetime.now(timezone.utc)
                return True
        except requests.RequestException:
            return False
    return False

def send_magic_link(email):
    """Envoie un Magic Link à l'adresse e-mail fournie."""
    try:
        response = requests.post(f"{API_URL}/send-magic-link", json={"email": email})
        if response.status_code == 200:
            st.success("Magic Link envoyé ! Vérifiez votre boîte mail.")
        else:
            st.error("Erreur lors de l'envoi du Magic Link.")
    except requests.RequestException:
        st.error("Erreur de connexion au serveur.")

def validate_code(email, code):
    """Valide le code Magic Link reçu par l'utilisateur."""
    try:
        response = requests.post(f"{API_URL}/validate-magic-link", json={"email": email, "code": code})
        if response.status_code == 200:
            data = response.json()
            session_expiry = data.get("session_expiry")
            if session_expiry is None:
                st.error("Erreur: Pas de session_expiry retourné.")
                return False
            st.session_state.authenticated = True
            st.session_state.email = email
            st.session_state.session_expiry = datetime.fromtimestamp(session_expiry, timezone.utc)
            st.session_state.cookies = requests.utils.dict_from_cookiejar(response.cookies)
            st.success("Authentification réussie !")
            return True
        else:
            st.error("Code invalide ou expiré.")
            return False
    except requests.RequestException:
        st.error("Erreur de connexion au serveur.")
        return False

def logout():
    """Déconnecte l'utilisateur et réinitialise la session."""
    if st.session_state.cookies:
        try:
            requests.post(f"{API_URL}/logout", cookies=st.session_state.cookies)
        except requests.RequestException:
            pass
    reset_session()

def display_session_info():
    """Affiche les informations de session dans la barre latérale."""
    st.sidebar.subheader("Informations de session")
    st.sidebar.write(f"Email: {st.session_state.email}")
    if st.session_state.session_expiry:
        expiry_time = st.session_state.session_expiry.strftime("%Y-%m-%d %H:%M:%S")
        st.sidebar.write(f"Expiration de la session: {expiry_time}")
    st.sidebar.write(f"Dernière activité: {st.session_state.last_activity.strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Fonction principale qui gère l'interface utilisateur et le flux d'authentification."""
    st.title("Authentification via Magic Link")
    init_session_state()
    is_session_valid = check_session()

    if not st.session_state.authenticated:
        # Afficher le formulaire de connexion si l'utilisateur n'est pas authentifié
        email = st.text_input("Entrez votre email pour recevoir un Magic Link :", st.session_state.email)
        if st.button("Envoyer le Magic Link"):
            send_magic_link(email)
        if email:
            code = st.text_input("Entrez le code reçu :")
            if st.button("Valider le code"):
                if validate_code(email, code):
                    st.rerun()
    else:
        # Afficher le message de bienvenue si l'utilisateur est authentifié
        st.success(f"Bienvenue, {st.session_state.email} !")
        st.write("Vous êtes connecté. Votre session restera active tant que vous interagissez avec l'application.")
        
        # Afficher les informations de session dans la barre latérale
        display_session_info()
        
        if st.button("Se déconnecter"):
            logout()
            st.rerun()

    # Vérifier si la session a expiré
    if st.session_state.authenticated and st.session_state.session_expiry:
        if datetime.now(timezone.utc) > st.session_state.session_expiry:
            reset_session()
            st.warning("Session expirée. Veuillez vous reconnecter.")

    # Mettre à jour le timestamp de dernière activité
    st.session_state.last_activity = datetime.now(timezone.utc)

if __name__ == "__main__":
    main()

