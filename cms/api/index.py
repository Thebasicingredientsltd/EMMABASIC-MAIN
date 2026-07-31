"""Vercel serverless entry point for the Emma Basic CMS.

Vercel's @vercel/python runtime serves the module-level WSGI callable named
`app`. We simply put the cms/ directory on the import path and re-export the
Flask app defined in app.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402  (must come after sys.path tweak)

# Exposed for Vercel's Python runtime.
application = app
