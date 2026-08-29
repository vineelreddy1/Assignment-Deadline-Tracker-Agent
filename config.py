"""
Configuration settings for Assignment Deadline Tracker Agent.
Handles environment variables, default reference date, and trace logging settings.
"""

import os
from datetime import date

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# LLM API Keys (Supports OpenAI, Gemini, Anthropic, or local/mock mode)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

# Reference Date for calculations. Default to current date.
# Can be overridden during testing or via configuration.
DEFAULT_REFERENCE_DATE = date.today()

# Trace logger toggle
VERBOSE_TRACE = True
