"""Analitika biznesi nga komentet e klientëve.

Merr një tabelë me komente (dhe opsionalisht datë, platformë, produkt, qytet,
vlerësim, klient) dhe kthen gjithçka që i duhet një pronari biznesi:
KPI, tendenca në kohë, aspektet që shkaktojnë ankesa, krahasime sipas
dimensioneve, klientë në rrezik, komente urgjente, insight-e dhe rekomandime.
"""
import math
from collections import Counter

import numpy as np
import pandas as pd

from .preprocess import normalize, tokenize

COLUMN_ALIASES = {
    "koment": ["koment", "komenti", "komente", "comment", "comments", "text", "teksti", "review",
               "recensioni", "message", "mesazhi", "commentary", "pershkrimi", "feedback"],
    "data": ["data", "date", "datetime", "koha", "timestamp", "created", "createdat", "created_at",
             "createtimeiso", "time", "dita"],
    "platforma": ["platforma", "platform", "burimi", "source", "kanali", "channel", "rrjeti"],
    "produkti": ["produkti", "product", "artikulli", "item", "sherbimi", "service", "menuja"],
    "kategoria": ["kategoria", "category", "grupi", "lloji", "type"],
    "qyteti": ["qyteti", "city", "lokacioni", "location", "dega", "branch", "zona", "region"],
    "vleresimi": ["vleresimi", "rating", "yje", "yjet", "stars", "nota", "score", "piket"],
    "klienti": ["klienti", "customer", "user", "username", "perdoruesi", "author", "autori",
                "emri", "name", "client"],
}
DIMENSIONS = {"platforma": "Platforma", "produkti": "Produkti", "kategoria": "Kategoria",
              "qyteti": "Qyteti"}

# Prefikse të normalizuara (pa ë/ç); "$" në fund = përputhje e saktë e fjalës
ASPECTS = {
    "Dërgesa": ["derges", "dorezim", "korrier", "postier", "vono", "vones", "mberrit", "adres",
                "orar", "prita", "pritje", "delivery", "sollen", "erdhi$"],
    "Çmimi": ["cmim", "shtrenjt", "lire$", "lek$", "leke$", "para$", "parate", "vlen$", "ofert",
              "zbritj", "fatur", "price", "kosto", "rimburs"],
    "Cilësia": ["cilesi", "shij", "fresk", "porcion", "djegur", "perberes", "ushqim", "kualitet",
                "quality", "prish", "defekt", "thyer", "brum"],
    "Stafi": ["staf", "kamarier", "operator", "shites", "sjellshem", "pasjellshem", "vrazhd",
              "sherbim", "ekip", "injor", "ankes", "suport", "ndihmo"],
    "Aplikacioni": ["aplikacion", "app$", "online", "llogari", "pages", "kart", "perditesim",
                    "bllok", "anulo", "faqj", "website"],
    "Paketimi": ["paket", "kuti", "salc", "derdh", "qese", "ambalazh"],
    "Ambienti": ["ambient", "pist", "paster", "lokal", "tavolin", "qime", "atmosfer", "zhurm",
                 "higjien"],
}
RECOMMENDATIONS = {
    "Dërgesa": "Shto korrierë në orët e pikut, njofto klientin për vonesat dhe kontrollo zonat me më shumë ankesa.",
    "Çmimi": "Rishiko raportin çmim/sasi dhe ofro paketa ose oferta për klientët e rregullt.",
    "Cilësia": "Kontrollo standardet e kuzhinës dhe recetat e produkteve me kënaqësi të ulët.",
    "Stafi": "Trajnim për komunikimin me klientin dhe afat maksimal përgjigjeje për çdo ankesë.",
    "Aplikacioni": "Testo pagesat dhe hyrjen në llogari pas çdo përditësimi dhe monitoro gabimet.",
    "Paketimi": "Përdor kuti më të forta dhe mbyllje të sigurta për salcat dhe pijet.",
    "Ambienti": "Rrit kontrollin e higjienës dhe pastrimin e tavolinave gjatë ditës.",
}
ASPECT_ACC = {"Dërgesa": "dërgesën", "Çmimi": "çmimin", "Cilësia": "cilësinë", "Stafi": "stafin",
              "Aplikacioni": "aplikacionin", "Paketimi": "paketimin", "Ambienti": "ambientin"}
DIM_BEST = {"platforma": "Platforma më e pëlqyer", "produkti": "Produkti më i pëlqyer",
            "kategoria": "Kategoria më e pëlqyer", "qyteti": "Qyteti më i kënaqur"}
