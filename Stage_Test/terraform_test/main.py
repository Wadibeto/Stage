from flask import jsonify
import pandas as pd
import io
from datetime import datetime
from google.cloud import storage, firestore
import uuid

# Initialiser Firestore
db = firestore.Client()

# Initialiser le client Storage
storage_client = storage.Client()

# Nom du bucket et fichier logs
BUCKET_NAME = "omega-wind-448707-r4-functions"
LOGS_FILE = "logs.txt"

# Télécharger les logs depuis le bucket
def download_logs():
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(LOGS_FILE)
    if not blob.exists():
        return ""
    return blob.download_as_text()

# Uploader les logs dans le bucket
def upload_logs(content):
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(LOGS_FILE)
    blob.upload_from_string(content)

# Enregistrer un log dans Firestore
def save_log_to_firestore(user_id, log_entry):
    try:
        # Diviser le log en parties
        parts = log_entry.split(" | ")
        if len(parts) != 3:
            raise ValueError("Format de log invalide.")

        log_data = {
            "user_id": user_id,
            "timestamp": parts[1].strip(),
            "file_size": int(parts[2].split()[0]),  # Extraire la taille du fichier
        }

        # Enregistrer dans Firestore
        db.collection("logs").add(log_data)
    except Exception as e:
        print(f"Erreur lors de l'enregistrement dans Firestore : {e}")

# Fonction pour convertir CSV en JSON
def function_1_handler(request):
    try:
        request_json = request.get_json(silent=True)
        if not request_json or 'csv_content' not in request_json:
            return jsonify({"error": "Invalid request payload."}), 400

        # Générer un user_id ou utiliser celui fourni
        user_id = request_json.get('user_id', str(uuid.uuid4()))
        csv_content = request_json['csv_content']

        # Vérifier et convertir le CSV en DataFrame
        try:
            csv_buffer = io.StringIO(csv_content)
            df = pd.read_csv(csv_buffer)
        except Exception as e:
            return jsonify({"error": f"Erreur lors de la lecture du CSV: {str(e)}"}), 400

        # Convertir en JSON
        json_data = df.to_json(orient="records", indent=4, force_ascii=False)

        # Créer une entrée de log
        log_entry = f"{user_id} | {datetime.now()} | {len(json_data)} caractères"

        # Sauvegarder dans Firestore
        save_log_to_firestore(user_id, log_entry)

        # Ajouter le log au fichier logs.txt
        logs = download_logs()
        logs += log_entry + "\n"
        upload_logs(logs)

        return jsonify({"json": json_data})
    except Exception as e:
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500

# Fonction pour récupérer les logs
def function_2_handler(request):
    try:
        logs = download_logs()
        if not logs:
            return jsonify({"error": "Aucun log trouvé."}), 404

        return jsonify({"logs": logs.splitlines()})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
