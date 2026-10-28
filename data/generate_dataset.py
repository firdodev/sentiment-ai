"""Gjeneron një dataset me komente në shqip (pozitive / negative).

Dataseti është sintetik, por imiton të dhëna reale: tema të ndryshme,
shkrim pa ë/ç, emoji, gabime, dublikime dhe rreshta të dëmtuar,
që hapi i pastrimit të ketë diçka reale për të rregulluar.

Përdorimi:  python data/generate_dataset.py
"""
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from business_phrases import ASPECT_PHRASES, CLOSERS  # noqa: E402

random.seed(42)
OUT = Path(__file__).parent / "komente_raw.csv"

SUBJECTS = [
    "Produkti", "Shërbimi", "Hoteli", "Restoranti", "Telefoni", "Aplikacioni",
    "Dyqani online", "Porosia", "Kamarieri", "Stafi", "Dërgesa", "Kursi",
    "Filmi", "Libri", "Laptopi", "Kafeneja", "Taksia", "Banka", "Klinika",
    "Palestra", "Pica", "Interneti", "Kompania", "Furra", "Agjencia",
]

POSITIVE = [
    "ishte shumë i mirë", "është i shkëlqyer", "më pëlqeu shumë", "ia vlen çdo lek",
    "funksionon në mënyrë perfekte", "ishte fantastik", "më la shumë të kënaqur",
    "e rekomandoj pa hezitim", "ka cilësi të lartë", "ishte mbi pritshmëritë",
    "erdhi shumë shpejt", "është i besueshëm", "ka çmim të arsyeshëm",
    "ishte i shijshëm", "punon pa asnjë problem", "ishte një eksperiencë e bukur",
    "më bëri shumë të lumtur", "është vërtet i mrekullueshëm", "ishte i pastër dhe i rregullt",
    "e kaloi çdo pritje", "ishte profesional", "ishte super", "është numri një",
    "më zgjidhi problemin menjëherë", "ishte i sjellshëm dhe i dashur",
]
POSITIVE_EXTRA = [
    "Do të kthehem përsëri.", "Faleminderit shumë!", "Bravo!", "Pesë yje.",
    "Do ta blej sërish.", "Ju falënderoj për punën.", "Rekomandim i fortë.",
    "Vazhdoni kështu!", "Jam shumë i kënaqur.", "Gjithçka perfekte.",
    "Nuk kisha asnjë ankesë.", "S'kam asnjë problem me ta.", "Një eksperiencë e paharrueshme.",
]
NEGATIVE = [
    "ishte shumë i keq", "është i dobët", "nuk më pëlqeu fare", "ishte humbje parash",
    "nuk funksionon siç duhet", "ishte i tmerrshëm", "më zhgënjeu shumë",
    "nuk e rekomandoj", "ka cilësi të ulët", "ishte nën çdo pritshmëri",
    "vonoi shumë", "nuk është i besueshëm", "ka çmim shumë të lartë",
    "ishte pa shije", "u prish pas dy ditësh", "ishte një eksperiencë e keqe",
    "më nervozoi shumë", "është katastrofë", "ishte i pistë dhe i çrregullt",
    "nuk ia vlen", "ishte i pasjellshëm", "ishte mashtrim", "bllokohet vazhdimisht",
    "nuk ma zgjidhi problemin", "ishte i ftohtë dhe i vjetër",
]
NEGATIVE_EXTRA = [
    "Nuk do të kthehem më.", "Turp!", "Kurrë më.", "Një yll është shumë.",
    "Nuk do ta blej më kurrë.", "Humbje kohe.", "Mos e provoni.",
    "Jam shumë i zhgënjyer.", "Gjithçka keq.", "Kërkoj rimbursim.",
    "Nuk ishte aspak i mirë.", "S'ka lidhje me përshkrimin.", "Shërbim i pafalshëm.",
]
EMOJI_POS = ["😍", "👍", "😊", "❤️", "🙂", "👏", "🔥"]
EMOJI_NEG = ["😡", "👎", "😞", "😠", "🤬", "😤"]

