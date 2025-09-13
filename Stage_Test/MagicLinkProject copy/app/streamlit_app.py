import os
from dotenv import load_dotenv
import streamlit as st
import requests
import time
from datetime import datetime, timedelta

# Charger les variables d'environnement
load_dotenv()

# Utiliser la variable d'environnement pour l'URL de l'API
API_URL = os.environ.get('API_URL', 'http://localhost:8000')

st.title("Authentification via Magic Link")

# Initialisation des variables de session
if "email" not in st.session_state:
    st.session_state.email = ""
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "last_activity" not in st.session_state:
    st.session_state.last_activity = time.time()

def check_session():
    if st.session_state.email:
        response = requests.post(f"{API_URL}/check-session", json={"email": st.session_state.email})
        if response.status_code == 200:
            st.session_state.authenticated = True
            st.session_state.last_activity = time.time()
        else:
            st.session_state.authenticated = False
            st.session_state.email = ""
            st.warning("Session expirée. Veuillez vous reconnecter.")

# Vérification de la session à chaque rechargement de la page
check_session()

# Formulaire d'entrée email
email = st.text_input("Entrez votre email pour recevoir un Magic Link :", st.session_state.email)
if st.button("Envoyer le Magic Link"):
    response = requests.post(f"{API_URL}/send-magic-link", json={"email": email})
    if response.status_code == 200:
        st.success("Magic Link envoyé ! Vérifiez votre boîte mail.")
    else:
        st.error("Erreur lors de l'envoi du Magic Link.")

# Formulaire d'entrée du code
if email and not st.session_state.authenticated:
    code = st.text_input("Entrez le code reçu :")
    if st.button("Valider le code"):
        response = requests.post(f"{API_URL}/validate-magic-link", json={"email": email, "code": code})
        if response.status_code == 200:
            st.session_state.authenticated = True
            st.session_state.email = email
            st.session_state.last_activity = time.time()
            st.success("Authentification réussie !")
            st.rerun()
        else:
            st.error("Code invalide ou expiré.")

# Affichage du statut de l'utilisateur
if st.session_state.authenticated:
    st.success(f"Bienvenue, {st.session_state.email} !")
    st.write("Vous resterez connecté tant que cette page est ouverte ou que vous ne restez pas inactif pendant plus de 30 secondes.")

# Bouton de déconnexion
if st.session_state.authenticated:
    if st.button("Se déconnecter"):
        st.session_state.authenticated = False
        st.session_state.email = ""
        st.session_state.last_activity = None
        st.success("Vous avez été déconnecté.")
        st.rerun()

# Vérification périodique de la session
if st.session_state.authenticated:
    current_time = time.time()
    if current_time - st.session_state.last_activity > 30:
        check_session()
    else:
        # Mise à jour de l'activité
        requests.post(f"{API_URL}/update-activity", json={"email": st.session_state.email})
        st.session_state.last_activity = current_time