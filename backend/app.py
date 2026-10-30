import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Add Research Agent directory to path so we can import research_agent
RESEARCH_AGENT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Research Agent",
)
sys.path.insert(0, RESEARCH_AGENT_DIR)

# Load environment variables from .env
ENV_PATH = os.path.join(RESEARCH_AGENT_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

from research_agent import research_agent  # noqa: E402

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend calls


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "TRACE Research Agent"})


@app.route("/api/research", methods=["POST"])
def research():
    """Accept a research question and return structured results."""
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    max_results = int(data.get("max_results", 10))

    if not question:
        return jsonify({"error": "Research question is required."}), 400

    try:
        result = research_agent(question, max_results=max_results)
        return jsonify(result), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
