import logging
import google.generativeai as genai
from django.conf import settings
import json
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    def __init__(self):
        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
            self.ready = True
            logger.info("GeminiAnalyzer initialized successfully.")
        except Exception as e:
            self.ready = False
            logger.error(f"Failed to initialize GeminiAnalyzer: {e}")

    def analyze_scene(self, vision_metadata, text_prompt=None):
        """
        Combines metadata from vision models (YOLO, ZoeDepth, GroundedSAM, ByteTrack)
        and sends it to Gemini to synthesize a helpful response for the visually impaired user.
        Ideally, we would also attach the raw image for Gemini Vision to analyze directly.
        """
        system_prompt = (
            "You are a highly capable and empathetic AI navigation assistant for a visually impaired user. "
            "You will be provided with scene metadata from computer vision models, including object detection, "
            "depth (distance in meters), and semantic segmentation. "
            "Your job is to read this metadata and provide a concise, clear, and reassuring description of the environment, "
            "highlighting safe pathways and warning about potential obstacles."
        )

        user_prompt = f"Vision Metadata from Frame: {json.dumps(vision_metadata, indent=2)}\n"
        if text_prompt:
            user_prompt += f"User Voice Command/Query: {text_prompt}\n"
        
        user_prompt += "Please provide a safe, confident, and very brief audio-ready description of the path ahead."

        try:
            response = self.model.generate_content([system_prompt, user_prompt])
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "An error occurred while analyzing the scene. Please proceed with caution."
