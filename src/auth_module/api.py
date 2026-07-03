"""Flask HTTP layer exposing the AuthService as a REST API."""
from __future__ import annotations

from flask import Flask, jsonify, request

from .service import AuthService, InvalidCredentialsError, LockedAccountError


def create_app(auth_service: AuthService | None = None) -> Flask:
    app = Flask(__name__)
    service = auth_service or AuthService()

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.post("/register")
    def register():
        body = request.get_json(silent=True) or {}
        try:
            created = service.register(body.get("username", ""), body.get("password", ""))
            return jsonify(created), 201
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @app.post("/login")
    def login():
        body = request.get_json(silent=True) or {}
        try:
            token = service.login(body.get("username", ""), body.get("password", ""))
            return jsonify({"token": token}), 200
        except LockedAccountError as exc:
            return jsonify({"error": str(exc)}), 423
        except InvalidCredentialsError as exc:
            return jsonify({"error": str(exc)}), 401

    @app.post("/validate")
    def validate():
        body = request.get_json(silent=True) or {}
        valid = service.validate_token(body.get("token", ""))
        return jsonify({"valid": valid}), 200

    return app
