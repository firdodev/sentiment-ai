"""Testet për analitikën e biznesit dhe leximin e linqeve sociale."""
import io

import pandas as pd
import pytest

from src import business, social


@pytest.fixture(scope="module")
def model():
    from src.predict import SentimentModel
    return SentimentModel()


# --- Zbulimi i kolonave dhe aspekteve ---
def test_detect_columns_albanian_and_english():
    cols = business.detect_columns(["Komenti", "Date", "Platform", "Qyteti", "Rating", "user"])
    assert cols == {"koment": "Komenti", "data": "Date", "platforma": "Platform",
                    "qyteti": "Qyteti", "vleresimi": "Rating", "klienti": "user"}


@pytest.mark.parametrize("text,aspect", [
    ("Dërgesa vonoi një orë", "Dërgesa"),
    ("shume e shtrenjte per ate qe merr", "Çmimi"),
    ("aplikacioni bllokohet gjatë pagesës", "Aplikacioni"),
    ("kamarieri ishte i pasjellshëm", "Stafi"),
])
def test_detect_aspects(text, aspect):
    assert aspect in business.detect_aspects(text)


def test_para_se_is_not_price():
    assert "Çmimi" not in business.detect_aspects("korrieri më telefonoi para se të vinte")


# --- Analiza ---
def test_analyze_minimal_dataset(model):
    df = pd.DataFrame({"text": ["Shumë mirë, faleminderit", "Keq fare, turp", "nuk më pëlqeu"]})
    report, export = business.analyze(df, model)
    assert report["kpi"]["gjithsej"] == 3
    assert report["kpi"]["negativ"] == 2
    assert "tendenca" not in report  # pa datë -> pa tendencë
    assert len(export) == 3 and "sentimenti" in export


def test_analyze_full_dataset(model):
    df = pd.DataFrame({
        "data": pd.date_range("2026-01-01", periods=60, freq="D").astype(str),
        "koment": ["Dërgesa erdhi shpejt, bravo!", "Dërgesa vonoi shumë, turp"] * 30,
        "qyteti": ["Tiranë", "Durrës"] * 30,
        "vleresimi": [5, 1] * 30,
    })
    report, _ = business.analyze(df, model)
    assert report["kpi"]["perqindja_pozitive"] == 50.0
    assert report["kpi"]["vleresimi_mesatar"] == 3.0
    assert report["aspektet"][0]["aspekti"] == "Dërgesa"
    durres = next(r for r in report["dimensionet"]["qyteti"]["rreshtat"] if r["emri"] == "Durrës")
    assert durres["perqindja_pozitive"] == 0.0
    assert report["tendenca"] and report["insights"]


def test_analyze_requires_comment_column(model):
    with pytest.raises(ValueError):
        business.analyze(pd.DataFrame({"numri": [1, 2]}), model)


# --- Linqet sociale ---
@pytest.mark.parametrize("url,platform,kind,ident", [
    ("https://www.instagram.com/p/DN8-GjPkgjS/?igsh=abc", "instagram", "post", "DN8-GjPkgjS"),
    ("instagram.com/reel/DDIJAfeyemG", "instagram", "reel", "DDIJAfeyemG"),
    ("https://www.tiktok.com/@bellapoarch/video/6862153058223197445?is_from_webapp=1",
     "tiktok", "video", "6862153058223197445"),
    ("https://vm.tiktok.com/ZMabc123/", "tiktok", "video", None),
    ("https://www.linkedin.com/posts/firma_titulli-activity-7320867199693246465-AbCd",
     "linkedin", "post", "7320867199693246465"),
    ("https://www.linkedin.com/feed/update/urn:li:activity:7320867199693246465/",
     "linkedin", "post", "7320867199693246465"),
    ("https://www.facebook.com/faqja/posts/pfbid0BbKbkisExKGSKuhee9a7i86Rw", "facebook", "post",
     "pfbid0BbKbkisExKGSKuhee9a7i86Rw"),
    ("https://m.facebook.com/permalink.php?story_fbid=123456&id=987", "facebook", "post", "123456"),
    ("https://www.facebook.com/reel/1234567890", "facebook", "reel", "1234567890"),
    ("https://www.instagram.com/share/BAC6cDeb_-", "instagram", "post", None),
    ("https://www.instagram.com/share/reel/BAbCd12_x", "instagram", "reel", None),
])
def test_parse_url(url, platform, kind, ident):
    info = social.parse_url(url)
    assert (info["platforma"], info["lloji"], info["id"]) == (platform, kind, ident)
    assert info["url"].startswith("https://")
    assert "igsh" not in info["url"] and "is_from_webapp" not in info["url"]


