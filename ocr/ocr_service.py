import os
# Disable oneDNN for PaddleX CPU inference.
# This must be set BEFORE importing PaddleOCR.
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"
import torch
from paddleocr import PaddleOCR
class OCRService:

    def __init__(self):

        print("Loading PaddleOCR models...")

        # English OCR model
        self.ocr_en = PaddleOCR(
            lang="en",
            use_doc_orientation_classify=True,
            use_doc_unwarping=True,
            use_textline_orientation=True
        )

        # Arabic OCR model
        self.ocr_ar = PaddleOCR(
            lang="ar",
            use_doc_orientation_classify=True,
            use_doc_unwarping=True,
            use_textline_orientation=True
        )

        print("PaddleOCR models loaded successfully!")

    def extract_text(self, image_path, language="en"):

        if language == "en":
            ocr_model = self.ocr_en

        elif language == "ar":
            ocr_model = self.ocr_ar

        else:
            raise ValueError(
                "OCR currently supports English and Arabic only."
            )

        result = ocr_model.predict(image_path)

        extracted_text = []

        for res in result:

            data = res.json["res"]

            texts = data["rec_texts"]
            scores = data["rec_scores"]

            for text, score in zip(texts, scores):

                if score >= 0.50 and text.strip():
                    extracted_text.append(text)

        return "\n".join(extracted_text)
