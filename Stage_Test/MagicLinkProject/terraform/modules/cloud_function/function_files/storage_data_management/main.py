import functions_framework
from flask import jsonify, request
from google.cloud import firestore
import datetime

# Initialize Firestore client
db = firestore.Client()

@functions_framework.http
def storage_data_management(request):
    if request.method == 'POST':
        return store_user_data(request)
    elif request.method == 'GET':
        return get_user_data(request)
    else:
        return jsonify({"error": "Method not allowed"}), 405

def store_user_data(request):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_id = data.get('userid')
        content = data.get('content')
        date = data.get('date')

        if not all([user_id, content, date]):
            return jsonify({"error": "Missing required fields"}), 400

        # Convert date string to datetime object
        date = datetime.datetime.fromisoformat(date)

        # Store data in Firestore
        doc_ref = db.collection('user_data').document(user_id)
        doc_ref.set({
            'content': content,
            'date': date,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_user_data(request):
    try:
        user_id = request.args.get('userid')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Retrieve data from Firestore
        doc_ref = db.collection('user_data').document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            # Convert date to ISO format string for JSON serialization
            data['date'] = data['date'].isoformat()
            return jsonify(data), 200
        else:
            return jsonify({"error": "User data not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
