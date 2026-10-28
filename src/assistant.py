"""Asistent inteligjent: prioritet, veprim dhe përgjigje e sugjeruar për çdo koment.

Nëse Ollama (LLM open-source lokal, p.sh. llama3.2) është në punë, përdoret
për përgjigje gjeneruese dhe për një "mendim të dytë" mbi sentimentin.
Përndryshe asistenti punon me rregulla dhe shabllone — pa varësi nga interneti.
"""
import json
import os
import random
import urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

REPLIES = {
    "pozitiv": [
        "Faleminderit shumë për fjalët e mira! Na gëzon që ishit të kënaqur.",
        "Ju falënderojmë për vlerësimin! Shpresojmë t'ju shohim përsëri së shpejti.",
        "Sa mirë të dëgjojmë këtë! Komenti juaj i jep zemër gjithë ekipit.",
    ],
    "negativ": [
        "Na vjen shumë keq për përvojën tuaj. Na shkruani në privat që ta zgjidhim menjëherë.",
        "Kërkojmë ndjesë për shqetësimin. Ekipi ynë do t'ju kontaktojë sa më shpejt.",
        "Faleminderit që na e thatë. Do ta shqyrtojmë problemin dhe do t'ju kthejmë përgjigje.",
    ],
}


def triage(result: dict) -> dict:
    """Vendos prioritetin dhe veprimin automatik bazuar në rezultatin e modelit."""
    s, conf = result["sentimenti"], result["besueshmeria"]
    if result.get("i_pasigurt"):
        return {"prioriteti": "mesatar", "veprimi": "Rishiko manualisht – modeli nuk është i sigurt"}
    if s == "negativ":
        level = "i lartë" if conf >= 0.85 else "mesatar"
        return {"prioriteti": level, "veprimi": "Dërgo te ekipi i suportit"}
    return {"prioriteti": "i ulët", "veprimi": "Falënderoje klientin / publiko si testimonial"}


def _ollama(prompt: str, timeout=30) -> str | None:
    body = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())["response"].strip()
    except Exception:
        return None


def llm_available() -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=1):
            return True
    except Exception:
        return False


def llm_sentiment(text: str) -> str | None:
    """Klasifikim zero-shot me LLM, për krahasim me modelin tonë."""
    answer = _ollama(
        "Klasifiko sentimentin e këtij komenti në shqip. "
        f"Përgjigju VETËM me një fjalë: pozitiv ose negativ.\n\nKomenti: {text}")
    if not answer:
        return None
    answer = answer.lower()
    return "negativ" if "negativ" in answer else "pozitiv" if "pozitiv" in answer else None


def suggest_reply(text: str, sentiment: str, use_llm=True) -> dict:
    if use_llm and sentiment in REPLIES and llm_available():
        reply = _ollama(
            "Je asistent i shërbimit ndaj klientit. Shkruaj një përgjigje të shkurtër "
            f"(1-2 fjali), të sjellshme, në shqip, për këtë koment {sentiment}:\n\n{text}")
        if reply:
            return {"pergjigja": reply, "burimi": f"LLM ({OLLAMA_MODEL})"}
    options = REPLIES.get(sentiment, ["Faleminderit për komentin tuaj!"])
    return {"pergjigja": random.choice(options), "burimi": "shabllon"}
