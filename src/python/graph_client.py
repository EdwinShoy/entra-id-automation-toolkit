"""
graph_client.py

Handles OAuth 2.0 client credentials auth against Microsoft Entra ID and
provides a thin wrapper for calling Microsoft Graph API endpoints.

Also owns audit logging: every call made through `GraphClient.request` is
logged with timestamp, method, endpoint, and outcome.
"""

import json
import logging
import os
from pathlib import Path

import msal
import requests

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CONFIG_PATH}. Copy config.example.json to config.json and fill it in."
        )
    with open(CONFIG_PATH) as f:
        return json.load(f)


def setup_logger(log_path: str) -> logging.Logger:
    logger = logging.getLogger("entra_toolkit")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        handler = logging.FileHandler(log_path)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        logger.addHandler(handler)
        logger.addHandler(logging.StreamHandler())
    return logger


class GraphClient:
    """Thin authenticated wrapper around the Microsoft Graph REST API."""

    def __init__(self, config: dict | None = None):
        self.config = config or load_config()
        self.logger = setup_logger(self.config.get("logFilePath", "../logs/audit.log"))
        self._token = None

    def _get_token(self) -> str:
        if self._token:
            return self._token

        app = msal.ConfidentialClientApplication(
            client_id=self.config["clientId"],
            client_credential=self.config["clientSecret"],
            authority=f"https://login.microsoftonline.com/{self.config['tenantId']}",
        )
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        if "access_token" not in result:
            raise RuntimeError(f"Token acquisition failed: {result.get('error_description')}")

        self._token = result["access_token"]
        return self._token

    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an authenticated Graph API call and log the outcome.

        endpoint: path relative to graphBaseUrl, e.g. "/users"
        """
        url = f"{self.config['graphBaseUrl']}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._get_token()}"
        headers.setdefault("Content-Type", "application/json")

        response = requests.request(method, url, headers=headers, **kwargs)

        outcome = "SUCCESS" if response.ok else "FAILED"
        self.logger.info(
            "%s %s -> %s (%s)", method.upper(), endpoint, response.status_code, outcome
        )
        if not response.ok:
            self.logger.info("Response body: %s", response.text)

        return response
