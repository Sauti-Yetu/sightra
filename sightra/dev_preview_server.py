#!/usr/bin/env python3
"""
Local frontend preview server only.
Stubs heavy ML imports so Django can render templates without full ML stack installed.
Does not modify application business logic.
"""
import sys
from unittest.mock import MagicMock

for mod in (
    "cv2",
    "torch",
    "torchvision",
    "ultralytics",
    "google.generativeai",
    "transformers",
    "numpy",
    "pyttsx3",
):
    sys.modules.setdefault(mod, MagicMock())

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sightra.settings")

import django

django.setup()

from django.core.management import execute_from_command_line

if __name__ == "__main__":
    port = os.environ.get("PORT", "8765")
    execute_from_command_line(["dev_preview_server.py", "runserver", f"127.0.0.1:{port}", "--noreload"])
