import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

url = (
    "https://raw.githubusercontent.com/"
    "omwn/tufs/master/tufs-vocab.tsv"
)

output_file = DATA_DIR / "tufs-vocab.tsv"

print("Downloading TUFS vocabulary dataset...")

try:
    urllib.request.urlretrieve(url, output_file)

    print("Download completed successfully!")
    print(f"Saved to: {output_file}")

except Exception as error:
    print(f"Download failed: {error}")