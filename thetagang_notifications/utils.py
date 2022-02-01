"""Small utilities for small tasks."""
from datetime import datetime


from dateutil import parser
from finvizfinance.quote import finvizfinance


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


def get_pretty_expiration(expiry_date):
    """Generate a pretty expiration date for trade notifications."""
    parsed_date = parse_expiry_date(expiry_date)
    dte = get_dte(expiry_date)
    if dte <= 365:
        return parsed_date.strftime("%m/%d")

    return parsed_date.strftime("%m/%d/%y")


def get_symbol_details(symbol):
    """Get information about a stock/ETF symbol from finviz."""
    try:
        stock = finvizfinance(symbol)
        details = stock.ticker_fundament()
        details["Symbol"] = symbol
    except:
        details = {"Symbol": symbol}

    return details


def get_stock_chart(symbol):
    """Get a URL for the stock chart."""
    return f"https://finviz.com/chart.ashx?t={symbol}&ty=c&ta=1&p=d"


def get_stock_logo(symbol):
    """Return a URL to a stock logo."""
    return f"https://g.foolcdn.com/art/companylogos/square/{symbol}.png"
