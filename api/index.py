"""Vercel Serverless Entrypoint for JalDrishti FastAPI Backend.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Exports the ASGI application for Vercel Python runtime execution.
"""

import os
import sys

# Ensure repository root is in python module search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app  # noqa: E402
