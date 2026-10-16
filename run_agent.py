"""
Quick CLI runner for the AI Competitor Watch Agent.
Example:
    python run_agent.py --preset "Frontier AI Labs"
    python run_agent.py --competitors "OpenAI, Anthropic, Cursor, Perplexity, Mistral AI" --days 14
"""

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.agent import cli_main

if __name__ == "__main__":
    cli_main()
