"""Ndërfaqja web (React) + REST API për klasifikimin dhe analitikën e komenteve.

Nisja:  python app.py   ->  http://127.0.0.1:5000
"""
import csv
import io
import threading
import uuid
from pathlib import Path

import pandas as pd
from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from src import assistant, business, config, social
from src.batch import OUTBOX, classify_comments
from src.data import FEEDBACK_PATH, LABELS, ROOT
from src.documents import IMAGE_EXT, extract_comments
from src.predict import SentimentModel
from src.train import train
from src.visualize import REPORTS

config.load_env()

DIST = ROOT / "frontend" / "dist"
SAMPLE_PATH = ROOT / "data" / "biznes_shembull.csv"

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB
app.json.ensure_ascii = False
app.json.sort_keys = False  # ruaj renditjen (p.sh. aspektet sipas numrit të ankesave)

_lock = threading.Lock()
model = SentimentModel()


def _error(message, code=400, **extra):
    return jsonify({"gabim": message, **extra}), code


def _save_export(df: pd.DataFrame, prefix="rezultate") -> str:
    OUTBOX.mkdir(exist_ok=True)
    name = f"{prefix}_{uuid.uuid4().hex[:8]}.csv"
    df.to_csv(OUTBOX / name, index=False, encoding="utf-8-sig")
    return f"/api/download/{name}"


def read_table(filename: str, data: bytes) -> pd.DataFrame:
    """CSV / Excel / JSON / TXT / PDF / imazh -> DataFrame me të paktën kolonën 'koment'."""
    ext = Path(filename).suffix.lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(io.BytesIO(data))
    if ext == ".json":
        return pd.read_json(io.BytesIO(data))
    if ext == ".csv":
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                return pd.read_csv(io.BytesIO(data), sep=None, engine="python", encoding=enc)
            except UnicodeDecodeError:
                continue
    if ext in (".txt", ".pdf", "") or ext in IMAGE_EXT:
        return pd.DataFrame({"koment": extract_comments(filename, data)})
    raise ValueError(f"Formati '{ext}' nuk mbështetet. Përdor CSV, Excel, JSON, TXT ose PDF.")


def _analysis_response(df: pd.DataFrame, source: dict):
    report, export = business.analyze(df, model)
    report["burimi"] = source
    report["shkarko"] = _save_export(export, "analiza")
    return jsonify(report)


# ---------- Faqja ----------
@app.get("/")
def index():
    if (DIST / "index.html").exists():
        return send_from_directory(DIST, "index.html")
    return render_template("index.html")  # ndërfaqja e thjeshtë, nëse React s'është ndërtuar


@app.get("/assets/<path:name>")
def assets(name):
    return send_from_directory(DIST / "assets", name)


@app.get("/reports/<path:name>")
def reports(name):
    return send_from_directory(REPORTS, name)


# ---------- Modeli ----------
@app.get("/api/health")
def health():
    return jsonify({"statusi": "ok", "modeli": model.metrics.get("modeli"),
                    "llm": assistant.llm_available()})


@app.get("/api/model")
def model_info():
    m = model.metrics
    keys = ("modeli", "data", "madhesia_dataset", "train", "test", "cv_f1", "test_accuracy",
            "test_f1", "test_real_accuracy", "test_real_f1", "matrica_konfuzionit",
            "test_real_gabime")
    return jsonify({k: m.get(k) for k in keys})


@app.post("/api/predict")
def predict():
    body = request.get_json(silent=True) or {}
    text = str(body.get("text", "")).strip()
    if not text:
        return _error("Fusha 'text' është e detyrueshme")
    if len(text) > 5000:
        return _error("Teksti është shumë i gjatë (maks. 5000 karaktere)")
    result = model.predict(text)
    result["aspektet"] = business.detect_aspects(text)
    result["asistenti"] = {**assistant.triage(result),
                           **assistant.suggest_reply(text, result["sentimenti"],
                                                     use_llm=bool(body.get("llm")))}
    if body.get("llm"):
        result["llm_sentimenti"] = assistant.llm_sentiment(text)
    return jsonify(result)


@app.post("/api/batch")
def batch():
    file = request.files.get("file")
    if not file or not file.filename:
        return _error("Ngarko një skedar (.txt, .csv, .pdf ose imazh)")
    try:
        comments = extract_comments(file.filename, file.read())
    except Exception as exc:
        return _error(f"Skedari nuk u lexua: {exc}")
    if not comments:
        return _error("Nuk u gjet asnjë koment në skedar")
    df, summary = classify_comments(model, comments[:5000])
    return jsonify({"permbledhje": summary, "shkarko": _save_export(df),
                    "rreshtat": df.head(200).to_dict(orient="records")})


