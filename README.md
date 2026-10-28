# Zëri i Klientit: klasifikimi i komenteve sipas sentimentit

Projekt AI që trajnon një model Machine Learning për të ndarë komentet në shqip në
**pozitive** dhe **negative**, dhe e përdor atë në tre mënyra përmes një ndërfaqeje web (React):

1. **Testo komentin**: sentimenti, siguria, fjalët që vendosën, tema dhe përgjigje e gatshme.
2. **Analiza e biznesit**: ngarko një dataset (CSV, Excel, JSON, TXT, PDF) dhe merr raport të plotë.
3. **Rrjetet sociale**: ngjit linkun e një postimi (Instagram post/reel, Facebook, LinkedIn, TikTok)
   dhe komentet lexohen e analizohen automatikisht.

## Nisja e shpejtë

```powershell
cd "D:\Firdo Polis\sentiment_ai"
py -m venv .venv                                          # vetëm herën e parë
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run.bat                                                 # trajnon (nëse duhet), teston, nis serverin
```

Pastaj hap **http://127.0.0.1:5000**. Ndërfaqja React është e ndërtuar tashmë në `frontend/dist`.
Nëse ndryshon kodin e saj:

```powershell
cd frontend
npm install
npm run build        # ose: npm run dev  ->  http://localhost:5173 (me Flask ndezur në 5000)
```

## Analiza e biznesit

Skedari ka nevojë vetëm për kolonën `koment`. Kolonat e tjera janë opsionale dhe njihen në shqip
ose anglisht (`data/date`, `platforma/platform`, `produkti/product`, `kategoria/category`,
`qyteti/city/dega`, `vleresimi/rating`, `klienti/customer`). Raporti përmban:

| Pjesa | Çfarë tregon |
|---|---|
| KPI | % pozitive, neto sentimenti, vlerësimi mesatar, ndryshimi në 30 ditët e fundit, komente urgjente |
| Gjetjet | insight-e automatike: tendenca, burimi kryesor i ankesave, degët/produktet më të dobëta, valë ankesash |
| Çfarë të bësh | rekomandime sipas ankesave kryesore |
| Tendenca | volumi dhe kënaqësia sipas muajit / javës / ditës |
| Aspektet | dërgesa, çmimi, cilësia, stafi, aplikacioni, paketimi, ambienti: ankesa kundrejt lëvdatave, dhe në kohë |
| Krahasimi | sipas platformës, produktit, kategorisë, qytetit |
| Kur shkruajnë | ditët e javës, orët, shpërndarja e yjeve |
| Fjalët | fjalët më dalluese në ankesa dhe në lëvdata (log-odds) |
| Klientët | klientë unikë, të përsëritur, klientë në rrezik (2+ ankesa) |
| Listat | komente urgjente, komente për t'u ndarë, tabela e plotë me kërkim dhe filtra |
| Eksporti | CSV me sentimentin, sigurinë, aspektet dhe prioritetin për çdo rresht; printim si PDF |

**Dataseti shembull** `data/biznes_shembull.csv` (2 600 komente, 12 muaj, zinxhir picerish fiktiv
“Furra Dielli”) ka modele të fshehura që analiza i gjen vetë: ankesa për dërgesën në Durrës dhe në
dhjetor-janar, cilësi e dobët e sushit, valë ankesash për aplikacionin në qershor 2026, përmirësim gradual.
Rigjenerohet me `python data/generate_business.py`.

## Leximi i komenteve nga një link

| Platforma | Linqet që pranohen | Si lexohen |
|---|---|---|
| Instagram | `/p/...`, `/reel/...`, `/share/...` | Apify (`apify/instagram-scraper`, comments), ose Meta Graph API për llogarinë tuaj Business |
| Facebook | `/posts/...`, `permalink.php`, `/reel/...`, `/videos/...`, `/share/...` | Apify, ose Meta Graph API për faqen tuaj |
| LinkedIn | `/posts/...activity-...`, `/feed/update/urn:li:activity:...` | Apify |
| TikTok | `/@emri/video/...`, `vm.tiktok.com/...` | Apify |

