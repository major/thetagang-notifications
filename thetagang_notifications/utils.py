"""Small utilities for small tasks."""
from datetime import datetime

from dateutil import parser


def get_put_breakeven(strike, premium):
    """Return the breakeven on a cash secured or naked put."""
    return strike - premium


def get_call_breakeven(strike, premium):
    """Return the breakeven on a covered or naked call."""
    return strike + premium


def parse_expiry_date(expiry_date):
    """Convert JSON expiration date into Python date object"""
    if not expiry_date:
        return None

    return parser.parse(expiry_date, ignoretz=True)


def get_dte(expiry_date):
    """Calculate days to expiry (DTE) for a trade."""
    parsed_expiry = parse_expiry_date(expiry_date)
    return (parsed_expiry - datetime.now()).days
