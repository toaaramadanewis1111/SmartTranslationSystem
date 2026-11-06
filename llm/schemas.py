from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
language_codes = Literal["en", "ar", "fr", "es", "de", "zh", "ja"]
TranslationStyle = Literal[
    "natural",
    "formal",
    "casual",
    "professional"
]
class TranslationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    source_lang: language_codes
    target_lang: language_codes
    context: str | None = None
    style: TranslationStyle = "natural"
class AmbiguityInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_ambiguous: bool
    chosen_meaning: str | None
    confidence: Literal["low", "medium", "high"]
class VocabularyRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    word: str
    score: float

class TranslationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    translation: str
    source_lang: str
    target_lang: str
    topic: str
    style: TranslationStyle
    ambiguity: AmbiguityInfo
    alternatives: list[str]
    recommended_vocabulary: list[VocabularyRecommendation] = Field(
        default_factory=list
    )
