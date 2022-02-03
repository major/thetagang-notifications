"""Small utilities for small tasks."""
from datetime import datetime

from dateutil import parser
import yfinance as yf


def get_breakeven(trade):
    """Return the breakeven on a cash secured or naked put."""
    premium = float(trade["price_filled"])
    match trade["type"]:
        case "CASH SECURED PUT":
            strike = float(trade["short_put"])
            result = strike - premium
        case "COVERED CALL" | "SHORT NAKED CALL":
            strike = float(trade["short_call"])
            result = strike + premium
        case _:
            return None

    return result


def get_short_put_return(trade):
    """Calculate the return and annualized return for a short put."""
    strike = float(trade["short_put"])
    premium = trade["price_filled"]

    return (premium / (strike - premium)) * 100


def get_short_call_return(trade):
    """Calculate the return and annualized return for a short call."""
    strike = float(trade["short_call"])
    premium = trade["price_filled"]

    return (premium / (strike - premium)) * 100


def get_annualized_return(potential_return, dte):
    """Calculate the annualized return for a trade."""
    return (potential_return / dte) * 365


def parse_expiry_date(expiry_date):
    """Convert JSON expiration date into Python date object"""
    if not expiry_date:
        return None

    return parser.parse(expiry_date, ignoretz=True)


def gather_strikes(trade):
    """Gather option strikes in a generic way."""
    strikes = {
        "short put": trade["short_put"],
        "short call": trade["short_call"],
        "long put": trade["long_put"],
        "long call": trade["long_call"],
    }

    # Make a string from the generic list of strikes.
    return "/".join([f"${v}" for k, v in strikes.items() if v is not None]).capitalize()


def get_dte(expiry_date):
    """Calculate days to expiry (DTE) for a trade."""
    parsed_expiry = parse_expiry_date(expiry_date)
    return (parsed_expiry - datetime.now()).days


def get_pretty_expiration(expiry_date):
    """Generate a pretty expiration date for trade notifications."""
    if not expiry_date:
        return None

    parsed_date = parse_expiry_date(expiry_date)
    dte = get_dte(expiry_date)
    if dte <= 365:
        return parsed_date.strftime("%m/%d")

    return parsed_date.strftime("%m/%d/%y")


def get_pretty_price(price):
    """Generate a pretty price based on a float."""
    return "{:,.2f}".format(price)


def get_symbol_details(symbol):
    """Get information about a stock/ETF symbol."""
    try:
        stock = yf.Ticker(symbol)
        details = stock.get_info()
    except:
        details = {"symbol": symbol}

    return details


def get_stock_chart(symbol):
    """Get a URL for the stock chart."""
    return f"https://finviz.com/chart.ashx?t={symbol}&ty=c&ta=1&p=d"
