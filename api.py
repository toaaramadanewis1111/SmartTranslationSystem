from fastapi.middleware.cors import CORSMiddleware
from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Form
)
from pydantic import ValidationError
from typing import Optional
from pathlib import Path
import tempfile
import os
import requests

from llm.schemas import TranslationRequest
from llm.translator import translate


app = FastAPI(
    title="MyBTranslation API",
    description="Multilingual Translation and Vocabulary Recommendation Service",
    version="2.0.0"
)

frontend_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# =====================================================
# GLOBAL MODEL INSTANCES
# =====================================================

vocabulary_predictor = None
ocr_service = None
_vocabulary_predictor_attempted = False
_ocr_service_attempted = False


@app.on_event("startup")
def load_models():
    print("Translation API ready. Optional models load only when requested.")


def _get_vocabulary_predictor():
    global vocabulary_predictor, _vocabulary_predictor_attempted

    if os.getenv("ENABLE_VOCABULARY_PREDICTOR", "1").lower() in {
        "0", "false", "no", "off"
    }:
        return None

    if not _vocabulary_predictor_attempted:
        _vocabulary_predictor_attempted = True
        try:
            from predection.predict import VocabularyPredictor

            vocabulary_predictor = VocabularyPredictor()
        except Exception as error:
            print(f"Vocabulary predictor unavailable: {error}")

    return vocabulary_predictor


def _get_ocr_service():
    global ocr_service, _ocr_service_attempted

    if not _ocr_service_attempted:
        _ocr_service_attempted = True
        try:
            from ocr.ocr_service import OCRService

            ocr_service = OCRService()
        except Exception as error:
            print(f"OCR service unavailable: {error}")

    return ocr_service


# =====================================================
# HOME
# =====================================================

@app.get("/")
def home():

    return {
        "message": "MyBTranslation API is running",
        "status": "healthy"
    }


# =====================================================
# HEALTH
# =====================================================

@app.get("/health")
def health():

    return {
        "api": "healthy",
        "llm": "configured",
        "ocr": "ready" if ocr_service else (
            "unavailable" if _ocr_service_attempted else "not_loaded"
        ),
        "vocabulary_predictor": "ready" if vocabulary_predictor else (
            "disabled"
            if os.getenv("ENABLE_VOCABULARY_PREDICTOR", "1").lower()
            in {"0", "false", "no", "off"}
            else (
                "unavailable"
                if _vocabulary_predictor_attempted
                else "not_loaded"
            )
        )
    }


# =====================================================
# SHARED PROCESSING PIPELINE
# =====================================================

def process_translation(
    text,
    source_lang,
    target_lang,
    style,
    context=None
):

    try:

        request = TranslationRequest(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            style=style,
            context=context
        )

        # STEP 1: LLM TRANSLATION

        translation_result = translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            context=request.context,
            style=request.style
        )

        if hasattr(translation_result, "model_dump"):
            translation_result = translation_result.model_dump()

        # STEP 2: LIGHTGBM PREDICTION

        recommended_vocabulary = []

        predictor = _get_vocabulary_predictor()

        if predictor is not None:
            topic = translation_result.get("topic")
            translated_text = translation_result.get("translation")
            prediction_language = request.target_lang

            if topic and translated_text and prediction_language:

                try:

                    recommended_vocabulary = (
                        predictor.predict(
                            sentence=f"{request.text}\n{translated_text}",
                            topic=topic,
                            target_lang=prediction_language,
                            top_k=5,
                            context=request.context
                        )
                    )

                except Exception as e:
                    print(f"Vocabulary prediction failed: {e}")

        # STEP 3: COMBINE RESULTS

        response = dict(translation_result)

        response["recommended_vocabulary"] = (
            recommended_vocabulary
        )

        return response

    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama. Make sure Ollama is running."
        )

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="The translation model took too long to respond."
        )

    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Translation service returned an error."
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )

    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=502,
            detail=str(e)
        )


# =====================================================
# TEXT INPUT
# =====================================================

@app.post("/translate")
def translate_text_endpoint(request: TranslationRequest):

    result = process_translation(
        text=request.text,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
        style=request.style,
        context=request.context
    )

    result["input_type"] = "text"

    return result


# =====================================================
# IMAGE INPUT
# =====================================================

@app.post("/translate/image")
async def translate_image_endpoint(

    file: UploadFile = File(...),

    target_lang: str = Form(...),

    source_lang: str = Form("en"),

    style: str = Form("natural"),

    context: Optional[str] = Form(None)

):

    image_ocr_service = _get_ocr_service()

    if image_ocr_service is None:

        raise HTTPException(
            status_code=503,
            detail="OCR service is unavailable."
        )

    # Validate image type
    allowed_extensions = {
        ".png", ".jpg", ".jpeg", ".bmp", ".webp"
    }

    extension = Path(file.filename or "").suffix.lower()

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail="Unsupported image format."
        )

    image_bytes = await file.read()

    if not image_bytes:

        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty."
        )

    temp_path = None

    try:

        # Save uploaded image temporarily
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp_file:

            temp_file.write(image_bytes)
            temp_path = temp_file.name

        # STEP 1: OCR
        extracted_text = image_ocr_service.extract_text(
            image_path=temp_path,
            language=source_lang
        )

        if not extracted_text.strip():

            raise HTTPException(
                status_code=422,
                detail="No readable text was detected in the image."
            )

        # STEP 2: LLM + LIGHTGBM
        result = process_translation(
            text=extracted_text,
            source_lang=source_lang,
            target_lang=target_lang,
            style=style,
            context=context
        )

        # STEP 3: Add OCR information
        result["input_type"] = "image"
        result["extracted_text"] = extracted_text

        return result

    except HTTPException:
        raise

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    finally:

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