# Komente të shkurtra "nga jeta reale"
HANDWRITTEN = [
    ("Super, faleminderit!", "pozitiv"), ("Shume i mire", "pozitiv"),
    ("mrekulli fare", "pozitiv"), ("E kam blere 2 here, gjithmone mire", "pozitiv"),
    ("bravo cuna", "pozitiv"), ("ma vlen per ate cmim", "pozitiv"),
    ("Top! 👍👍", "pozitiv"), ("Shpejt dhe sakte", "pozitiv"),
    ("nuk kisha asnje problem, gjithcka ok", "pozitiv"), ("perfekt!!!", "pozitiv"),
    ("Shuuume i kenaqur", "pozitiv"), ("cilesi shume e mire", "pozitiv"),
    ("Kisha frike por doli shume mire", "pozitiv"), ("me pelqen shume", "pozitiv"),
    ("I rekomandoj te gjitheve", "pozitiv"), ("stafi shume i dashur", "pozitiv"),
    ("Keq fare", "negativ"), ("mos e bleni", "negativ"), ("turp t'ju vij", "negativ"),
    ("asnjehere me", "negativ"), ("shume i dobet", "negativ"), ("Mashtrues!!!", "negativ"),
    ("leket hedhur ne ere", "negativ"), ("s'me pelqeu aspak", "negativ"),
    ("prita 2 ore dhe askush nuk erdhi", "negativ"), ("e keqe e keqe e keqe", "negativ"),
    ("nuk punon fare 😡", "negativ"), ("cilesi shume e dobet", "negativ"),
    ("zhgenjim total", "negativ"), ("u prish menjehere", "negativ"),
    ("Nuk ia vlen fare", "negativ"), ("stafi i pasjellshem", "negativ"),
]


def strip_diacritics(text: str) -> str:
    """Imiton përdoruesit që shkruajnë pa ë dhe ç."""
    return text.replace("ë", "e").replace("Ë", "E").replace("ç", "c").replace("Ç", "C")


def make_comment(phrases, extras, emojis):
    parts = [f"{random.choice(SUBJECTS)} {random.choice(phrases)}."]
    if random.random() < 0.6:
        parts.append(random.choice(extras))
    text = " ".join(parts)
    if random.random() < 0.3:
        text += " " + random.choice(emojis)
    if random.random() < 0.4:
        text = strip_diacritics(text)
    if random.random() < 0.2:
        text = text.lower()
    return text


def make_business_comment(label: str) -> str:
    """Koment me fjalor biznesi (dërgesa, çmimi, aplikacioni...)."""
    aspect = random.choice(list(ASPECT_PHRASES))
    text = random.choice(ASPECT_PHRASES[aspect][label]).format(p=random.choice(SUBJECTS))
    text = text[0].upper() + text[1:] + "."
    if random.random() < 0.5:
        text += " " + random.choice(CLOSERS[label])
    if random.random() < 0.4:
        text = strip_diacritics(text)
    return text


def main(n_per_class: int = 600, n_business_per_class: int = 300):
    rows = []
    for _ in range(n_per_class):
        rows.append((make_comment(POSITIVE, POSITIVE_EXTRA, EMOJI_POS), "pozitiv"))
        rows.append((make_comment(NEGATIVE, NEGATIVE_EXTRA, EMOJI_NEG), "negativ"))
    for _ in range(n_business_per_class):
        rows.append((make_business_comment("pozitiv"), "pozitiv"))
        rows.append((make_business_comment("negativ"), "negativ"))
    rows += HANDWRITTEN * 2

    # Zhurmë reale: label të shkruar ndryshe, rreshta bosh, URL, dublikime
    noisy = [
        ("   Shërbim i shkëlqyer, faleminderit!   ", "Pozitiv"),
        ("Produkt i keq, mos e blini http://shembull.com", "NEGATIV"),
        ("", "pozitiv"), ("   ", "negativ"), ("Ok", ""), ("Komenti pa label", None),
        ("Very good product", "positive"), ("Terrible service", "negative"),
        ("Shume mire!!!", "1"), ("Shume keq!!!", "0"),
    ]
    rows += noisy + random.sample(rows, 40)  # 40 dublikime
    random.shuffle(rows)

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "koment", "sentimenti"])
        for i, (text, label) in enumerate(rows, 1):
            writer.writerow([i, text, label if label is not None else ""])
    print(f"U krijuan {len(rows)} rreshta -> {OUT}")


if __name__ == "__main__":
    main()
