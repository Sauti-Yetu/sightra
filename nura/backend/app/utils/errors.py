"""User-facing error messages. Never leak stack traces or provider errors."""

CAMERA_DENIED = "Camera access is required to read visual information."
NETWORK_FAILURE = "Nura couldn't connect to the AI service. Please check your connection."
LOW_CONFIDENCE = "I couldn't confidently identify the information."
EMPTY_RESULT = "I couldn't find readable text in this image."
UNCLEAR_IMAGE = "I couldn't read this clearly. Try moving closer or improving the lighting."
INVALID_IMAGE = "That image couldn't be used. Try capturing again."
INVALID_AUDIO = "I couldn't hear that clearly. Please try speaking again."
FILE_TOO_LARGE = "That file is too large. Try capturing again from a bit farther away."
RATE_LIMITED = "Nura is busy right now. Please wait a moment and try again."
NO_CONTEXT = "I don't have a recent scan to answer from. Capture the visual information first."
TTS_UNAVAILABLE = "The spoken response isn't available right now. The text result is still ready."
STT_UNAVAILABLE = "Voice input isn't available right now. You can type your question instead."
GENERIC = "Something went wrong while reading. Please try again."


class UserFacingError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
