"""Ngarkimi dhe pastrimi i të dhënave reale (CSV)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "komente_raw.csv"
CLEAN_PATH = ROOT / "data" / "komente_clean.csv"
FEEDBACK_PATH = ROOT / "data" / "feedback.csv"

LABELS = ("negativ", "pozitiv")
_LABEL_MAP = {
    "pozitiv": "pozitiv", "pozitive": "pozitiv", "poz": "pozitiv", "positive": "pozitiv",
    "pos": "pozitiv", "1": "pozitiv",
    "negativ": "negativ", "negative": "negativ", "neg": "negativ", "0": "negativ",
}


def normalize_label(value) -> str | None:
    if pd.isna(value):
        return None
    return _LABEL_MAP.get(str(value).strip().lower())


def clean_dataframe(df: pd.DataFrame, text_col="koment", label_col="sentimenti"):
    """Kthen (df_i_pastër, raport) — raporti tregon çfarë u hoq dhe pse."""
    report = {"rreshta_fillestar": len(df)}
    df = df[[text_col, label_col]].rename(columns={text_col: "koment", label_col: "sentimenti"})

    df["koment"] = df["koment"].astype("string").str.strip()
    empty = df["koment"].isna() | (df["koment"].str.len() < 2)
    report["tekst_bosh_ose_shume_i_shkurter"] = int(empty.sum())
    df = df[~empty]

    df["sentimenti"] = df["sentimenti"].map(normalize_label)
    bad_label = df["sentimenti"].isna()
    report["label_mungon_ose_i_panjohur"] = int(bad_label.sum())
    df = df[~bad_label]

    before = len(df)
    df = df.drop_duplicates(subset="koment")
    report["dublikime"] = before - len(df)

    report["rreshta_final"] = len(df)
    report["shperndarja"] = {k: int(v) for k, v in df["sentimenti"].value_counts().items()}
    return df.reset_index(drop=True), report


def load_clean(include_feedback=True) -> pd.DataFrame:
    """Dataseti i pastër + korrigjimet e përdoruesve nga ndërfaqja (nëse ka)."""
    if not CLEAN_PATH.exists():
        df, _ = clean_dataframe(pd.read_csv(RAW_PATH))
        df.to_csv(CLEAN_PATH, index=False, encoding="utf-8")
    df = pd.read_csv(CLEAN_PATH)
    if include_feedback and FEEDBACK_PATH.exists():
        fb, _ = clean_dataframe(pd.read_csv(FEEDBACK_PATH))
        df = pd.concat([df, fb]).drop_duplicates(subset="koment", keep="last")
    return df.reset_index(drop=True)


def main():
    import json
    df, report = clean_dataframe(pd.read_csv(RAW_PATH))
    df.to_csv(CLEAN_PATH, index=False, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Ruajtur: {CLEAN_PATH}")


if __name__ == "__main__":
    main()
