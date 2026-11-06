import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
INPUT_FILE = DATA_DIR / "tufs-vocab.tsv"
OUTPUT_FILE = DATA_DIR / "topic_vocabulary.csv"

LANGUAGES = ["en", "ar", "fr", "es", "de", "zh", "ja"]

# Map TUFS Japanese scene labels to project topics
SCENE_TO_TOPIC = {
    "海外旅行": "Travel",
    "駅": "Travel",
    "道": "Travel",

    "レストラン／食堂": "Food & Dining",
    "食生活": "Food & Dining",
    "喫茶店": "Food & Dining",

    "学校": "Education",
    "授業": "Education",
    "図書館": "Education",

    "会社": "Work",

    "病院": "Healthcare",

    "店": "Shopping",
    "デパート": "Shopping",

    "銀行": "Finance",

    "スポーツ": "Sports",

    "天気": "Weather",

    "娯楽・趣味": "Entertainment",

    "家庭／家": "Home",
    "部屋": "Home",
    "道具・家具": "Home",
    "不動産屋": "Home",

    "郵便局": "Communication",
    "ことば": "Communication",

    "家族": "Family",
    "人間": "People",
}

print("Loading TUFS dataset...")

df = pd.read_csv(INPUT_FILE, sep="\t")

# Keep the seven project languages
df = df[df["lang"].isin(LANGUAGES)].copy()

# Remove rows without vocabulary
df = df.dropna(subset=["lemma", "scenes"])

# Normalize text
df["lemma"] = df["lemma"].astype(str).str.strip()
df["scenes"] = df["scenes"].astype(str).str.strip()

# Handle entries assigned to multiple scenes
df["scene"] = df["scenes"].str.split(",")
df = df.explode("scene")
df["scene"] = df["scene"].str.strip()

# Map scene labels to project topics
df["topic"] = df["scene"].map(SCENE_TO_TOPIC)

# Keep only mapped topics
df = df.dropna(subset=["topic"])

# Remove empty vocabulary
df = df[df["lemma"] != ""]

# Keep useful columns
result = df[
    ["topic", "scene", "lang", "lemma", "cid", "examples"]
].drop_duplicates(subset=["topic", "lang", "lemma"])

# Save
result.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("\nTopic vocabulary created!")
print("Total vocabulary entries:", len(result))

print("\nEntries per topic:")
print(result["topic"].value_counts())

print("\nEntries per language:")
print(result["lang"].value_counts())

print("\nTravel vocabulary by language:")

travel = result[result["topic"] == "Travel"]

for lang in LANGUAGES:
    words = travel[travel["lang"] == lang]["lemma"].head(15).tolist()
    print(f"\n{lang}: {words}")

print(f"\nSaved to: {OUTPUT_FILE}")