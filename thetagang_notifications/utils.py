"""Small utilities for small tasks."""
from datetime import datetime
import logging

from dateutil import parser
import finviz
import requests
import tld
import yfinance as yf


log = logging.getLogger(__name__)


# IEX logo URLs.
IEX_PRIMARY_LOGO_URL = "https://storage.googleapis.com/iexcloud-hl37opg/api/logos"
IEX_SECONDARY_LOGO_URL = "https://storage.googleapis.com/iex/api/logos"

# When IEX does not have a logo for a stock, it returns a 403 or returns a placeholder
# image with an ugly, wavy picture. The picture has a common MD5 hash that we can
# detect and work around.
IEX_PLACEHOLDER_IMAGE_HASH = "md5=ZLE6FlAxyV8t6arLO5AFeg=="


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
    if dte == 0:
        # Computers dislike dividing by zero. It hurts.
        dte = 1
    elif dte < 0:
        # We aren't time travelers here.
        return None
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


def get_logo(symbol):
    """Generate a URL to a stock logo on IEX cloud."""
    # More details: https://iexcloud.io/docs/api/#logo
    return f"https://storage.googleapis.com/iex/api/logos/{symbol.upper()}.png"


def get_stock_logo(symbol):
    """Get a stock logo like a honeybadger and never give up."""
    result = get_logo_iex(f"{IEX_PRIMARY_LOGO_URL}/{symbol}.png")

    if result:
        return result

    result = get_logo_iex(f"{IEX_SECONDARY_LOGO_URL}/{symbol}.png")

    if result:
        return result

    return get_logo_clearbit(symbol)


def get_finviz_stock(symbol):
    """Get data about a stock from finviz."""
    try:
        return finviz.get_stock(symbol)
    except Exception:
        return None


def get_base_domain(url):
    """Take a URL and get the base domain, such as example.com or example.co.uk."""
    return tld.get_fld(url, fix_protocol=True)


def get_logo_iex(url):
    """Get a stock logo from IEX Cloud."""
    resp = requests.get(url)

    # Check if we got a 403/404 because the logo does not exist.
    if not resp.ok:
        log.info("🖼 Logo failed: %s", url)
        return None

    # Check if the default logo image is being returned.
    hashes = resp.headers.get("x-goog-hash", None)
    if hashes and IEX_PLACEHOLDER_IMAGE_HASH in hashes:
        log.info("🖼 Logo placeholder spotted: %s", url)
        return None

    return url


def get_logo_clearbit(symbol):
    """Get a logo using clearbit, which requires a domain name."""
    finviz_data = get_finviz_stock(symbol)

    if not finviz_data:
        return None

    # Ensure the finviz result has a URL listed.
    if "Website" not in finviz_data.keys() or not finviz_data["Website"]:
        return None

    domain = tld.get_fld(finviz_data["Website"])
    return f"https://logo.clearbit.com/{domain}"


def get_stock_chart(symbol):
    """Get a URL for the stock chart."""
    return f"https://finviz.com/chart.ashx?t={symbol}&ty=c&ta=1&p=d"
