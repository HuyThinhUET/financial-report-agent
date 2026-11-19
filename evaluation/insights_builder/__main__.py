"""Run the consolidated financial statement insight builder."""
import sys
from .extract_financial_insights import main

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8')

sys.exit(main())
