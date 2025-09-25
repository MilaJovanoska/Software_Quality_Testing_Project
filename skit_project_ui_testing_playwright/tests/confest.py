# tests/conftest.py
import os, sys

# Додај го root директориумот (еден кат погоре од tests/) во sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
