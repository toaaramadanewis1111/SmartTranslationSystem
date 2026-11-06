import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
INPUT_FILE = DATA_DIR / "tufs-vocab.tsv"

df = pd.read_csv(INPUT_FILE, sep="\t")

# Keep rows with a thematic scene
scenes = df.dropna(subset=["scenes"]).copy()

scenes["scenes"] = scenes["scenes"].astype(str).str.strip()
scenes = scenes[scenes["scenes"] != ""]

print("Total entries with scenes:", len(scenes))

print("\nMost common scenes:")
print(scenes["scenes"].value_counts().head(30).to_string())

print("\nSample vocabulary entries with scenes:")
print(
    scenes[["lang", "lemma", "scenes", "examples"]]
    .head(20)
    .to_string(index=False)
)

print("\nLanguages represented in scenes:")
print(scenes["lang"].value_counts().to_string())
print("\nMost common scene labels:")
print(
    df["scenes"]
    .dropna()
    .value_counts()
    .head(40)
    .to_string()
)