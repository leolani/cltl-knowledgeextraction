"""
The Leolani Triple Extractor Package contains tools to extract SPO triples from Natural Language.
"""

import logging.config
from pathlib import Path

# create logger
LOGGING_CONFIG_PATH = Path(__file__).parents[3] / 'config' / 'logging.config'
logging.config.fileConfig(LOGGING_CONFIG_PATH)
logger = logging.getLogger(__name__)
