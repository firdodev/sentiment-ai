"""Automatizim: klasifikon skedarë me shumë komente, ose monitoron një dosje.

Shembuj:
  python -m src.batch data/komente_test.txt            # një skedar -> outbox/
  python -m src.batch --watch                          # monitoron inbox/ çdo 5 sekonda
"""
import argparse
import json
import shutil
import time
from pathlib import Path

import pandas as pd

from .assistant import triage
from .data import ROOT
from .documents import extract_comments
from .predict import SentimentModel

INBOX, OUTBOX = ROOT / "inbox", ROOT / "outbox"


def classify_comments(model: SentimentModel, comments: list[str]) -> tuple[pd.DataFrame, dict]:
    rows = []
    for r in model.predict_batch(comments):
        t = triage(r)
        rows.append({"koment": r["teksti"], "sentimenti": r["sentimenti"],
                     "besueshmeria": r["besueshmeria"], "i_pasigurt": r["i_pasigurt"],
                     "prioriteti": t["prioriteti"], "veprimi": t["veprimi"]})
    df = pd.DataFrame(rows)
    summary = {
        "gjithsej": len(df),
        "pozitiv": int((df["sentimenti"] == "pozitiv").sum()) if len(df) else 0,
        "negativ": int((df["sentimenti"] == "negativ").sum()) if len(df) else 0,
        "te_pasigurt": int(df["i_pasigurt"].sum()) if len(df) else 0,
    }
    summary["perqindja_pozitive"] = round(100 * summary["pozitiv"] / max(summary["gjithsej"], 1), 1)
    return df, summary


def process_file(model: SentimentModel, path: Path) -> Path:
    comments = extract_comments(path.name, path.read_bytes())
    df, summary = classify_comments(model, comments)
    OUTBOX.mkdir(exist_ok=True)
    out = OUTBOX / f"{path.stem}_rezultate.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")  # -sig: hapet mirë në Excel
    (OUTBOX / f"{path.stem}_permbledhje.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {path.name}: {summary} -> {out.name}")
    return out


def watch(model: SentimentModel, interval=5):
    INBOX.mkdir(exist_ok=True)
    done = INBOX / "perpunuar"
    done.mkdir(exist_ok=True)
    print(f"Duke monitoruar {INBOX} (Ctrl+C për të ndaluar)...")
    while True:
        for path in INBOX.iterdir():
            if path.is_file():
                try:
                    process_file(model, path)
                    shutil.move(str(path), done / path.name)
                except Exception as exc:  # një skedar i dëmtuar s'duhet të ndalë monitorimin
                    print(f"[GABIM] {path.name}: {exc}")
        time.sleep(interval)


def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Klasifikim automatik i komenteve")
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--watch", action="store_true", help="monitoro dosjen inbox/")
    args = parser.parse_args()
    model = SentimentModel()
    if args.watch:
        watch(model)
    for f in args.files:
        process_file(model, f)
    if not args.files and not args.watch:
        parser.print_help()


if __name__ == "__main__":
    main()
