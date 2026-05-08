import json
import traceback
from datetime import date, timedelta, datetime
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

CONFIG = {}
LAST_STATUS = {"generated": False}
OPTIONS_PATH = "/data/options.json"


def load_config():
    global CONFIG
    try:
        with open(OPTIONS_PATH) as f:
            CONFIG = json.load(f)
        print("[INFO] Configuration chargée depuis /data/options.json")
    except FileNotFoundError:
        print(f"[WARN] {OPTIONS_PATH} introuvable, utilisation des valeurs par défaut")
        CONFIG = {
            "mealie_url": "http://localhost:9925",
            "mealie_token": "",
            "openai_api_key": "",
            "openai_model": "gpt-4o",
            "location": "Lausanne, Suisse",
            "default_planning_days": 7,
            "weekday_meals": ["dinner"],
            "weekend_meals": ["lunch", "dinner"],
            "avoid_repeat_days": 14,
        }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    from planner import generate_plan

    body = request.get_json(silent=True) or {}
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    start_date = body.get("start_date", tomorrow)
    planning_days = int(body.get("planning_days", CONFIG.get("default_planning_days", 7)))
    custom_instructions = body.get("custom_instructions", None)

    print(f"[INFO] Génération demandée : {start_date} sur {planning_days} jours")

    try:
        result = generate_plan(CONFIG, start_date, planning_days, custom_instructions)
        result["timestamp"] = datetime.now().isoformat()
        LAST_STATUS.update(result)
        LAST_STATUS["generated"] = True
        LAST_STATUS["error"] = None
        print(f"[INFO] Génération terminée : {result['count']} repas créés")
        return jsonify(result)
    except Exception as e:
        error_msg = str(e)
        tb = traceback.format_exc()
        print(f"[ERROR] Génération échouée : {error_msg}\n{tb}")
        LAST_STATUS.update({
            "generated": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "start_date": start_date,
            "planning_days": planning_days,
        })
        return jsonify({"success": False, "error": error_msg}), 500


@app.route("/api/status")
def status():
    return jsonify(LAST_STATUS)


@app.route("/api/config")
def config_view():
    safe = {k: v for k, v in CONFIG.items() if k not in ("mealie_token", "openai_api_key")}
    return jsonify(safe)


if __name__ == "__main__":
    load_config()
    app.run(host="0.0.0.0", port=8099, debug=False)
