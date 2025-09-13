import functions_framework
from flask import jsonify, request
import google.auth
import google.auth.transport.requests
import requests
import sys
import traceback
import json
from google.cloud import firestore

# Initialize Firestore client
db = firestore.Client()

# Your Gemini API key
API_KEY = "AIzaSyD2yg211f1Xk9s0uEMdakmyWr6K1LLFdpY"

# Pre-prompt instruction
PRE_PROMPT = """You are an AI assistant specialized in providing insights and recommendations. 
Your task is to analyze the user's input and provide a response in the following JSON format:

{
  "title": "A concise title summarizing the main point",
  "description": "A brief description or overview of the analysis",
  "recommendations": [
    {
      "icon": "A suitable Lucide icon name",
      "text": "Detailed explanation of the recommendation"
    },
    // ... more recommendations ...
  ]
}

Ensure that your response is a valid JSON object with these exact keys. 
The 'recommendations' array should contain at least 3 items, each with 'icon' and 'text' fields."""

def log_error(error_message):
    print(f"ERROR: {error_message}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

@functions_framework.http
def gemini_complicated(request):
    try:
        # Check if it's a GET request for ping
        if request.method == 'GET':
            return jsonify({"status": "OK", "message": "Ping successful"}), 200

        # If it's not a GET request, proceed with the original function logic
        request_json = request.get_json(silent=True)
        
        if not request_json:
            log_error("No JSON data provided")
            return jsonify({"error": "No JSON data provided"}), 400

        message = request_json.get('message', '')
        parameters = request_json.get('parameters', {})

        if not message:
            log_error("No message provided")
            return jsonify({"error": "No message provided"}), 400

        # Combine pre-prompt and user message
        full_prompt = f"{PRE_PROMPT}\n\nUser Input: {message}"

        # Prepare the request to the Gemini API
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY
        }
        payload = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "temperature": parameters.get('temperature', 0.7),
                "maxOutputTokens": parameters.get('max_tokens', 1000),
            }
        }

        # Make the request to the Gemini API
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # This will raise an exception for HTTP errors
    
        # Extract the generated text from the response
        generated_text = response.json()['candidates'][0]['content']['parts'][0]['text']

        # Parse the JSON response
        try:
            parsed_response = json.loads(generated_text)
            
            # Validate the structure of the parsed response
            if not all(key in parsed_response for key in ['title', 'description', 'recommendations']):
                raise ValueError("Missing required keys in the response")
            
            if not isinstance(parsed_response['recommendations'], list) or len(parsed_response['recommendations']) < 3:
                raise ValueError("'recommendations' should be a list with at least 3 items")
            
            for rec in parsed_response['recommendations']:
                if not all(key in rec for key in ['icon', 'text']):
                    raise ValueError("Each recommendation should have 'icon' and 'text' fields")
            
        except json.JSONDecodeError as e:
            log_error(f"Failed to parse JSON from Gemini API response: {generated_text}")
            return jsonify({
                "error": "Invalid JSON format in Gemini API response",
                "raw_response": generated_text,
                "details": str(e)
            }), 500
        except ValueError as e:
            log_error(f"Invalid structure in Gemini API response: {generated_text}")
            return jsonify({
                "error": "Invalid structure in Gemini API response",
                "raw_response": generated_text,
                "details": str(e)
            }), 500

        # Store the request and response in Firestore
        doc_ref = db.collection('gemini_complicated_exchanges').document()
        doc_ref.set({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'user_message': message,
            'ai_response': parsed_response
        })

        return jsonify(parsed_response)

    except requests.exceptions.RequestException as e:
        log_error(f"Error calling Gemini API: {str(e)}")
        return jsonify({"error": "Failed to get response from Gemini API", "details": str(e)}), 500
    except KeyError as e:
        log_error(f"Unexpected response format from Gemini API: {response.json()}")
        return jsonify({
            "error": "Unexpected response format from Gemini API",
            "raw_response": response.json(),
            "details": str(e)
        }), 500
    except Exception as e:
        log_error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

