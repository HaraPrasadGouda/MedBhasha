"""
MedBhasha Gemini Extractor Service
Utilizes Google GenAI SDK (gemini-3.5-flash-lite by default) with Pydantic
Structured Outputs to transcribe medical prescriptions and pathology lab reports.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from google import genai

from backend.schemas import DocumentExtraction
from backend.services.gemini_models import generate_content

load_dotenv()

SYSTEM_EXTRACTION_INSTRUCTION = """
You are MedBhasha's expert medical document transcriptionist specializing in Indian clinical documents:
handwritten doctor prescriptions, hospital discharge summaries, and printed diagnostic laboratory reports.

STRICT OPERATIONAL DIRECTIVES:
1. FIDELITY FIRST: Transcribe ONLY what is visibly written or printed.
2. NO SPECULATION: DO NOT invent medications, missing symptoms, clinical diagnoses, or lab test interpretations.
3. ILLEGIBILITY HANDLING: If a doctor's handwriting for a drug name is partially illegible, transcribe the exact legible letters/characters. Never guess or hallucinate an unwritten drug.
4. DOSAGE & TIMING EXTRACTION:
   - Identify dosage strength (e.g., '650mg', '500mg', '10mg', '5ml', 'Unspecified').
   - Identify frequency codes: '1-0-1' (morning & night), '1-0-0' (morning only), '0-0-1' (night only), '1-1-1' (three times daily), 'SOS' (as needed), 'BD' (twice daily), 'TDS' (thrice daily), 'OD' (once daily), 'HS' (bedtime).
   - Set numeric counts: morning_count, afternoon_count, night_count (e.g. 1-0-1 gives morning_count=1.0, afternoon_count=0.0, night_count=1.0).
   - Classify meal_timing strictly as 'before_food', 'after_food', 'with_food', or 'unspecified'.
   - Identify duration_days if stated (e.g., 'x 5 days' -> 5, '1 month' -> 30).
   - general_purpose: state high-level clinical intent (e.g., 'Fever and pain relief', 'Blood sugar control', 'Blood pressure management', 'Antibiotic').
5. LAB BIOMARKER EXTRACTION:
   - For lab reports, transcribe test_name, numeric value (float if present), raw_value_text, unit, and printed_reference_range.
   - Do NOT evaluate whether a test value is high or low; only extract the literal numbers and printed reference ranges.
6. CLASSIFICATION:
   - Set document_type to 'prescription', 'lab_report', or 'mixed'.
   - Extract patient instructions (e.g., 'Drink plenty of warm water', 'Review after 5 days with FBS report').
"""


class GeminiMedicalExtractor:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key or self.api_key == "your-gemini-api-key-here":
            self.client = None
        else:
            self.client = genai.Client(
                api_key=self.api_key, http_options={"timeout": 90000}
            )

    def _is_configured(self) -> bool:
        return self.client is not None

    def _parse_response(self, response) -> DocumentExtraction:
        if hasattr(response, "parsed") and response.parsed:
            return response.parsed
        if getattr(response, "text", None):
            return DocumentExtraction.model_validate_json(response.text)
        raise RuntimeError("Gemini model returned empty response for document extraction.")

    def extract_document(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> DocumentExtraction:
        if not self.client:
            raise ValueError(
                "GEMINI_API_KEY is not set or invalid. Please configure your key in backend/.env"
            )

        from google import genai as _genai

        image_part = _genai.types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        )

        prompt = (
            "Carefully analyze and transcribe all visible medical information from this document. "
            "Follow the strict instructions: do not guess illegible text, extract exact medicines, "
            "frequency counts (morning, afternoon, night), meal timings, and lab biomarkers."
        )

        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_EXTRACTION_INSTRUCTION,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=DocumentExtraction,
        )

        response = generate_content(
            self.client,
            contents=[image_part, prompt],
            config=config,
            operation="document extraction",
        )
        return self._parse_response(response)

    def extract_document_from_text(self, text: str) -> DocumentExtraction:
        if not self.client:
            raise ValueError(
                "GEMINI_API_KEY is not set or invalid. Please configure your key in backend/.env"
            )

        from google.genai import types

        prompt = (
            "The following text was extracted from a medical document (prescription or lab report). "
            "Carefully transcribe every medicine, dosage, frequency, meal timing, and lab biomarker "
            "into the strict JSON schema. Do not guess missing values; use 'Unspecified' where unknown.\n\n"
            "DOCUMENT TEXT:\n" + text
        )

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_EXTRACTION_INSTRUCTION,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=DocumentExtraction,
        )

        response = generate_content(
            self.client,
            contents=[prompt],
            config=config,
            operation="document text extraction",
        )
        return self._parse_response(response)


# Global singleton instance
gemini_extractor = GeminiMedicalExtractor()