# Fjalë që e bëjnë një ankesë urgjente pavarësisht datës
SEVERE = ["rimburs", "turp", "mashtr", "qime", "helm", "avokat", "polic", "padi", "semur",
          "alergj", "paturp"]
MONTHS = ["Jan", "Shk", "Mar", "Pri", "Maj", "Qer", "Kor", "Gus", "Sht", "Tet", "Nën", "Dhj"]
WEEKDAYS = ["E hënë", "E martë", "E mërkurë", "E enjte", "E premte", "E shtunë", "E diel"]
KEYWORD_STOP = {"porosi", "porosia", "porosine", "porosis", "shume", "gjithe", "per", "pas",
                "emojipoz", "emojineg", "kete", "keto", "atij", "nje", "dhe"}


# ---------- Ndihmës ----------
def _pct(part, whole) -> float:
    return round(100 * float(part) / float(whole), 1) if whole else 0.0


def _num(x):
    """Konverton vlerat numpy/NaN në tipe JSON."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return None if np.isnan(x) else round(float(x), 2)
    return x


def _key(name: str) -> str:
    return normalize(name).replace(" ", "").replace("_", "")


def detect_columns(columns) -> dict:
    """Gjen cila kolonë i përgjigjet çdo roli, pavarësisht emrit (shqip/anglisht)."""
    found = {}
    keys = {c: _key(str(c)) for c in columns}
    for role, aliases in COLUMN_ALIASES.items():
        alias_keys = [a.replace("_", "") for a in aliases]
        for col, k in keys.items():
            if col not in found.values() and k in alias_keys:
                found[role] = col
                break
    return found


def _matches(tokens: list[str], keywords: list[str]) -> bool:
    for kw in keywords:
        if kw.endswith("$"):
            if kw[:-1] in tokens:
                return True
        elif any(t.startswith(kw) for t in tokens):
            return True
    return False


def detect_aspects(text: str) -> list[str]:
    # "para se" = "përpara", jo para si monedhë
    tokens = normalize(text).replace("para se", "parase").split()
    return [name for name, kws in ASPECTS.items() if _matches(tokens, kws)]


def _parse_dates(series: pd.Series) -> pd.Series:
    d = pd.to_datetime(series, errors="coerce", utc=True, format="mixed")
    if d.isna().mean() > 0.5:
        d = pd.to_datetime(series, errors="coerce", utc=True, dayfirst=True, format="mixed")
    return d.dt.tz_convert(None)


def _period_label(ts: pd.Timestamp, freq: str) -> str:
    if freq == "M":
        return f"{MONTHS[ts.month - 1]} {ts.year}"
    return f"{ts.day} {MONTHS[ts.month - 1]}"


# ---------- Analiza ----------
def prepare(df_raw: pd.DataFrame, model, max_rows=20000) -> tuple[pd.DataFrame, dict]:
    cols = detect_columns(df_raw.columns)
    if "koment" not in cols:
        raise ValueError("Nuk u gjet kolona e komenteve. Emërto njërën kolonë 'koment' "
                         f"(kolonat e gjetura: {', '.join(map(str, df_raw.columns))}).")
    df = pd.DataFrame({role: df_raw[col] for role, col in cols.items()})
    df["koment"] = df["koment"].astype("string").str.strip()
    df = df[df["koment"].notna() & (df["koment"].str.len() >= 2)].head(max_rows).copy()
    df["koment"] = df["koment"].astype(str)

    preds = model.predict_batch(df["koment"].tolist())
    df["sentimenti"] = [p["sentimenti"] for p in preds]
    df["besueshmeria"] = [p["besueshmeria"] for p in preds]
    df["i_pasigurt"] = [p["i_pasigurt"] for p in preds]
    df["aspektet"] = [detect_aspects(t) for t in df["koment"]]

    if "data" in df:
        df["data"] = _parse_dates(df["data"])
        if df["data"].isna().all():
            df = df.drop(columns="data")
    if "vleresimi" in df:
        r = pd.to_numeric(df["vleresimi"], errors="coerce")
        if r.notna().any():
            df["vleresimi"] = r * 5 / 10 if r.max() > 5 else r  # shkallë 1-10 -> 1-5
        else:
            df = df.drop(columns="vleresimi")
    for dim in DIMENSIONS:
        if dim in df:
            df[dim] = df[dim].astype("string").str.strip().fillna("Pa specifikuar").astype(str)
    if "klienti" in df:
        df["klienti"] = df["klienti"].astype("string").str.strip()

    # Urgjente = negative e sigurt + (e fundit, 14 ditë) ose me fjalë të rënda (rimbursim, turp...)
    strong_neg = (df["sentimenti"] == "negativ") & (df["besueshmeria"] >= 0.85)
    severe = df["koment"].apply(lambda t: _matches(normalize(t).split(), SEVERE))
    recent = (df["data"] >= df["data"].max() - pd.Timedelta(days=14)) if "data" in df else False
    df["urgjent"] = strong_neg & (severe | recent)
    df["prioriteti"] = np.where(
        df["urgjent"], "urgjent",
        np.where(strong_neg, "i lartë",
                 np.where((df["sentimenti"] == "negativ") | df["i_pasigurt"], "mesatar", "i ulët")))
    return df.reset_index(drop=True), cols


def _kpis(df, known):
    total, pos = len(known), int((known["sentimenti"] == "pozitiv").sum())
    neg = total - pos
    k = {
        "gjithsej": len(df), "te_klasifikuara": total, "pozitiv": pos, "negativ": neg,
        "perqindja_pozitive": _pct(pos, total), "perqindja_negative": _pct(neg, total),
        "neto_sentimenti": round(_pct(pos, total) - _pct(neg, total), 1),
        "besueshmeria_mesatare": round(float(known["besueshmeria"].mean()) * 100, 1) if total else 0,
        "te_pasigurt": int(df["i_pasigurt"].sum()),
        "urgjente": int(df["urgjent"].sum()),
    }
    if "vleresimi" in df:
        k["vleresimi_mesatar"] = _num(df["vleresimi"].mean())
    if "data" in df:
        end = df["data"].max()
        cur = known[known["data"] > end - pd.Timedelta(days=30)]
        prev = known[(known["data"] <= end - pd.Timedelta(days=30)) &
                     (known["data"] > end - pd.Timedelta(days=60))]
        if len(cur) >= 5 and len(prev) >= 5:
            cur_p = _pct((cur["sentimenti"] == "pozitiv").sum(), len(cur))
            prev_p = _pct((prev["sentimenti"] == "pozitiv").sum(), len(prev))
            k["krahasimi_30_dite"] = {
                "perqindja_pozitive": cur_p, "me_pare": prev_p,
                "ndryshimi_pp": round(cur_p - prev_p, 1),
                "volumi": len(cur), "volumi_me_pare": len(prev),
                "ndryshimi_volumit": _pct(len(cur) - len(prev), len(prev)),
            }
    return k


def _timeline(known):
    span = (known["data"].max() - known["data"].min()).days
    freq = "M" if span > 120 else "W" if span > 21 else "D"
    rule = {"M": "MS", "W": "W-MON", "D": "D"}[freq]
    g = known.set_index("data").groupby([pd.Grouper(freq=rule), "sentimenti"]).size().unstack(fill_value=0)
    for col in ("pozitiv", "negativ"):
        if col not in g:
            g[col] = 0
    out = []
    for ts, row in g.iterrows():
        total = int(row["pozitiv"] + row["negativ"])
        out.append({"periudha": ts.strftime("%Y-%m-%d"), "etiketa": _period_label(ts, freq),
                    "pozitiv": int(row["pozitiv"]), "negativ": int(row["negativ"]),
                    "gjithsej": total, "perqindja_pozitive": _pct(row["pozitiv"], total)})
    return freq, rule, out, g.index


def _dimension(known, dim, limit=15):
    g = known.groupby(dim)
    rows = []
    for name, part in g:
        pos = int((part["sentimenti"] == "pozitiv").sum())
        item = {"emri": str(name), "gjithsej": len(part), "pozitiv": pos, "negativ": len(part) - pos,
                "perqindja_pozitive": _pct(pos, len(part))}
        if "vleresimi" in part:
            item["vleresimi_mesatar"] = _num(part["vleresimi"].mean())
        neg_aspects = Counter(a for asp in part.loc[part["sentimenti"] == "negativ", "aspektet"] for a in asp)
        item["ankesa_kryesore"] = neg_aspects.most_common(1)[0][0] if neg_aspects else None
        rows.append(item)
    rows.sort(key=lambda r: r["gjithsej"], reverse=True)
    return rows[:limit]


def _aspects(known):
    total_neg = int((known["sentimenti"] == "negativ").sum())
    rows = []
    for name in ASPECTS:
        mask = known["aspektet"].apply(lambda a, n=name: n in a)
        part = known[mask]
        if not len(part):
            continue
        neg = int((part["sentimenti"] == "negativ").sum())
        rows.append({"aspekti": name, "permendje": len(part), "pozitiv": len(part) - neg,
                     "negativ": neg, "perqindja_negative": _pct(neg, len(part)),
                     "pjesa_e_ankesave": _pct(neg, total_neg)})
    rows.sort(key=lambda r: r["negativ"], reverse=True)
    return rows


def _aspect_timeline(known, rule, freq, periods, aspects):
    neg = known[known["sentimenti"] == "negativ"]
    out = {}
    for a in aspects:
        s = neg[neg["aspektet"].apply(lambda x, n=a: n in x)].set_index("data").resample(rule).size()
        s = s.reindex(periods, fill_value=0)
        out[a] = [{"periudha": ts.strftime("%Y-%m-%d"), "etiketa": _period_label(ts, freq),
                   "ankesa": int(v)} for ts, v in s.items()]
    return out


def _keywords(known, top=12):
    counts = {"pozitiv": Counter(), "negativ": Counter()}
    for text, label in zip(known["koment"], known["sentimenti"]):
        counts[label].update({t for t in tokenize(text)
                              if len(t) >= 3 and t not in KEYWORD_STOP and not t[0].isdigit()})
    n_pos, n_neg = sum(counts["pozitiv"].values()) or 1, sum(counts["negativ"].values()) or 1
    vocab = set(counts["pozitiv"]) | set(counts["negativ"])
    v = len(vocab) or 1
    scored = []
    for w in vocab:
        p, n = counts["pozitiv"][w], counts["negativ"][w]
        if p + n < 3:
            continue
        score = math.log((n + 1) / (n_neg + v)) - math.log((p + 1) / (n_pos + v))  # log-odds
        scored.append((w, score, p, n))
    # Renditje: sa shpesh × sa dallues (log-odds e ponderuar)
    neg = sorted((s for s in scored if s[1] > 0.5), key=lambda s: s[3] * s[1], reverse=True)[:top]
    pos = sorted((s for s in scored if s[1] < -0.5), key=lambda s: s[2] * -s[1], reverse=True)[:top]
    fmt = lambda w: w.replace("_", " ")  # noqa: E731
    return {"pozitive": [{"fjala": fmt(w), "numri": p} for w, _, p, _ in pos],
            "negative": [{"fjala": fmt(w), "numri": n} for w, _, _, n in neg]}


def _row(r, extra=()):
    item = {"koment": r["koment"], "sentimenti": r["sentimenti"],
            "besueshmeria": _num(r["besueshmeria"]), "aspektet": r["aspektet"]}
    for c in ("data", "platforma", "produkti", "qyteti", "vleresimi", "klienti", *extra):
        if c in r and not pd.isna(r[c]):
            item[c] = r[c].strftime("%Y-%m-%d %H:%M") if isinstance(r[c], pd.Timestamp) else _num(r[c])
    return item


def _insights(df, known, k, dims, aspects, aspect_tl, timeline):
    out = []
    p = k["perqindja_pozitive"]
    level = "good" if p >= 75 else "warning" if p >= 55 else "critical"
    out.append({"lloji": level, "titulli": f"{p}% e komenteve janë pozitive",
                "teksti": f"{k['pozitiv']} pozitive dhe {k['negativ']} negative nga {k['te_klasifikuara']} komente."})

    if timeline and len(timeline) >= 6:
        first, last = timeline[:3], timeline[-3:]
        a = _pct(sum(t["pozitiv"] for t in first), sum(t["gjithsej"] for t in first))
        b = _pct(sum(t["pozitiv"] for t in last), sum(t["gjithsej"] for t in last))
        if abs(b - a) >= 4:
            out.append({"lloji": "good" if b > a else "critical",
                        "titulli": f"Tendenca afatgjatë: kënaqësia {'u rrit' if b > a else 'ra'} {abs(b - a):.1f} pikë",
                        "teksti": f"Nga {a}% ({first[0]['etiketa']} - {first[-1]['etiketa']}) "
                                  f"në {b}% ({last[0]['etiketa']} - {last[-1]['etiketa']})."})

    if "krahasimi_30_dite" in k:
        c = k["krahasimi_30_dite"]
        d = c["ndryshimi_pp"]
        if abs(d) >= 3:
            out.append({"lloji": "good" if d > 0 else "critical",
                        "titulli": f"Kënaqësia {'u rrit' if d > 0 else 'ra'} {abs(d)} pikë në 30 ditët e fundit",
                        "teksti": f"Nga {c['me_pare']}% në {c['perqindja_pozitive']}% ({c['volumi']} komente)."})
        else:
            out.append({"lloji": "info", "titulli": "Kënaqësia është e qëndrueshme në 30 ditët e fundit",
                        "teksti": f"{c['perqindja_pozitive']}% pozitive, ndryshim {d:+} pikë."})

    if aspects and aspects[0]["negativ"]:
        a = aspects[0]
        out.append({"lloji": "critical" if a["pjesa_e_ankesave"] >= 30 else "warning",
                    "titulli": f"{a['aspekti']} është burimi kryesor i ankesave",
                    "teksti": f"Përmendet në {a['pjesa_e_ankesave']}% të komenteve negative ({a['negativ']} ankesa)."})

    min_volume = max(15, int(0.04 * len(known)))
    mentioned = set()
    for dim, rows in dims.items():
        big = [r for r in rows if r["gjithsej"] >= min_volume]
        if len(big) < 2 or (dim == "kategoria" and "produkti" in dims):  # shmang përsëritjen
            continue
        worst, best = min(big, key=lambda r: r["perqindja_pozitive"]), max(big, key=lambda r: r["perqindja_pozitive"])
        if worst["perqindja_pozitive"] <= p - 8 and worst["emri"] not in mentioned:
            mentioned.add(worst["emri"])
            reason = (f", kryesisht për {ASPECT_ACC[worst['ankesa_kryesore']]}"
                      if worst["ankesa_kryesore"] else "")
            out.append({"lloji": "warning",
                        "titulli": f"{DIMENSIONS[dim]} me kënaqësinë më të ulët: {worst['emri']}",
                        "teksti": f"{worst['perqindja_pozitive']}% pozitive kundrejt mesatares {p}%{reason}."})
        if (dim in ("produkti", "platforma") and best["perqindja_pozitive"] >= p + 5
                and best["emri"] not in mentioned):
            mentioned.add(best["emri"])
            out.append({"lloji": "good", "titulli": f"{DIM_BEST[dim]}: {best['emri']}",
                        "teksti": f"{best['perqindja_pozitive']}% pozitive nga {best['gjithsej']} komente."})

    for name, series in aspect_tl.items():
        values = [s["ankesa"] for s in series]
        if len(values) >= 4:
            peak = max(range(len(values)), key=values.__getitem__)
            median = float(np.median(values)) or 1
            if values[peak] >= 2.2 * median and values[peak] >= 8:
                out.append({"lloji": "warning",
                            "titulli": f"Valë ankesash për {ASPECT_ACC[name]} në {series[peak]['etiketa']}",
                            "teksti": f"{values[peak]} ankesa, {values[peak] / median:.1f} herë më shumë se zakonisht."})

    if k["urgjente"]:
        n = k["urgjente"]
        out.append({"lloji": "critical", "titulli": f"{n} {'koment kërkon' if n == 1 else 'komente kërkojnë'} përgjigje urgjente",
                    "teksti": "Ankesa të fundit ose të rënda (rimbursim, higjienë, \"turp\"). Shiko listën më poshtë."})
    if "vleresimi" in df:
        mism = df[((df["vleresimi"] >= 4) & (df["sentimenti"] == "negativ")) |
                  ((df["vleresimi"] <= 2) & (df["sentimenti"] == "pozitiv"))]
        if len(mism):
            out.append({"lloji": "info", "titulli": f"{len(mism)} komente ku yjet nuk përputhen me tekstin",
                        "teksti": "P.sh. 5 yje me tekst negativ. Ia vlen t'i lexosh manualisht."})
    return out


def _summary(k, aspects, insights) -> str:
    parts = [f"Nga {k['te_klasifikuara']} komente, {k['perqindja_pozitive']}% janë pozitive "
             f"(neto sentimenti {k['neto_sentimenti']:+})."]
    if "krahasimi_30_dite" in k:
        d = k["krahasimi_30_dite"]["ndryshimi_pp"]
        parts.append(f"Në 30 ditët e fundit kënaqësia ndryshoi {d:+} pikë.")
    top = [ASPECT_ACC[a["aspekti"]] for a in aspects[:2] if a["negativ"]]
    if top:
        parts.append(f"Ankesat kryesore lidhen me {' dhe '.join(top)}.")
    if k["urgjente"]:
        parts.append(f"{k['urgjente']} komente kërkojnë vëmendje të menjëhershme.")
    return " ".join(parts)


def analyze(df_raw: pd.DataFrame, model, max_rows=20000) -> tuple[dict, pd.DataFrame]:
    df, cols = prepare(df_raw, model, max_rows)
    if df.empty:
        raise ValueError("Skedari nuk ka asnjë koment të vlefshëm.")
    known = df[df["sentimenti"] != "i panjohur"]
    k = _kpis(df, known)
    report = {"kolonat": {role: str(col) for role, col in cols.items()}, "kpi": k}

    if "data" in df and known["data"].notna().any():
        dated = known.dropna(subset=["data"])
        report["periudha"] = {"nga": dated["data"].min().strftime("%Y-%m-%d"),
                              "deri": dated["data"].max().strftime("%Y-%m-%d")}
        freq, rule, tl, periods = _timeline(dated)
        report["granulariteti"] = {"M": "muaj", "W": "javë", "D": "ditë"}[freq]
        report["tendenca"] = tl
        wd = dated.groupby(dated["data"].dt.day_of_week)
        report["ditet_e_javes"] = [
            {"dita": WEEKDAYS[i], "gjithsej": len(part),
             "perqindja_pozitive": _pct((part["sentimenti"] == "pozitiv").sum(), len(part))}
            for i, part in wd]
        if dated["data"].dt.hour.nunique() > 1:
            hours = dated["data"].dt.hour.value_counts().reindex(range(24), fill_value=0)
            report["oret"] = [{"ora": f"{h:02d}", "gjithsej": int(v)} for h, v in hours.items()]
    else:
        dated, rule, freq, periods = None, None, None, None

    dims = {d: _dimension(known, d) for d in DIMENSIONS if d in known}
    report["dimensionet"] = {d: {"titulli": DIMENSIONS[d], "rreshtat": rows} for d, rows in dims.items()}
    aspects = _aspects(known)
    report["aspektet"] = aspects
    top_neg = [a["aspekti"] for a in aspects[:3] if a["negativ"]]
    all_neg = [a["aspekti"] for a in aspects if a["negativ"]]
    aspect_tl = (_aspect_timeline(dated, rule, freq, periods, all_neg)
                 if dated is not None and all_neg else {})
    report["aspektet_ne_kohe"] = {a: aspect_tl[a] for a in top_neg if a in aspect_tl}
    report["fjalet"] = _keywords(known)

    if "vleresimi" in df:
        dist = df["vleresimi"].round().value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
        report["vleresimet"] = [{"yje": int(s), "numri": int(n)} for s, n in dist.items()]

    if "klienti" in known and known["klienti"].notna().any():
        c = known.dropna(subset=["klienti"]).groupby("klienti")["sentimenti"]
        stats = pd.DataFrame({"gjithsej": c.size(), "negativ": c.apply(lambda s: (s == "negativ").sum())})
        risk = stats[stats["negativ"] >= 2].sort_values(["negativ", "gjithsej"], ascending=False)
        report["klientet"] = {
            "unik": int(len(stats)), "te_perseritur": int((stats["gjithsej"] >= 2).sum()),
            "ne_rrezik": [{"klienti": str(i), "negativ": int(r["negativ"]), "gjithsej": int(r["gjithsej"])}
                          for i, r in risk.head(8).iterrows()],
            "numri_ne_rrezik": int(len(risk)),
        }

    urgent = df[df["urgjent"]]
    urgent = urgent.sort_values(["data", "besueshmeria"] if "data" in urgent else ["besueshmeria"],
                                ascending=False)
    report["urgjente"] = [_row(r) for _, r in urgent.head(12).iterrows()]
    pos = known[known["sentimenti"] == "pozitiv"]
    pos = pos.assign(_len=pos["koment"].str.len()).sort_values(["besueshmeria", "_len"], ascending=False)
    report["deshmi"] = [_row(r) for _, r in pos[pos["_len"] >= 30].head(6).iterrows()]

    report["insights"] = _insights(df, known, k, dims, aspects, aspect_tl, report.get("tendenca"))
    report["rekomandime"] = [{"aspekti": a, "teksti": RECOMMENDATIONS[a]} for a in top_neg]
    report["permbledhja"] = _summary(k, aspects, report["insights"])
    latest = df.sort_values("data", ascending=False, na_position="last") if "data" in df else df
    report["rreshtat"] = [_row(r, ("prioriteti",)) for _, r in latest.head(3000).iterrows()]

    export = df.drop(columns="urgjent")
    export["aspektet"] = export["aspektet"].apply(", ".join)
    return report, export
