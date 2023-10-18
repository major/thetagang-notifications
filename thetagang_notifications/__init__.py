"""Top-level package for thetagang-notifications."""

import logging
import sys

import sentry_sdk

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s;%(levelname)s;%(message)s",
)

__author__ = """Major Hayden"""
__email__ = "major@mhtx.net"
__version__ = "0.1.0"

sentry_sdk.init(
    dsn="https://c62e0d37db5d46b991a641b35878042a@o4504556291358720.ingest.sentry.io/4504556292341761",
    traces_sample_rate=1.0,
)
