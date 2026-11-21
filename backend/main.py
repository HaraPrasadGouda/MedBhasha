"""
MedBhasha Backend - Vernacular AI Prescription & Lab Report Decoder
FastAPI Application Entry Point
"""

import os
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.schemas import (
    DocumentExtraction,
    LocalizedGuidance,
    TTSRequest,
    VerifiedDocumentResult,
)
from backend.services.gemini_extractor import gemini_extractor
from backend.services.image_processor import (
    extract_pdf_text,
    preprocess_medical_image,
)
from backend.services.localizer import vernacular_localizer
from backend.services.tts_service import synthesize_speech_stream
from backend.services.verifier import verify_document_extraction

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "or": "Odia (ଓଡ଼ିଆ)",
    "bn": "Bengali (বাংলা)",
    "ta": "Tamil (தமிழ்)",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[MedBhasha] Initializing vernacular medical AI decoder services...")
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your-gemini-api-key-here":
        print(
            "[MedBhasha WARNING] GEMINI_API_KEY is not configured or using placeholder. "
            "Configure it in backend/.env for multimodal AI extraction."
        )
    else:
        print("[MedBhasha] Gemini API Key detected and configured.")
    yield
    print("[MedBhasha] Shutting down services.")


app = FastAPI(
    title="MedBhasha API",
    description="Vernacular AI Prescription & Lab Report Decoder API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    gemini_configured: bool
    supported_languages: Dict[str, str]


class LocalizeRequest(BaseModel):
    verification: VerifiedDocumentResult
    language: str = "hi"


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="ok",
        app="MedBhasha - Vernacular AI Medical Decoder",
        version="1.0.0",
        gemini_configured=bool(GEMINI_API_KEY and GEMINI_API_KEY != "your-gemini-api-key-here"),
        supported_languages=SUPPORTED_LANGUAGES,
    )


@app.post("/api/preprocess", tags=["Image Processing"])
async def preprocess_image_endpoint(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded.",
            )

        result = preprocess_medical_image(content)
        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "preview_base64": result["preview_base64"],
            "metrics": result["metrics"],
            "dimensions": result["dimensions"],
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image preprocessing failed: {str(exc)}",
        )


@app.post("/api/verify-data", response_model=VerifiedDocumentResult, tags=["Verification"])
async def verify_data_endpoint(extraction: DocumentExtraction):
    try:
        return verify_document_extraction(extraction)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(exc)}",
        )


@app.post("/api/localize", response_model=LocalizedGuidance, tags=["Localization"])
async def localize_endpoint(req: LocalizeRequest):
    try:
        clean_lang = (req.language or "hi").lower().strip()
        if clean_lang not in SUPPORTED_LANGUAGES:
            clean_lang = "hi"
        return vernacular_localizer.generate_vernacular_guidance(
            verified_doc=req.verification, language=clean_lang
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Localization failed: {str(exc)}",
        )


@app.post("/api/tts", tags=["Speech Synthesis"])
async def text_to_speech_endpoint(req: TTSRequest):
    try:
        clean_lang = (req.language or "hi").lower().strip()
        if clean_lang not in SUPPORTED_LANGUAGES:
            clean_lang = "hi"
        audio_stream, media_type = await synthesize_speech_stream(req.text, clean_lang)
        return StreamingResponse(
            audio_stream,
            media_type=media_type,
            headers={
                "Content-Disposition": f'inline; filename="medbhasha_audio_{clean_lang}.mp3"',
                "Cache-Control": "no-cache",
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS synthesis failed: {str(exc)}",
        )


@app.post("/api/analyze", tags=["End-to-End Pipeline"])
async def analyze_medical_document_endpoint(
    file: UploadFile = File(...),
    language: str = Form(default="hi"),
) -> Dict[str, Any]:
    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        clean_lang = (language or "hi").lower().strip()
        if clean_lang not in SUPPORTED_LANGUAGES:
            clean_lang = "hi"

        # 1. Preprocess image; fall back to PDF text extraction when no raster image
        #    can be rendered (e.g. text-only PDFs without poppler).
        text_pdf_content: Optional[str] = None
        proc_result: Optional[Dict[str, Any]] = None
        try:
            proc_result = preprocess_medical_image(content)
        except ValueError as pre_err:
            if content.startswith(b"%PDF"):
                text_pdf_content = extract_pdf_text(content)
                if not text_pdf_content:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=(
                            "Could not extract an image or text from the provided PDF file. "
                            "Please upload a JPG, PNG, or a text-based PDF."
                        ),
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=str(pre_err),
                )

        # 2. Extract structured entities with Gemini (or raise informative error).
        try:
            if text_pdf_content is not None:
                raw_extraction = gemini_extractor.extract_document_from_text(text_pdf_content)
            else:
                raw_extraction = gemini_extractor.extract_document(
                    image_bytes=proc_result["enhanced_image_bytes"],
                    mime_type="image/png",
                )
        except ValueError as key_err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(key_err),
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI extraction failed: {str(exc)}",
            )

        # 3. Deterministic verification & clinical lab rule evaluation
        verified_result = verify_document_extraction(raw_extraction)

        # 4. Localize guidance & generate natural spoken summary script
        localized_guidance = vernacular_localizer.generate_vernacular_guidance(
            verified_doc=verified_result,
            language=clean_lang,
        )

        if proc_result is not None:
            preview_base64 = proc_result["preview_base64"]
            quality_metrics = proc_result["metrics"]
            dimensions = proc_result["dimensions"]
        else:
            preview_base64 = None
            quality_metrics = {
                "blur_variance": None,
                "brightness_score": None,
                "is_blurry": False,
                "is_too_dark": False,
                "is_too_bright": False,
                "quality_status": "text_pdf",
                "warnings": ["Text-based PDF detected; image quality metrics are not applicable."],
            }
            dimensions = None

        return {
            "success": True,
            "filename": file.filename,
            "language": clean_lang,
            "quality_metrics": quality_metrics,
            "preview_base64": preview_base64,
            "dimensions": dimensions,
            "raw_extraction": raw_extraction.model_dump(),
            "verification": verified_result.model_dump(),
            "localized_guidance": localized_guidance.model_dump(),
            "spoken_summary_script": localized_guidance.spoken_summary_script,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline failed: {str(exc)}",
        )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)