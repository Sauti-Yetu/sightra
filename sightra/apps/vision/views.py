from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import YoloObjectDetector, ZoeDepthEstimator
import logging

logger = logging.getLogger(__name__)
yolo_detector = YoloObjectDetector()
depth_estimator = ZoeDepthEstimator()

# Create your views here.
def vision(request):
    return render(request, "vision.html")

class ObjectDetectionView(APIView):
    """
    API for real-time object detection using YOLO.
    """
    def post(self, request):
        image_b64 = request.data.get("image")
        if not image_b64:
            return Response({"error": "No image data provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        detections = yolo_detector.detect(image_b64)
        return Response({
            "detections": detections,
            "count": len(detections)
        }, status=status.HTTP_200_OK)

class SceneAnalysisView(APIView):
    """
    Full scene analysis including depth and object tracking.
    """
    def post(self, request):
        image_b64 = request.data.get("image")
        if not image_b64:
            return Response({"error": "No image data provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        detections = yolo_detector.detect(image_b64)
        depth_data = depth_estimator.estimate_depth(image_b64)
        
        return Response({
            "objects": detections,
            "depth": depth_data,
            "summary": f"Detected {len(detections)} objects in the scene."
        }, status=status.HTTP_200_OK)