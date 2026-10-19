# CareBridge Spoken Audio Generation Service
# Implements PRD Section 13.3 and FR-15 (Stretch Goal)

from io import BytesIO
import logging
from typing import Optional

logger = logging.getLogger("carebridge.audio")


def generate_audio_bytes(text: str, lang: str = "en") -> Optional[bytes]:
    # Generates audio speech bytes for verified care plan text.
    # Uses gTTS if available; returns None if library not installed or network unavailable.
    try:
        from gtts import gTTS
        tts_lang = "te" if lang.startswith("te") else "en"
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        out = BytesIO()
        tts.write_to_fp(out)
        return out.getvalue()
    except Exception as e:
        logger.info("Backend gTTS unavailable: %s. Client-side SpeechSynthesis serves audio.", str(e))
        return None
