"""Parashikimi i sentimentit për tekst të ri, me shpjegim të fjalëve kyçe.

Përdorimi:  python -m src.predict "Shërbimi ishte fantastik!"
"""
import json

import joblib
import numpy as np

from .preprocess import clean_text
from .train import METRICS_PATH, MODEL_PATH

UNCERTAIN_BELOW = 0.65  # nën këtë besueshmëri, rezultati shënohet "i pasigurt"


class SentimentModel:
    def __init__(self, path=MODEL_PATH):
        if not path.exists():
            raise FileNotFoundError(f"Modeli mungon: {path}. Ekzekuto: python -m src.train")
        self.pipeline = joblib.load(path)
        self.classes = list(self.pipeline.classes_)
        self.metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8")) if METRICS_PATH.exists() else {}
        self._weights = self._linear_weights()
        self._features = self.pipeline.named_steps["features"].get_feature_names_out()

    def _linear_weights(self):
        """Pesha për çdo veçori: >0 shtyn drejt 'pozitiv', <0 drejt 'negativ'."""
        clf = self.pipeline.named_steps["clf"]
        if hasattr(clf, "coef_"):
            return clf.coef_[0]
        if hasattr(clf, "feature_log_prob_"):
            return clf.feature_log_prob_[1] - clf.feature_log_prob_[0]
        if hasattr(clf, "calibrated_classifiers_"):
            return np.mean([c.estimator.coef_[0] for c in clf.calibrated_classifiers_], axis=0)
        return None

    def explain(self, text, top=6):
        if self._weights is None:
            return []
        vec = self.pipeline.named_steps["features"].transform([text]).tocoo()
        contrib = []
        for idx, value in zip(vec.col, vec.data):
            name = self._features[idx]
            if name.startswith("word__"):
                contrib.append((name[6:].replace("_", " "), float(value * self._weights[idx])))
        contrib.sort(key=lambda x: abs(x[1]), reverse=True)
        return [{"fjala": w, "ndikimi": round(c, 3)} for w, c in contrib[:top]]

    def predict(self, text: str) -> dict:
        text = str(text)
        if not clean_text(text):
            return {"teksti": text, "sentimenti": "i panjohur", "besueshmeria": 0.0,
                    "probabilitetet": {}, "i_pasigurt": True, "fjalet_kyce": []}
        proba = self.pipeline.predict_proba([text])[0]
        best = int(np.argmax(proba))
        return {
            "teksti": text,
            "sentimenti": self.classes[best],
            "besueshmeria": round(float(proba[best]), 4),
            "probabilitetet": {c: round(float(p), 4) for c, p in zip(self.classes, proba)},
            "i_pasigurt": bool(proba[best] < UNCERTAIN_BELOW),
            "fjalet_kyce": self.explain(text),
        }

    def predict_many(self, texts):
        return [self.predict(t) for t in texts]

    def predict_batch(self, texts) -> list[dict]:
        """Version i shpejtë për mijëra komente: pa shpjegim fjalësh."""
        texts = [str(t) for t in texts]
        valid = [i for i, t in enumerate(texts) if clean_text(t)]
        out = [{"teksti": t, "sentimenti": "i panjohur", "besueshmeria": 0.0, "i_pasigurt": True}
               for t in texts]
        if valid:
            proba = self.pipeline.predict_proba([texts[i] for i in valid])
            for i, p in zip(valid, proba):
                best = int(np.argmax(p))
                out[i].update(sentimenti=self.classes[best], besueshmeria=round(float(p[best]), 4),
                              i_pasigurt=bool(p[best] < UNCERTAIN_BELOW))
        return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    model = SentimentModel()
    for t in sys.argv[1:] or ["Shërbimi ishte fantastik!", "Nuk do të kthehem më kurrë."]:
        print(json.dumps(model.predict(t), ensure_ascii=False, indent=2))
