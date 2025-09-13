# File: app.py
import streamlit as st  # Interface utilisateur
import pandas as pd  # Manipulation de données
import requests  # Requêtes HTTP
import uuid  # Génération d'IDs uniques

# URL de l'API Flask déployée
API_URL = "https://europe-west6-omega-wind-448707-r4.cloudfunctions.net/convert-csv-to-json"

def main():
    """
    Fonction principale de l'application Streamlit
    """
    st.title("Convertisseur CSV en JSON")  # Titre principal
    st.write("Importez un fichier CSV et convertissez-le en JSON facilement.")

    # Barre latérale pour l'importation et les paramètres
    st.sidebar.header("Options")
    uploaded_file = st.sidebar.file_uploader("Importer un fichier CSV", type=["csv"])  # Upload de fichier CSV

    if uploaded_file is not None:
        try:
            # Lecture et affichage du fichier CSV
            df = pd.read_csv(uploaded_file)
            st.write("### Aperçu du fichier CSV :")
            st.dataframe(df)

            # Bouton pour lancer la conversion
            if st.button("Convertir en JSON"):
                # Génération d'un user_id unique
                user_id = str(uuid.uuid4())
                csv_content = uploaded_file.getvalue().decode("utf-8")  # Lecture du contenu du fichier

                try:
                    # Envoi de la requête POST à l'API
                    response = requests.post(
                        API_URL,
                        json={"user_id": user_id, "csv_content": csv_content}
                    )

                    # Traitement de la réponse
                    if response.status_code == 200:
                        response_data = response.json()
                        st.write("### Résultat JSON :")
                        st.json(response_data["json"])  # Afficher le JSON formaté
                        st.success("Conversion réussie ! Les logs ont été sauvegardés.")
                    else:
                        st.error(f"Erreur de conversion : {response.json().get('error', 'Erreur inconnue')}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Erreur de connexion à l'API : {e}")

        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier CSV : {e}")

if __name__ == "__main__":
    main()
