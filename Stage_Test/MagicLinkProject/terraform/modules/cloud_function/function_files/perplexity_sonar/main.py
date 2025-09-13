import functions_framework
from flask import jsonify, request
import requests
import sys
import traceback
from google.cloud import firestore
from pydantic import BaseModel
from typing import Dict
import json

# Initialize Firestore client
db = firestore.Client()

# Perplexity API key
API_KEY = "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"

class AnswerFormat(BaseModel):
    title: str
    summary: str
    key_points: Dict[str, str]

def log_error(error_message):
    print(f"ERROR: {error_message}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

def log_debug(message):
    print(f"DEBUG: {message}", file=sys.stdout)

@functions_framework.http
def perplexity_sonar(request):
    try:
        # Check if it's a GET request for ping
        if request.method == 'GET':
            return jsonify({"status": "OK", "message": "Ping successful"}), 200

        # If it's not a GET request, proceed with the function logic
        request_json = request.get_json(silent=True)
        
        if not request_json:
            log_error("No JSON data provided")
            return jsonify({"error": "No JSON data provided"}), 400

        message = request_json.get('message', '')
        parameters = request_json.get('parameters', {})

        if not message:
            log_error("No message provided")
            return jsonify({"error": "No message provided"}), 400

        # Prepare the request to the Perplexity API
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "sonar-medium-online",
            "messages": [
                {"role": "system", "content": "Be precise and concise."},
                {"role": "user", "content": (
                    f"{message} "
                    "Please output a JSON object containing the following fields: "
                    "title (a brief title), summary (a concise summary), "
                    "and key_points (a dictionary with at least 3 key-value pairs)."
                )},
            ],
            "max_tokens": parameters.get('max_tokens', 1000),
            "temperature": parameters.get('temperature', 0.7),
            "top_p": parameters.get('top_p', 1.0)
        }

        # Debug logging
        log_debug(f"Request URL: {url}")
        log_debug(f"Request Headers: {json.dumps({k: v for k, v in headers.items() if k != 'Authorization'})}")
        log_debug(f"Request Payload: {json.dumps(payload)}")

        # Make the request to the Perplexity API
        response = requests.post(url, headers=headers, json=payload)
        
        # Debug logging
        log_debug(f"Response Status: {response.status_code}")
        log_debug(f"Response Headers: {json.dumps(dict(response.headers))}")
        log_debug(f"Response Content: {response.text[:1000]}...")  # Log first 1000 characters

        if response.status_code == 401:
            log_error(f"Authentication failed. Response: {response.text}")
            return jsonify({
                "error": "Authentication failed",
                "details": "Please verify your Perplexity API key",
                "response": response.text
            }), 401

        response.raise_for_status()
    
        # Extract the generated text from the response
        response_json = response.json()
        log_debug(f"Response JSON: {json.dumps(response_json)}")

        generated_content = response_json['choices'][0]['message']['content']

        # Validate response format using Pydantic
        validated_response = AnswerFormat.model_validate_json(generated_content)

        # Store the request and response in Firestore
        doc_ref = db.collection('perplexity_sonar_exchanges').document()
        doc_ref.set({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'user_message': message,
            'ai_response': validated_response.model_dump(),
            'model': 'sonar-medium-online'
        })

        return jsonify({
            "response": validated_response.model_dump(),
            "model": "sonar-medium-online",
            "usage": response_json.get('usage', {})
        })

    except requests.exceptions.RequestException as e:
        log_error(f"Error calling Perplexity API: {str(e)}")
        return jsonify({
            "error": "Failed to get response from Perplexity API",
            "details": str(e),
            "status_code": getattr(e.response, 'status_code', None),
            "response_text": getattr(e.response, 'text', None)
        }), 500
    except Exception as e:
        log_error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