@app.get("/api/download/<path:name>")
def download(name):
    if not name.startswith(("rezultate_", "analiza_", "komente_")) or "/" in name or "\\" in name:
        abort(404)
    return send_from_directory(OUTBOX, name, as_attachment=True)


@app.post("/api/feedback")
def feedback():
    """Përdoruesi korrigjon modelin -> ruhet për ritrajnimin e radhës."""
    body = request.get_json(silent=True) or {}
    text, label = str(body.get("text", "")).strip(), body.get("sentimenti")
    if not text or label not in LABELS:
        return _error(f"Duhen 'text' dhe 'sentimenti' ({' / '.join(LABELS)})")
    new = not FEEDBACK_PATH.exists()
    with _lock, FEEDBACK_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new:
            writer.writerow(["koment", "sentimenti"])
        writer.writerow([text, label])
    return jsonify({"statusi": "u ruajt", "mesazhi": "Faleminderit! Do përdoret në ritrajnim."})


@app.post("/api/retrain")
def retrain():
    global model
    with _lock:
        metrics = train(verbose=False)
        model = SentimentModel()
    return jsonify({"statusi": "u ritrajnua", "modeli": metrics["modeli"],
                    "test_accuracy": metrics["test_accuracy"],
                    "test_real_accuracy": metrics.get("test_real_accuracy")})


# ---------- Analitika e biznesit ----------
@app.post("/api/business/analyze")
def business_analyze():
    file = request.files.get("file")
    try:
        if file and file.filename:
            df = read_table(file.filename, file.read())
            source = {"lloji": "skedar", "emri": file.filename}
        else:
            body = request.get_json(silent=True) or {}
            lines = body.get("komente")
            if isinstance(lines, str):
                lines = lines.splitlines()
            lines = [str(x).strip() for x in (lines or []) if str(x).strip()]
            if not lines:
                return _error("Ngarko një skedar ose ngjit komentet (një për rresht).")
            df = pd.DataFrame({"koment": lines})
            source = {"lloji": "tekst", "emri": "Komente të ngjitura"}
        return _analysis_response(df, source)
    except ValueError as exc:
        return _error(str(exc))
    except Exception as exc:
        return _error(f"Skedari nuk u lexua: {exc}")


@app.get("/api/business/sample")
def business_sample():
    return send_from_directory(SAMPLE_PATH.parent, SAMPLE_PATH.name, as_attachment=True)


@app.post("/api/business/sample")
def business_sample_analyze():
    df = pd.read_csv(SAMPLE_PATH)
    return _analysis_response(df, {"lloji": "shembull", "emri": SAMPLE_PATH.name})


# ---------- Rrjetet sociale ----------
@app.post("/api/social/parse")
def social_parse():
    body = request.get_json(silent=True) or {}
    try:
        info = social.parse_url(body.get("url", ""))
    except social.SocialError as exc:
        return jsonify(exc.to_dict()), exc.status
    return jsonify({**info, "burimet": social.providers_for(info["platforma"])})


@app.post("/api/social/fetch")
def social_fetch():
    body = request.get_json(silent=True) or {}
    try:
        result = social.fetch_comments(body.get("url", ""), body.get("limit", 200), body.get("burimi"))
    except social.SocialError as exc:
        return jsonify(exc.to_dict()), exc.status
    df = pd.DataFrame(result["komente"]).rename(columns={"autori": "klienti"})
    df["platforma"] = result["posti"]["emri"]
    report, export = business.analyze(df, model)
    posti = result["posti"]
    report["burimi"] = {"lloji": "postim", "emri": posti["emri"], "platforma": posti["platforma"],
                        "lloji_postit": posti["lloji"], "url": posti["url"], "lidhja": result["burimi"],
                        "shenim": result.get("shenim")}
    report["shkarko"] = _save_export(export, "komente")
    return jsonify(report)


@app.get("/api/settings")
def settings_get():
    return jsonify(config.status())


@app.post("/api/settings")
def settings_save():
    if request.remote_addr not in ("127.0.0.1", "::1"):  # çelësat ndryshohen vetëm nga ky kompjuter
        return _error("Cilësimet mund të ndryshohen vetëm lokalisht.", 403)
    config.save_env(request.get_json(silent=True) or {})
    return jsonify(config.status())


@app.errorhandler(413)
def too_large(_):
    return _error("Skedari është shumë i madh (maks. 25 MB).", 413)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
