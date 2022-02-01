"""Top-level package for thetagang-notifications."""
import logging
import sys

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s;%(levelname)s;%(message)s",
)

__author__ = """Major Hayden"""
__email__ = "major@mhtx.net"
__version__ = "0.1.0"
