"""Pastrimi dhe normalizimi i tekstit shqip para trajnimit."""
import re
import unicodedata

POS_EMOJI = "😍😊👍❤🙂😀😃😄👏🔥💯🥰⭐"
NEG_EMOJI = "😡👎😞😠🤬😤💩😢😭🙁☹"

# Fjalë shumë të shpeshta që nuk mbartin sentiment (pa ë/ç, pas normalizimit)
STOPWORDS = {
    "dhe", "e", "te", "i", "per", "me", "ne", "nga", "se", "qe", "u", "do", "ka",
    "kam", "kemi", "keni", "kane", "eshte", "ishte", "ishin", "jane", "jam", "je",
    "nje", "kjo", "ky", "keto", "kete", "ai", "ajo", "ata", "ato", "une", "ti",
    "si", "por", "edhe", "tek", "ku", "kur", "sa", "po", "ose", "apo", "tij",
    "saj", "tyre", "ma", "me", "mu", "na", "ju", "ia", "the", "a", "to", "is",
}
# Mohimet: ngjiten me fjalën pasardhëse ("nuk pelqeu" -> "nuk_pelqeu")
NEGATIONS = {"nuk", "s", "jo", "mos", "pa", "asnje", "aspak", "not", "no"}

_URL = re.compile(r"https?://\S+|www\.\S+")
_REPEAT = re.compile(r"(\w)\1{2,}")
_NON_WORD = re.compile(r"[^a-z0-9_ ]+")


def normalize(text: str) -> str:
    """Shkronja të vogla, pa diakritikë (ë->e, ç->c), emoji -> token."""
    text = str(text).lower()
    text = _URL.sub(" ", text)
    for ch in POS_EMOJI:
        text = text.replace(ch, " emojipoz ")
    for ch in NEG_EMOJI:
        text = text.replace(ch, " emojineg ")
    text = text.replace("'", " ").replace("’", " ")  # s'me -> s me
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = _REPEAT.sub(r"\1", text)  # shuuume -> shume
    text = _NON_WORD.sub(" ", text)
    text = re.sub(r"\d+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    tokens = [t for t in normalize(text).split() if t not in STOPWORDS]
    out, neg = [], None
    for tok in tokens:
        if tok in NEGATIONS:
            neg = tok if neg is None else f"{neg}_{tok}"
            continue
        out.append(f"{neg}_{tok}" if neg else tok)
        neg = None
    if neg:
        out.append(neg)
    return out


def clean_text(text: str) -> str:
    """Teksti final që i jepet vektorizuesit TF-IDF."""
    return " ".join(tokenize(text))
