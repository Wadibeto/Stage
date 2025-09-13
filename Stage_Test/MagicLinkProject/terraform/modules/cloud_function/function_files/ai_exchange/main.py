import functions_framework
from flask import jsonify

@functions_framework.http
def ai_exchange(request):
    return jsonify({"message": "Hello from AI Exchange!"})
