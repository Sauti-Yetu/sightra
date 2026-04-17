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
    MIN_CALL_INTERVAL_S = 1.5

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

    def analyze_scene(self, vision_metadata, text_prompt=None):
        """
        Combines metadata from vision models (YOLO, ZoeDepth, GroundedSAM, ByteTrack)
        and sends it to Gemini to synthesize a helpful response for the visually impaired user.
        Ideally, we would also attach the raw image for Gemini Vision to analyze directly.
        """
        system_prompt = (
            "You are a real-time environmental intelligence assistant designed for a visually impaired user. "
            "You interpret structured scene data from computer vision systems, including detected objects, distances (in meters), "
            "and spatial positioning relative to the user.\n\n"

            "Your first task is to infer the user's current state: stationary (e.g., seated, standing still) or navigating (walking or moving).\n\n"

            "Behavior rules:\n"

            "1. If the user is STATIONARY:\n"
            "- Describe the immediate environment in a calm, concise, and informative way.\n"
            "- Focus on relevant objects, layout, and spatial relationships (e.g., 'Laptop is directly in front of you, about half a meter away').\n"
            "- Do NOT give navigation advice or safety warnings unless there is an immediate hazard.\n"
            "- Help the user build a mental map of their surroundings.\n\n"

            "2. If the user is NAVIGATING:\n"
            "- Prioritize safety-critical information first.\n"
            "- Clearly describe obstacles, their distance, and direction (e.g., 'Obstacle one meter ahead, slightly to your left').\n"
            "- Suggest safe paths using simple directional guidance (e.g., 'Clear path to your right').\n"
            "- Keep instructions short, direct, and actionable.\n\n"

            "3. Communication style:\n"
            "- Use short, natural sentences optimized for audio delivery.\n"
            "- Prioritize the most important information first.\n"
            "- Avoid unnecessary detail or repetition.\n"
            "- Do NOT mention raw model data, probabilities, or technical terms.\n"
            "- Speak as a calm, confident guide.\n\n"

            "4. Spatial clarity:\n"
            "- Always describe positions relative to the user (front, left, right, behind).\n"
            "- Include approximate distances when relevant.\n"
            "- Highlight changes in the environment immediately.\n\n"

            "5. Safety and uncertainty handling:\n"
            "- If an obstacle is close (within ~1.5 meters), treat it as high priority.\n"
            "- If data is uncertain or incomplete, communicate cautiously (e.g., 'Possible object ahead').\n"
            "- Never remain silent if there may be a safety risk.\n\n"

            "Your goal is to provide real-time, context-aware, and trustworthy environmental awareness "
            "that enhances safety, independence, and confidence."
        )

        user_prompt = f"Vision Metadata from Frame: {json.dumps(vision_metadata, indent=2)}\n"
        if text_prompt:
            user_prompt += f"User Voice Command/Query: {text_prompt}\n"
        
        user_prompt += "Analyze the scene to infer the user's current state (e.g., seated, standing, walking). Then provide a confident, concise, and highly relevant audio-ready response tailored exactly to what they are doing."

        # --- Scene-change guard ---------------------------------------------
        new_hash = self._scene_fingerprint(vision_metadata)
        now = time.monotonic()
        elapsed = now - self._last_call_time

        if not self._scene_changed(new_hash, vision_metadata) and elapsed < self.MIN_CALL_INTERVAL_S:
            logger.debug("Scene unchanged – skipping Gemini call, returning cached response.")
            return self._last_analysis_text

        if elapsed < self.MIN_CALL_INTERVAL_S:
            # Rate-limit even for changed scenes to avoid hammering the API
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
