"""Testet e projektit:  python -m pytest -q"""
import io

import pandas as pd
import pytest

from src.data import clean_dataframe, normalize_label
from src.preprocess import clean_text, normalize
from src.train import REAL_TEST_PATH


# --- Pastrimi i tekstit ---
def test_normalize_removes_diacritics_and_urls():
    assert normalize("Shërbim i SHKËLQYER! http://x.com") == "sherbim i shkelqyer"


def test_normalize_collapses_repeats_and_emoji():
    assert normalize("shuuuume mire 😍") == "shume mire emojipoz"


def test_negation_is_attached():
    assert clean_text("Nuk më pëlqeu") == "nuk_pelqeu"
    assert clean_text("s'me pelqeu") == "s_pelqeu"


# --- Pastrimi i datasetit ---
def test_clean_dataframe_drops_bad_rows():
    df = pd.DataFrame({"koment": ["Mirë", "Mirë", "", None, "Keq", "x"],
                       "sentimenti": ["Pozitiv", "pozitiv", "pozitiv", "negativ", "0", "pozitiv"]})
    clean, report = clean_dataframe(df)
    assert list(clean["koment"]) == ["Mirë", "Keq"]
    assert list(clean["sentimenti"]) == ["pozitiv", "negativ"]
    assert report["dublikime"] == 1


@pytest.mark.parametrize("raw,expected", [("POZITIV", "pozitiv"), ("negative", "negativ"),
                                          ("1", "pozitiv"), ("ndoshta", None)])
def test_normalize_label(raw, expected):
    assert normalize_label(raw) == expected


# --- Modeli ---
@pytest.fixture(scope="module")
def model():
    from src.predict import SentimentModel
    return SentimentModel()


@pytest.mark.parametrize("text,expected", [
    ("Shërbim fantastik, e rekomandoj!", "pozitiv"),
    ("Produkt i shkëlqyer, faleminderit", "pozitiv"),
    ("Nuk do të kthehem më kurrë, turp", "negativ"),
    ("cilesi shume e dobet, humbje parash", "negativ"),
    ("nuk punon fare 😡", "negativ"),
])
def test_model_predictions(model, text, expected):
    assert model.predict(text)["sentimenti"] == expected


def test_prediction_structure(model):
    r = model.predict("Shumë mirë")
    assert set(r) >= {"sentimenti", "besueshmeria", "probabilitetet", "i_pasigurt", "fjalet_kyce"}
    assert abs(sum(r["probabilitetet"].values()) - 1) < 1e-6


def test_empty_text_is_unknown(model):
    assert model.predict("!!! ...")["sentimenti"] == "i panjohur"


def test_accuracy_on_handwritten_set(model):
    real = pd.read_csv(REAL_TEST_PATH)
    preds = [model.predict(t)["sentimenti"] for t in real["koment"]]
    accuracy = (pd.Series(preds) == real["sentimenti"]).mean()
    assert accuracy >= 0.85, f"Saktësia ra në {accuracy:.2%}"


# --- API ---
@pytest.fixture(scope="module")
def client():
    from app import app
    app.config["TESTING"] = True
    return app.test_client()


def test_api_predict(client):
    res = client.post("/api/predict", json={"text": "Stafi shumë i sjellshëm"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["sentimenti"] == "pozitiv"
    assert "pergjigja" in data["asistenti"]


def test_api_predict_validation(client):
    assert client.post("/api/predict", json={}).status_code == 400


def test_api_batch_txt(client):
    file = (io.BytesIO("Shumë mirë!\nShumë keq, turp\n".encode()), "komente.txt")
    res = client.post("/api/batch", data={"file": file}, content_type="multipart/form-data")
    assert res.status_code == 200
    summary = res.get_json()["permbledhje"]
    assert summary == {**summary, "gjithsej": 2, "pozitiv": 1, "negativ": 1}