**Konfigurimi** (një herë): krijo llogari falas në [apify.com](https://apify.com), kopjo API token-in
(Settings, API & Integrations) dhe vendose te paneli **Lidhjet** në faqen “Rrjetet sociale”.
Token-i ruhet në `.env` (shih `.env.example`) dhe nuk i dërgohet kurrë shfletuesit.

Kujdes:
- Lexohen vetëm postime **publike**. Apify tarifon sipas përdorimit: Instagram rreth $2.70 për 1 000 komente
  në planin falas. **Plani falas kthen vetëm ~15 komente për postim në Instagram**; faqja e njofton këtë.
- Scraping i postimeve të të tjerëve mund të bjerë ndesh me kushtet e platformave. Për faqen ose
  llogarinë tuaj, përdor API-në zyrtare të Meta (`META_ACCESS_TOKEN` + `FB_PAGE_ID` / `IG_USER_ID`).
- API-të zyrtare të LinkedIn dhe TikTok kërkojnë miratim të veçantë, prandaj për to përdoret Apify.
- Pa token, faqja tregon hapat e konfigurimit; komentet mund të ngjiten edhe me dorë te “Analiza e biznesit”.

## Si lidhet me çdo modul të kursit

| Moduli | Ku është në projekt |
|---|---|
| AI në praktikë + Python environment | `.venv`, `requirements.txt`, `run.bat`, `.env` |
| Working with Real Data | CSV me zhurmë (`data/komente_raw.csv`), Excel/JSON/PDF, komente reale nga rrjetet sociale |
| Data Cleaning & Visualization | `src/data.py`, `src/preprocess.py`, `src/visualize.py`, grafikët në ndërfaqe |
| Machine Learning: First Model | `src/train.py`: TF-IDF (fjalë + karaktere) + Logistic Regression |
| Prediction & Classification | `src/predict.py`: klasa, probabiliteti, shpjegimi i fjalëve |
| Testing the Model | cross-validation, test set, komente reale me dorë, `tests/` (52 teste) |
| Automation with Python | `src/batch.py` (dosja `inbox/` → `outbox/`), raporti automatik i biznesit |
| APIs & Connecting Systems | REST API në `app.py`, Apify dhe Meta Graph API në `src/social.py` |
| AI for Text & Documents | `src/documents.py` (TXT, CSV, PDF), zbulimi i aspekteve në `src/business.py` |
| AI for Images | OCR nga screenshot komentesh (`pytesseract`, opsionale) |
| Generative AI & Open-Source LLMs | `src/assistant.py`: Ollama për përgjigje gjeneruese dhe klasifikim zero-shot |
| AI Assistants & Intelligent Automation | prioritet, veprim, përgjigje e sugjeruar, insight-e dhe rekomandime automatike |
| From Code to Working Prototype | ndërfaqja React (`frontend/`) e shërbyer nga Flask |
| Project Lab & Testing | `python -m pytest -q` |
| Real Project Demonstration | skenari më poshtë |

## Rezultatet e modelit

| Vlerësimi | Rezultati |
|---|---|
| Cross-validation F1 (LogReg / LinearSVC / NaiveBayes) | 99.8% / 99.8% / 99.4% |
| Test set (20% e datasetit) | 99.7% |
| Komente reale të shkruara me dorë (`data/test_real.csv`) | 97.5% (39/40) |
| Përputhja me yjet në datasetin e biznesit (4-5 yje = pozitiv, 1-2 = negativ) | 98.3% |

**Shënim i ndershëm:** të dhënat e trajnimit janë sintetike (shabllone), prandaj test set-i i brendshëm
është optimist. Edhe frazat e biznesit që shtova në trajnim janë shkruar nga e njëjta dorë si dataseti
shembull, ndaj 98.3% është gjithashtu optimiste. Numri më i ndershëm është 97.5% në 40 komente të
shkruara veçmas, por është një mostër e vogël. Për komente reale nga rrjetet sociale (zhargon,
anglisht, ironi) saktësia do jetë më e ulët. Përmirësimi: korrigjo gabimet te “Testo komentin” dhe kliko
“Ritrajno modelin”, ose shto komente reale me label te `data/komente_raw.csv`.

## API

| Metoda | Rruga | Përshkrimi |
|---|---|---|
| POST | `/api/predict` | `{"text": "..."}` → sentimenti, shpjegimi, aspektet, asistenti |
| POST | `/api/business/analyze` | multipart `file` ose `{"komente": "një për rresht"}` → raporti i plotë |
| GET / POST | `/api/business/sample` | shkarko / analizo datasetin shembull |
| POST | `/api/social/parse` | `{"url": "..."}` → platforma, lloji, ID |
| POST | `/api/social/fetch` | `{"url": "...", "limit": 200}` → komentet + raporti |
| GET / POST | `/api/settings` | statusi i çelësave (pa vlerat) / ruajtja në `.env` (vetëm nga localhost) |
| POST | `/api/batch` | skedar → klasifikim i thjeshtë + CSV |
| POST | `/api/feedback`, `/api/retrain` | korrigjime dhe ritrajnim |
| GET | `/api/model`, `/api/health` | metrikat dhe statusi |

## Struktura

```
sentiment_ai/
├── app.py                  Flask: API + shërben ndërfaqen React
├── frontend/               React + TypeScript + Tailwind v4 + Recharts + Motion
│   └── src/pages/          Analyze, Business, Social, Model
├── src/
│   ├── preprocess.py       pastrimi i tekstit shqip (ë/ç, emoji, mohime)
│   ├── train.py            trajnim + krahasim i 3 algoritmeve
│   ├── predict.py          parashikim me shpjegim
│   ├── business.py         analitika e biznesit
│   ├── social.py           leximi i komenteve nga linqet
│   ├── config.py           çelësat në .env
│   ├── assistant.py        prioritet, përgjigje, LLM lokal
│   ├── documents.py        TXT / CSV / PDF / OCR
│   └── batch.py            automatizim me dosje
├── data/                   datasetet dhe gjeneratorët
├── templates/index.html    ndërfaqja e thjeshtë rezervë (nëse React s'është ndërtuar)
└── tests/                  52 teste
```

## Skenari i demonstrimit (7 minuta)

1. **Testo komentin**: “Porosia vonoi dy orë dhe erdhi e ftohtë”. Trego fjalët që vendosën, temën
   “Dërgesa” dhe përgjigjen e gatshme. Pastaj “Nuk kisha asnjë problem” (mohim, pozitiv).
2. **Analiza e biznesit** → “Provo me shembullin”. Lexo gjetjet: Durrës dhe dërgesa, Sushi dhe cilësia,
   vala e ankesave për aplikacionin në qershor. Trego tendencën, aspektet, krahasimin sipas qytetit.
3. Shkarko CSV-në dhe printo raportin si PDF.
4. **Rrjetet sociale**: ngjit linkun e një reel-i publik në Instagram (me token Apify) dhe trego raportin.
5. **Modeli**: krahasimi i algoritmeve, matrica e konfuzionit, gabimet. Kliko “Ritrajno modelin”.
6. `python -m pytest -q`: 52 teste kalojnë.
