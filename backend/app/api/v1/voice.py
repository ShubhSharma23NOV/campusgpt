"""Voice assistant endpoints – Speech-to-Text and Text-to-Speech."""

import io
import base64
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.core.security import require_any_user

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    language: str = "en"  # "en" | "hi"
    voice: str = "neutral"


class STTResponse(BaseModel):
    transcript: str
    language: str
    confidence: float


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    audio: UploadFile = File(..., description="Audio file (WAV/MP3/WebM)"),
    language: str = "en",
    payload: dict = Depends(require_any_user),
):
    """Convert speech to text using Google's Speech API via Gemini."""
    try:
        import google.generativeai as genai
        from app.core.config import settings

        genai.configure(api_key=settings.GEMINI_API_KEY)

        audio_bytes = await audio.read()
        if len(audio_bytes) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Audio file too large (max 10MB)")

        # Use Gemini's multimodal capability for transcription
        model = genai.GenerativeModel("gemini-1.5-flash")

        lang_instruction = {
            "en": "Transcribe this audio in English.",
            "hi": "इस ऑडियो को हिंदी में transcribe करें।",
            "hinglish": "Transcribe this audio. It may be in Hindi, English, or Hinglish (mix of both).",
        }.get(language, "Transcribe this audio.")

        # Create audio part
        audio_part = {"mime_type": audio.content_type or "audio/webm", "data": audio_bytes}

        response = model.generate_content([lang_instruction, audio_part])
        transcript = response.text.strip()

        return STTResponse(
            transcript=transcript,
            language=language,
            confidence=0.95,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech recognition failed: {str(e)}")


@router.post("/tts")
async def text_to_speech(
    req: TTSRequest,
    payload: dict = Depends(require_any_user),
):
    """Convert text to speech. Returns base64-encoded audio."""
    try:
        # Use gTTS (Google Text-to-Speech) as it's free and supports Hindi
        from gtts import gTTS

        lang_map = {
            "en": "en",
            "hi": "hi",
            "hinglish": "hi",  # Use Hindi for Hinglish
        }
        lang_code = lang_map.get(req.language, "en")

        tts = gTTS(text=req.text, lang=lang_code, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        audio_base64 = base64.b64encode(audio_buffer.read()).decode("utf-8")

        return {
            "audio_base64": audio_base64,
            "format": "mp3",
            "language": req.language,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.post("/tts/stream")
async def text_to_speech_stream(
    req: TTSRequest,
    payload: dict = Depends(require_any_user),
):
    """Stream audio response for TTS."""
    try:
        from gtts import gTTS

        lang_map = {"en": "en", "hi": "hi", "hinglish": "hi"}
        lang_code = lang_map.get(req.language, "en")

        tts = gTTS(text=req.text, lang=lang_code, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=response.mp3"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS streaming failed: {str(e)}")
