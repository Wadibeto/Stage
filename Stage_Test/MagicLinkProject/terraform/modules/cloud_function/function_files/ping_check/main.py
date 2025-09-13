import functions_framework
from flask import jsonify

@functions_framework.http
def ping_check(request):
    return jsonify({"status": "alive", "message": "Ping check successful!"})
