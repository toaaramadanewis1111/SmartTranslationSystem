import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
import csv
from itertools import permutations
from llm.translator import translate
# One sample sentence in each supported language
samples = {
    "en": "I enjoy learning artificial intelligence.",
    "ar": "أحب تعلم الذكاء الاصطناعي.",
    "fr": "J'aime apprendre l'intelligence artificielle.",
    "es": "Me gusta aprender inteligencia artificial.",
    "de": "Ich lerne gerne künstliche Intelligenz.",
    "zh": "我喜欢学习人工智能。",
    "ja": "人工知能を学ぶことが好きです。"
}

languages = list(samples.keys())
# Generate all directed language pairs
language_pairs = list(permutations(languages, 2))
results = []
print(f"Starting {len(language_pairs)} translation tests...\n")
for index, (source, target) in enumerate(language_pairs, start=1):
    print(
        f"[{index}/{len(language_pairs)}] "
        f"{source} -> {target}"
    )
    try:
        result = translate(
            text=samples[source],
            source_lang=source,
            target_lang=target,
            context="A general statement about learning.",
            style="natural"
        )

        results.append({
            "source_lang": source,
            "target_lang": target,
            "status": "SUCCESS",
            "translation": result.translation,
            "alternatives_count": len(result.alternatives),
            "ambiguity": result.ambiguity.is_ambiguous,
            "error": ""
        })

        print("SUCCESS")
        print("Translation:", result.translation)

    except Exception as error:

        results.append({
            "source_lang": source,
            "target_lang": target,
            "status": "FAILED",
            "translation": "",
            "alternatives_count": 0,
            "ambiguity": "",
            "error": str(error)
        })

        print("FAILED:", error)

    print("-" * 50)
# Save results to CSV
with open(
    "tests/language_test_results.csv",
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:
    fieldnames = [
        "source_lang",
        "target_lang",
        "status",
        "translation",
        "alternatives_count",
        "ambiguity",
        "error"
    ]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)


# Final summary
successful = sum(
    result["status"] == "SUCCESS"
    for result in results
)

failed = len(results) - successful

print("\n========== FINAL REPORT ==========")
print(f"Total tests: {len(results)}")
print(f"Successful: {successful}")
print(f"Failed: {failed}")
print(f"Success rate: {successful / len(results) * 100:.2f}%")
print("Report saved to tests/language_test_results.csv")
