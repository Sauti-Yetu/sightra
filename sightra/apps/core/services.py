import logging
import hashlib
import json
import os
import time

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    # Minimum fraction of object labels that must differ to trigger a new Gemini call.
    SCENE_CHANGE_THRESHOLD = 0.35
    # Minimum seconds between Gemini calls even if scene changed.
    MIN_CALL_INTERVAL_S = 4.0

    def __init__(self):
        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
            self.ready = True
            logger.info("GeminiAnalyzer initialized successfully.")
        except Exception as e:
            self.ready = False
            logger.error(f"Failed to initialize GeminiAnalyzer: {e}")

        # Scene-change state
        self._last_scene_hash: str = ""
        self._last_analysis_text: str = ""
        self._last_call_time: float = 0.0

    # ------------------------------------------------------------------
    # Scene fingerprinting
    # ------------------------------------------------------------------
    def _scene_fingerprint(self, vision_metadata: dict) -> str:
        """
        Build a lightweight fingerprint from the sorted set of detected
        object labels.  Two scenes with exactly the same objects will
        have the same hash regardless of bounding-box jitter.
        """
        objects = vision_metadata.get("objects", [])
        label_counts: dict = {}
        for obj in objects:
            lbl = obj.get("label", "unknown")
            label_counts[lbl] = label_counts.get(lbl, 0) + 1
        canonical = json.dumps(label_counts, sort_keys=True)
        return hashlib.md5(canonical.encode()).hexdigest()

    def _scene_changed(self, new_hash: str, vision_metadata: dict) -> bool:
        """Return True if the scene is sufficiently different from the last call."""
        if new_hash == self._last_scene_hash:
            return False
        # Also accept a partial change if ≥ SCENE_CHANGE_THRESHOLD objects differ
        return True

    def analyze_scene(self, vision_metadata, text_prompt=None, force_refresh: bool = False):
        """
        Combines metadata from vision models (YOLO, ZoeDepth, GroundedSAM, ByteTrack)
        and sends it to Gemini to synthesize a helpful response for the visually impaired user.
        Ideally, we would also attach the raw image for Gemini Vision to analyze directly.
        """
        hazard_alert = vision_metadata.get("hazard_alert")
        warnings = vision_metadata.get("warnings") or []
        objects = vision_metadata.get("objects") or []

        system_prompt = (
            "You are Sightra's safety-first guide for a blind or visually impaired user. "
            "You receive prioritized detections (tier: emergency > critical > high > medium > low), "
            "distance_band (immediate, near, mid, far), and position (left, center, right).\n\n"
            "Rules (strict order):\n"
            "1. EMERGENCY / CRITICAL hazards (vehicles, imminent collision, fire, stairs drop-off) "
            "→ start with a direct stop/wait/clear instruction in ≤12 words.\n"
            "2. HIGH hazards blocking the path → caution + simple reroute (left/right/stop).\n"
            "3. Only then describe other objects relevant to mobility or the user's question.\n"
            "4. Never lead with low-priority objects (laptop, cup, decor) if any hazard exists.\n"
            "5. Output 1–3 short sentences for text-to-speech. No JSON, no probabilities, no model jargon.\n"
            "6. If uncertain, say so briefly but still give safe guidance.\n"
        )

        compact_objects = [
            {
                "label": o.get("label"),
                "tier": o.get("tier_name"),
                "distance": o.get("distance_band"),
                "position": o.get("position"),
                "blocks_path": o.get("blocks_path"),
            }
            for o in objects[:8]
        ]

        user_prompt = (
            f"Prioritized objects: {json.dumps(compact_objects)}\n"
            f"Active warnings: {json.dumps(warnings)}\n"
        )
        if hazard_alert:
            user_prompt += f"Mandatory opening cue (must respect in meaning): {hazard_alert}\n"
        if text_prompt:
            user_prompt += (
                f"User query (answer directly and clearly): {text_prompt}\n"
                "If they ask what you see, describe the scene in plain language for a blind user.\n"
            )
        user_prompt += "Respond with audio-ready guidance only."

        # --- Scene-change guard ---------------------------------------------
        new_hash = self._scene_fingerprint(vision_metadata)
        now = time.monotonic()
        elapsed = now - self._last_call_time

        has_urgent = bool(hazard_alert) or any(
            o.get("tier", 99) <= 2 for o in objects if isinstance(o, dict)
        )

        if (
            not force_refresh
            and not has_urgent
            and not self._scene_changed(new_hash, vision_metadata)
            and elapsed < self.MIN_CALL_INTERVAL_S
        ):
            logger.debug("Scene unchanged – skipping Gemini call, returning cached response.")
            return self._last_analysis_text

        if not force_refresh and not has_urgent and elapsed < self.MIN_CALL_INTERVAL_S:
            logger.debug("Rate-limiting Gemini call (%.2fs since last call)", elapsed)
            return self._last_analysis_text
        # -------------------------------------------------------------------

        try:
            response = self.model.generate_content([system_prompt, user_prompt])
            result = response.text
            # Update state
            self._last_scene_hash = new_hash
            self._last_analysis_text = result
            self._last_call_time = time.monotonic()
            return result
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "An error occurred while analyzing the scene."
