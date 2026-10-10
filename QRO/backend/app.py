"""
QuantumRoute Backend Application

VNQFF-08
Quantum-Enhanced Last-Mile Route Optimisation
"""

from flask import Flask, jsonify
from flask_cors import CORS

from api import api


# ============================================================
# CREATE FLASK APPLICATION
# ============================================================

app = Flask(__name__)

# Allow frontend to communicate with backend
CORS(app)


# ============================================================
# REGISTER API BLUEPRINT
# ============================================================

app.register_blueprint(
    api,
    url_prefix="/api"
)


# ============================================================
# HOME ROUTE
# ============================================================

@app.route("/", methods=["GET"])
def home():
    """
    Basic endpoint to verify that QuantumRoute backend
    is running successfully.
    """

    return jsonify({
        "success": True,
        "project": "QuantumRoute",
        "problem_statement": "VNQFF-08",
        "application": "Quantum-Enhanced Last-Mile Route Optimisation",
        "message": "QuantumRoute backend is running successfully",
        "server": "http://127.0.0.1:5000",
        "api": "http://127.0.0.1:5000/api"
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    """
    Health-check endpoint.
    """

    return jsonify({
        "success": True,
        "status": "healthy",
        "service": "QuantumRoute Backend"
    })


# ============================================================
# API HEALTH CHECK
# ============================================================

@app.route("/api/status", methods=["GET"])
def api_status():
    """
    API status endpoint.
    """

    return jsonify({
        "success": True,
        "status": "online",
        "project": "QuantumRoute",
        "problem_statement": "VNQFF-08"
    })


# ============================================================
# 404 ERROR HANDLER
# ============================================================

@app.errorhandler(404)
def page_not_found(error):
    """
    Handles requests to endpoints that do not exist.
    """

    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "The requested API endpoint does not exist."
    }), 404


# ============================================================
# 405 ERROR HANDLER
# ============================================================

@app.errorhandler(405)
def method_not_allowed(error):
    """
    Handles unsupported HTTP methods.
    """

    return jsonify({
        "success": False,
        "error": "Method not allowed",
        "message": "The HTTP method used for this endpoint is not supported."
    }), 405


# ============================================================
# 500 ERROR HANDLER
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):
    """
    Handles unexpected server errors.
    """

    import traceback

    traceback.print_exc()

    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": str(error)
    }), 500


# ============================================================
# APPLICATION STARTUP
# ============================================================

def start_server():
    """
    Starts the QuantumRoute Flask backend.
    """

    print()
    print("=" * 60)
    print("              QUANTUMROUTE BACKEND")
    print("=" * 60)
    print()
    print("Problem Statement : VNQFF-08")
    print("Application       : Quantum-Enhanced Last-Mile Route Optimisation")
    print()
    print("Server URL        : http://127.0.0.1:5000")
    print("API URL           : http://127.0.0.1:5000/api")
    print("Health Check      : http://127.0.0.1:5000/health")
    print("API Status        : http://127.0.0.1:5000/api/status")
    print()
    print("Frontend should connect to:")
    print("http://127.0.0.1:5000")
    print()
    print("=" * 60)
    print("              SERVER STARTING...")
    print("=" * 60)
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    start_server()