@pytest.mark.parametrize("url", ["https://youtube.com/watch?v=x", "https://www.instagram.com/firma/",
                                 "", "https://www.tiktok.com/@firma"])
def test_parse_url_rejects(url):
    with pytest.raises(social.SocialError):
        social.parse_url(url)


def test_normalize_apify_items():
    li = social._normalize_item("linkedin", {"commentary": "Shumë mirë", "actor": {"name": "Arta"},
                                             "createdAt": "2026-01-01", "reactionTypeCounts": [{"count": 2}, {"count": 1}]})
    assert li == {"koment": "Shumë mirë", "autori": "Arta", "data": "2026-01-01", "pelqime": 3}
    assert social._normalize_item("tiktok", {"error": "not found"}) is None
    assert social._normalize_item("facebook", {"text": "  "}) is None


def test_fetch_without_config_explains_setup(monkeypatch):
    for key in ("APIFY_TOKEN", "META_ACCESS_TOKEN", "FB_PAGE_ID", "IG_USER_ID"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(social.SocialError) as exc:
        social.fetch_comments("https://www.instagram.com/p/ABC123/")
    assert exc.value.code == "pa_konfigurim" and exc.value.help


def test_fetch_apify_mocked(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test")
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    calls = {}

    def fake_request(url, data=None, headers=None, timeout=60):
        calls.update(url=url, data=data)
        return [{"text": "Super produkt!", "ownerUsername": "arta", "timestamp": "2026-10-01T10:00:00Z",
                 "likesCount": 4}, {"text": "Keq fare"}]

    monkeypatch.setattr(social, "_request", fake_request)
    out = social.fetch_comments("https://www.instagram.com/reel/ABC123/", limit=50)
    assert out["burimi"] == "apify" and out["numri"] == 2
    assert "apify~instagram-scraper" in calls["url"]
    assert calls["data"] == {"directUrls": ["https://www.instagram.com/reel/ABC123/"],
                             "resultsType": "comments", "resultsLimit": 50, "addParentData": False}
    assert "15 komente" in out["shenim"]  # 2 komente nga 50 të kërkuara -> kufiri i planit falas


def test_fetch_apify_comment_scraper_override(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test")
    monkeypatch.setenv("APIFY_INSTAGRAM_ACTOR", "apify/instagram-comment-scraper")
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    calls = {}

    def fake_request(url, data=None, headers=None, timeout=60):
        calls.update(url=url, data=data)
        return [{"text": "Shumë mirë", "ownerUsername": "a"}]

    monkeypatch.setattr(social, "_request", fake_request)
    out = social.fetch_comments("https://www.instagram.com/p/ABC123/", limit=10)
    assert "apify~instagram-comment-scraper" in calls["url"] and "resultsType" not in calls["data"]
    assert "shenim" not in out  # limit 10 <= 15: s'ka kufizim për t'u njoftuar


# --- API ---
@pytest.fixture(scope="module")
def client():
    from app import app
    app.config["TESTING"] = True
    return app.test_client()


def test_api_business_sample(client):
    res = client.post("/api/business/sample")
    assert res.status_code == 200
    data = res.get_json()
    assert data["kpi"]["gjithsej"] > 1000 and data["insights"] and data["shkarko"].startswith("/api/download/")


def test_api_business_upload_csv(client):
    csv_bytes = "koment;qyteti\nShumë mirë!;Tiranë\nTurp, dërgesa vonoi;Durrës\n".encode("utf-8")
    res = client.post("/api/business/analyze", data={"file": (io.BytesIO(csv_bytes), "test.csv")},
                      content_type="multipart/form-data")
    assert res.status_code == 200
    assert res.get_json()["kpi"]["gjithsej"] == 2


def test_api_business_paste(client):
    res = client.post("/api/business/analyze", json={"komente": "Super!\nKeq fare"})
    assert res.status_code == 200 and res.get_json()["kpi"]["gjithsej"] == 2


def test_api_social_parse(client):
    res = client.post("/api/social/parse", json={"url": "https://www.tiktok.com/@a/video/123456789"})
    assert res.status_code == 200 and res.get_json()["platforma"] == "tiktok"


def test_settings_save_and_mask(tmp_path, monkeypatch):
    from src import config
    monkeypatch.setattr(config, "ENV_PATH", tmp_path / ".env")
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    config.save_env({"APIFY_TOKEN": "abc123", "PATH": "nuk-lejohet"})
    assert (tmp_path / ".env").read_text(encoding="utf-8") == "APIFY_TOKEN=abc123\n"
    status = config.status()
    assert status["APIFY_TOKEN"]["vendosur"] is True and "abc123" not in str(status)
    config.save_env({"APIFY_TOKEN": ""})
    assert (tmp_path / ".env").read_text(encoding="utf-8") == ""
