from celery import shared_task
from .services import GeminiAnalyzer
from apps.vision.tasks import process_frame_vision_pipeline

analyzer = GeminiAnalyzer()

@shared_task
def analyze_frame_context(frame_data, text_prompt=None, run_vision_first=True, frame_id=1):
    """
    Coordinates the vision pipeline and Gemini reasoning.
    If run_vision_first=True, it synchronously triggers the vision pipeline inside this task.
    (Alternatively, they can be chained in Celery using Canvas primitives like `chain` or `chord`).
    """
    vision_metadata = {}
    
    if run_vision_first:
        # Alternatively: process_frame_vision_pipeline.delay().get() if we want it isolated,
        # but running directly avoids extra broker overhead for a sequence of tasks that 
        # MUST happen sequentially for the analyzer.
        vision_metadata = process_frame_vision_pipeline(frame_data, frame_id)
        
    analysis_text = analyzer.analyze_scene(vision_metadata, text_prompt)
    
    return {
        "analysis_text": analysis_text,
        "vision_metadata": vision_metadata
    }

