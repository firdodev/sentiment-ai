"""Fraza sipas aspektit të biznesit (dërgesa, çmimi, cilësia...).

Përdoren nga dy gjeneratorë:
  - generate_business.py  -> dataseti shembull i biznesit për analizë
  - generate_dataset.py   -> shton fjalor biznesi në të dhënat e trajnimit
"""

# {p} zëvendësohet me emrin e produktit
ASPECT_PHRASES = {
    "Dërgesa": {
        "pozitiv": [
            "dërgesa erdhi shumë shpejt", "korrieri ishte i sjellshëm dhe i saktë",
            "porosia mbërriti brenda 20 minutave", "dorëzimi ishte në kohë",
            "porosia erdhi e nxehtë dhe në orar", "korrieri më telefonoi para se të vinte",
        ],
        "negativ": [
            "dërgesa vonoi më shumë se një orë", "porosia mbërriti e ftohtë",
            "korrieri nuk e gjente adresën dhe askush nuk u përgjigj",
            "prita 90 minuta për porosinë", "më sollën porosinë e gabuar",
            "dorëzimi u vonua pa asnjë njoftim",
        ],
    },
    "Çmimi": {
        "pozitiv": [
            "çmimi është shumë i arsyeshëm", "ia vlen çdo lek",
            "oferta e fundjavës ishte super", "çmime të mira për këtë cilësi",
        ],
        "negativ": [
            "çmimet janë shumë të larta për sasinë", "shumë e shtrenjtë për atë që merr",
            "na morën më shumë lekë se çmimi në menu", "çmimet u rritën por cilësia jo",
        ],
    },
    "Cilësia": {
        "pozitiv": [
            "{p} kishte shije fantastike", "cilësia e ushqimit është e shkëlqyer",
            "porcioni bujar dhe shija perfekte", "{p} me shijen më të mirë në qytet",
            "përbërës të freskët, shije fantastike",
        ],
        "negativ": [
            "{p} erdhi pa shije", "ushqimi nuk ishte i freskët",
            "porcioni shumë i vogël dhe cilësi e dobët", "brumi ishte i djegur",
            "{p} kishte shije të keqe",
        ],
    },
    "Stafi": {
        "pozitiv": [
            "stafi shumë i sjellshëm", "operatorja më ndihmoi menjëherë",
            "shërbim korrekt nga ekipi", "kamarieri ishte shumë i dashur",
        ],
        "negativ": [
            "operatori më foli me ton të keq në telefon", "askush nuk iu përgjigj ankesës sime",
            "stafi ishte i pasjellshëm", "kamarieri nuk erdhi te tavolina për 20 minuta",
        ],
    },
    "Aplikacioni": {
        "pozitiv": [
            "aplikacioni është shumë i lehtë për t'u përdorur", "porosita online pa asnjë problem",
            "pagesa me kartë funksionoi shpejt", "aplikacioni i ri është shumë i mirë",
        ],
        "negativ": [
            "aplikacioni bllokohet gjatë pagesës", "nuk mund të hyj në llogari pas përditësimit",
            "aplikacioni më anuloi porosinë pa arsye", "pagesa me kartë dështoi tri herë",
        ],
    },
    "Paketimi": {
        "pozitiv": [
            "paketim i sigurt, asgjë nuk u derdh", "erdhi i paketuar mirë dhe i nxehtë",
            "paketim i bukur dhe ekologjik",
        ],
        "negativ": [
            "kutia erdhi e shtypur dhe salca e derdhur", "paketimi ishte i dobët",
            "pija erdhi e derdhur në qese",
        ],
    },
    "Ambienti": {
        "pozitiv": [
            "ambienti i pastër dhe i këndshëm", "lokali gjithmonë i rregullt",
            "atmosferë shumë e mirë për familjen",
        ],
        "negativ": [
            "tavolinat ishin të pista", "gjeta një qime në ushqim",
            "lokali ishte i zhurmshëm dhe i pistë",
        ],
    },
}

CLOSERS = {
    "pozitiv": ["Do të porosis përsëri!", "Faleminderit!", "E rekomandoj.", "Bravo ekipit!",
                "Pesë yje.", "Vazhdoni kështu!", "Jam shumë i kënaqur."],
    "negativ": ["Nuk do porosis më.", "Shumë i zhgënjyer.", "Kërkoj rimbursim.", "Turp!",
                "Rregullohuni.", "Hera e fundit.", "Nuk e rekomandoj."],
}
