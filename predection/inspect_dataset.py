import pandas as pd
from pathlib import Path
file_path = Path(__file__).parent / "tufs-vocab.tsv"
df = pd.read_csv(file_path, sep="\t")
print("Dataset shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())
print("\nFirst 5 rows:")
print(df.head().to_string())
print("\nAvailable languages:")
print(df["lang"].value_counts())
required_languages = ["en", "ar", "fr", "es", "de", "zh", "ja"]

print("\nDataset columns:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head().to_string())