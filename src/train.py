"""Trajnimi, krahasimi dhe vlerësimi i modelit të sentimentit.

Përdorimi:  python -m src.train
"""
import json
from datetime import datetime

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from . import visualize
from .data import LABELS, ROOT, load_clean
from .preprocess import clean_text

REAL_TEST_PATH = ROOT / "data" / "test_real.csv"
MODEL_PATH = ROOT / "models" / "sentiment_model.joblib"
METRICS_PATH = ROOT / "models" / "metrics.json"


def build_features():
    # Fjalë (1-2 gram) + karaktere (3-5 gram, toleron gabime shkrimi)
    return FeatureUnion([
        ("word", TfidfVectorizer(preprocessor=clean_text, token_pattern=r"(?u)\b\w+\b",
                                 ngram_range=(1, 2), sublinear_tf=True, min_df=1)),
        ("char", TfidfVectorizer(preprocessor=clean_text, analyzer="char_wb",
                                 ngram_range=(3, 5), sublinear_tf=True, min_df=2)),
    ])


def candidates():
    return {
        "LogisticRegression": LogisticRegression(C=4.0, max_iter=2000),
        "NaiveBayes": MultinomialNB(alpha=0.3),
        "LinearSVC": CalibratedClassifierCV(LinearSVC(C=0.5), cv=3),
    }


def make_pipeline(clf):
    return Pipeline([("features", build_features()), ("clf", clf)])


def train(verbose=True):
    df = load_clean()
    X, y = df["koment"], df["sentimenti"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42)

    # 1) Krahaso modelet me cross-validation vetëm në train set
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = {}
    for name, clf in candidates().items():
        scores = cross_val_score(make_pipeline(clf), X_train, y_train, cv=cv, scoring="f1_macro")
        cv_scores[name] = round(float(scores.mean()), 4)
        if verbose:
            print(f"  {name:20s} F1 = {scores.mean():.4f} ± {scores.std():.4f}")
    best_name = max(cv_scores, key=cv_scores.get)

    # 2) Vlerëso modelin më të mirë në test set (të dhëna që s'i ka parë kurrë)
    model = make_pipeline(candidates()[best_name]).fit(X_train, y_train)
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred, labels=list(LABELS))
    errors = [{"koment": t, "e_verteta": a, "parashikuar": p}
              for t, a, p in zip(X_test, y_test, y_pred) if a != p]

    metrics = {
        "modeli": best_name,
        "data": datetime.now().isoformat(timespec="seconds"),
        "madhesia_dataset": len(df),
        "train": len(X_train),
        "test": len(X_test),
        "cv_f1": cv_scores,
        "test_accuracy": round(accuracy_score(y_test, y_pred), 4),
        "test_f1": round(f1_score(y_test, y_pred, average="macro"), 4),
        "raporti": classification_report(y_test, y_pred, output_dict=True),
        "matrica_konfuzionit": cm.tolist(),
        "gabime_shembull": errors[:15],
    }

    # 3) Ritrajno në të gjithë datasetin për versionin final që përdor aplikacioni
    final = make_pipeline(candidates()[best_name]).fit(X, y)

    # 4) Test i ndershëm: komente të shkruara me dorë, jashtë shablloneve të datasetit
    if REAL_TEST_PATH.exists():
        real = pd.read_csv(REAL_TEST_PATH)
        real_pred = final.predict(real["koment"])
        metrics["test_real_accuracy"] = round(accuracy_score(real["sentimenti"], real_pred), 4)
        metrics["test_real_f1"] = round(f1_score(real["sentimenti"], real_pred, average="macro"), 4)
        metrics["test_real_gabime"] = [
            {"koment": t, "e_verteta": a, "parashikuar": p}
            for t, a, p in zip(real["koment"], real["sentimenti"], real_pred) if a != p]

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(final, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    visualize.confusion_matrix_plot(cm, list(LABELS))
    visualize.model_comparison(cv_scores)
    if verbose:
        print(f"\nModeli më i mirë: {best_name}")
        print(f"Test accuracy: {metrics['test_accuracy']}  |  Test F1: {metrics['test_f1']}")
        print(classification_report(y_test, y_pred))
        if "test_real_accuracy" in metrics:
            print(f"Test real (me dorë): accuracy {metrics['test_real_accuracy']}"
                  f"  |  F1 {metrics['test_real_f1']}")
            for e in metrics["test_real_gabime"]:
                print(f"   GABIM: {e['koment']!r} -> {e['parashikuar']} (duhej {e['e_verteta']})")
        print(f"Ruajtur: {MODEL_PATH}")
    return metrics


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("Krahasimi i modeleve (5-fold CV):")
    train()
