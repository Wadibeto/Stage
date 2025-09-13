import functions_framework
from flask import jsonify, request
import requests
import sys
import traceback

# Your Gemini API key
API_KEY = "AIzaSyD2yg211f1Xk9s0uEMdakmyWr6K1LLFdpY"

def log_error(error_message):
    print(f"ERROR: {error_message}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

@functions_framework.http
def gemini_exchange(request):
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

        if not message:
            log_error("No message provided")
            return jsonify({"error": "No message provided"}), 400

        # Prepare the request to the Gemini API
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY
        }
        payload = {
            "contents": [{
                "parts": [{
                    "text": message
                }]
            }]
        }

        # Make the request to the Gemini API
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # This will raise an exception for HTTP errors
    
        # Extract the generated text from the response
        generated_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        return jsonify({"response": generated_text})

    except requests.exceptions.RequestException as e:
        log_error(f"Error calling Gemini API: {str(e)}")
        return jsonify({"error": "Failed to get response from Gemini API", "details": str(e)}), 500
    except KeyError as e:
        log_error(f"Unexpected response format from Gemini API: {response.json()}")
        return jsonify({"error": "Unexpected response format from Gemini API", "details": str(e)}), 500
    except Exception as e:
        log_error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

