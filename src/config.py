"""Lexon dhe ruan çelësat e API-ve në skedarin .env (vetëm lokalisht, kurrë në frontend)."""
import os
import re

from .data import ROOT

ENV_PATH = ROOT / ".env"
ALLOWED_KEYS = {
    "APIFY_TOKEN": "Apify (Instagram, Facebook, TikTok, LinkedIn)",
    "META_ACCESS_TOKEN": "Meta Graph API (faqja/llogaria juaj)",
    "FB_PAGE_ID": "ID e faqes Facebook",
    "IG_USER_ID": "ID e llogarisë Instagram Business",
    "OLLAMA_MODEL": "Modeli LLM lokal (Ollama)",
}
_LINE = re.compile(r"^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$")


def load_env():
    """Ngarkon .env në os.environ pa mbishkruar variablat ekzistuese."""
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        m = _LINE.match(line)
        if m and not line.lstrip().startswith("#"):
            os.environ.setdefault(m.group(1), m.group(2).strip('"').strip("'"))


def save_env(values: dict):
    """Ruan vetëm çelësat e lejuar; një vlerë bosh e fshin çelësin."""
    current = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            m = _LINE.match(line)
            if m:
                current[m.group(1)] = m.group(2)
    for key, value in values.items():
        if key not in ALLOWED_KEYS:
            continue
        value = str(value or "").strip()
        if value:
            current[key] = value
            os.environ[key] = value
        else:
            current.pop(key, None)
            os.environ.pop(key, None)
    ENV_PATH.write_text("".join(f"{k}={v}\n" for k, v in current.items()), encoding="utf-8")


def status() -> dict:
    """Cilët çelësa janë vendosur (pa i zbuluar vlerat)."""
    return {k: {"pershkrimi": d, "vendosur": bool(os.environ.get(k))} for k, d in ALLOWED_KEYS.items()}
