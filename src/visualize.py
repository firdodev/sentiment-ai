"""Grafikë për të kuptuar të dhënat dhe modelin (ruhen në reports/)."""
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .data import ROOT, load_clean  # noqa: E402
from .preprocess import tokenize  # noqa: E402

REPORTS = ROOT / "reports"
COLORS = {"pozitiv": "#2a78d6", "negativ": "#e34948"}  # të njëjtat si ndërfaqja


def _save(fig, name) -> Path:
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / name
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def class_distribution(df):
    counts = df["sentimenti"].value_counts()
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.bar(counts.index, counts.values, color=[COLORS[c] for c in counts.index])
    for i, v in enumerate(counts.values):
        ax.text(i, v, str(v), ha="center", va="bottom")
    ax.set_title("Shpërndarja e komenteve")
    ax.set_ylabel("Numri")
    return _save(fig, "shperndarja.png")


def length_histogram(df):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    for label, color in COLORS.items():
        lengths = df.loc[df["sentimenti"] == label, "koment"].str.split().str.len()
        ax.hist(lengths, bins=20, alpha=0.6, label=label, color=color)
    ax.set_title("Gjatësia e komenteve (fjalë)")
    ax.set_xlabel("Fjalë")
    ax.legend()
    return _save(fig, "gjatesia.png")


def top_words(df, n=12):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, (label, color) in zip(axes, COLORS.items()):
        counter = Counter()
        for text in df.loc[df["sentimenti"] == label, "koment"]:
            counter.update(tokenize(text))
        words, freqs = zip(*counter.most_common(n))
        ax.barh(words[::-1], freqs[::-1], color=color)
        ax.set_title(f"Fjalët më të shpeshta – {label}")
    return _save(fig, "fjalet_kryesore.png")


def confusion_matrix_plot(cm, labels):
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels)
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Parashikuar")
    ax.set_ylabel("E vërtetë")
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, cm[i][j], ha="center", va="center",
                    color="white" if cm[i][j] > cm.max() / 2 else "black", fontsize=14)
    ax.set_title("Matrica e konfuzionit")
    return _save(fig, "matrica_konfuzionit.png")


def model_comparison(scores: dict):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    names = list(scores)
    ax.bar(names, [scores[n] for n in names], color="#3d5a80")
    ax.set_ylim(min(scores.values()) - 0.05, 1.0)
    ax.set_title("Krahasimi i modeleve (F1, cross-validation)")
    for i, n in enumerate(names):
        ax.text(i, scores[n], f"{scores[n]:.3f}", ha="center", va="bottom")
    return _save(fig, "krahasimi_modeleve.png")


def main():
    df = load_clean()
    for p in (class_distribution(df), length_histogram(df), top_words(df)):
        print("Ruajtur:", p)


if __name__ == "__main__":
    main()
