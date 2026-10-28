"""Gjeneron një dataset shembull biznesi: 12 muaj komente për një zinxhir
picerish me dërgesa ("Furra Dielli", biznes fiktiv) në disa qytete.

Të dhënat janë sintetike, por kanë modele të fshehura që analiza duhet t'i gjejë:
  - ankesat për dërgesën rriten në dhjetor-janar dhe janë më të shumta në Durrës
  - një përditësim i aplikacionit në qershor 2026 sjell valë ankesash
  - sushi ka cilësi më të dobët se pica
  - kënaqësia përmirësohet gradualisht në muajt e fundit

Përdorimi:  python data/generate_business.py   ->  data/biznes_shembull.csv
"""
import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from business_phrases import ASPECT_PHRASES, CLOSERS  # noqa: E402

random.seed(7)
OUT = Path(__file__).parent / "biznes_shembull.csv"
START, END = datetime(2025, 11, 1), datetime(2026, 10, 27)

CITIES = {"Tiranë": 0.42, "Durrës": 0.16, "Shkodër": 0.1, "Vlorë": 0.1,
          "Elbasan": 0.08, "Korçë": 0.08, "Fier": 0.06}
PLATFORMS = {"Instagram": 0.3, "Facebook": 0.24, "Google Maps": 0.2, "TikTok": 0.12,
             "Aplikacioni": 0.14}
PRODUCTS = {  # produkti: (kategoria, pesha, ndikimi në sentiment)
    "Pica Margarita": ("Pica", 0.2, 0.0), "Pica Speciale": ("Pica", 0.16, -0.08),
    "Pica Proshuto": ("Pica", 0.12, 0.0), "Burger Klasik": ("Burger", 0.14, 0.02),
    "Sushi Set": ("Sushi", 0.1, 0.16), "Sallatë Cezar": ("Sallata", 0.1, 0.0),
    "Byrek me spinaq": ("Tradicionale", 0.1, -0.05), "Tiramisu": ("Ëmbëlsira", 0.08, -0.06),
}
EMOJI = {"pozitiv": ["😍", "👍", "🔥", "❤️", "👏"], "negativ": ["😡", "👎", "😞", "😤"]}


def pick(weights: dict):
    return random.choices(list(weights), weights=[w if not isinstance(w, tuple) else w[1]
                                                  for w in weights.values()])[0]


def random_date() -> datetime:
    while True:
        d = START + timedelta(seconds=random.randint(0, int((END - START).total_seconds())))
        # Më shumë komente në fundjavë dhe në orët e darkës
        weight = (1.5 if d.weekday() >= 4 else 1.0) * (1.6 if 18 <= d.hour <= 22 else 0.6)
        if random.random() < weight / 2.4:
            return d


def negative_probability(d: datetime, city: str, platform: str, product: str) -> float:
    p = 0.34 + PRODUCTS[product][2]
    months_from_start = (d.year - START.year) * 12 + d.month - START.month
    p -= 0.012 * months_from_start                       # përmirësim gradual
    if d.month in (12, 1):
        p += 0.12                                        # fluksi i festave
    if city == "Durrës":
        p += 0.12
    if d.year == 2026 and d.month == 6 and platform == "Aplikacioni":
        p += 0.35                                        # përditësimi problematik
    if platform == "TikTok":
        p -= 0.08
    if platform == "Google Maps":
        p += 0.06
    return min(max(p, 0.05), 0.9)


def aspect_weights(sentiment, d, city, platform, product):
    w = {"Dërgesa": 3, "Çmimi": 2, "Cilësia": 3, "Stafi": 1.5, "Aplikacioni": 1,
         "Paketimi": 1, "Ambienti": 0.8}
    if sentiment == "negativ":
        if d.month in (12, 1) or city == "Durrës":
            w["Dërgesa"] += 4
        if d.year == 2026 and d.month == 6:
            w["Aplikacioni"] += 6
        if PRODUCTS[product][0] == "Sushi":
            w["Cilësia"] += 4
    if platform == "Aplikacioni":
        w["Aplikacioni"] += 2
    if platform == "Google Maps":
        w["Ambienti"] += 1.5
    return w


def strip_diacritics(text):
    return text.replace("ë", "e").replace("Ë", "E").replace("ç", "c").replace("Ç", "C")


def make_comment(sentiment, aspects, product, platform):
    parts = []
    for a in aspects:
        phrase = random.choice(ASPECT_PHRASES[a][sentiment]).format(p=product.split()[0])
        parts.append(phrase)
    text = ", ".join(parts)
    text = text[0].upper() + text[1:] + "."
    if random.random() < 0.55:
        text += " " + random.choice(CLOSERS[sentiment])
    if platform in ("Instagram", "TikTok") and random.random() < 0.45:
        text += " " + random.choice(EMOJI[sentiment])
    if random.random() < 0.35:
        text = strip_diacritics(text)
    return text


def rating_for(sentiment):
    if random.random() < 0.04:  # zhurmë reale: yjet nuk përputhen me tekstin
        return random.randint(1, 5)
    if sentiment == "pozitiv":
        return random.choices([5, 4, 3], weights=[0.62, 0.32, 0.06])[0]
    return random.choices([1, 2, 3], weights=[0.55, 0.35, 0.10])[0]


def main(n=2600):
    rows = []
    for i in range(n):
        d, city, platform, product = random_date(), pick(CITIES), pick(PLATFORMS), pick(PRODUCTS)
        sentiment = "negativ" if random.random() < negative_probability(d, city, platform, product) \
            else "pozitiv"
        w = aspect_weights(sentiment, d, city, platform, product)
        k = 1 if random.random() < 0.65 else 2
        aspects = list(dict.fromkeys(random.choices(list(w), weights=list(w.values()), k=k)))
        rows.append({
            "data": d.strftime("%Y-%m-%d %H:%M"),
            "platforma": platform,
            "qyteti": city,
            "produkti": product,
            "kategoria": PRODUCTS[product][0],
            "vleresimi": rating_for(sentiment),
            "koment": make_comment(sentiment, aspects, product, platform),
            "klienti": f"K-{random.randint(1000, 1900)}",  # klientë të përsëritur
        })
    rows.sort(key=lambda r: r["data"])
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", *rows[0]])
        writer.writeheader()
        for i, r in enumerate(rows, 1):
            writer.writerow({"id": i, **r})
    print(f"U krijuan {len(rows)} komente biznesi -> {OUT}")


if __name__ == "__main__":
    main()
