"""Small utilities for small tasks."""
import logging

import finviz
import requests
import tld

log = logging.getLogger(__name__)


# IEX logo URLs.
IEX_PRIMARY_LOGO_URL = "https://storage.googleapis.com/iexcloud-hl37opg/api/logos"
IEX_SECONDARY_LOGO_URL = "https://storage.googleapis.com/iex/api/logos"

# When IEX does not have a logo for a stock, it returns a 403 or returns a placeholder
# image with an ugly, wavy picture. The picture has a common MD5 hash that we can
# detect and work around.
IEX_PLACEHOLDER_IMAGE_HASH = "md5=ZLE6FlAxyV8t6arLO5AFeg=="


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
    """Take a URL and get the base domain, such as example.com or
    example.co.uk."""
    return tld.get_fld(url, fix_protocol=True)


def get_logo_iex(url):
    """Get a stock logo from IEX Cloud."""
    resp = requests.get(url, timeout=15)

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

    domain = tld.get_fld(finviz_data["Website"])
    return f"https://logo.clearbit.com/{domain}"


def get_stock_chart(symbol):
    """Get a URL for the stock chart."""
    return f"https://finviz.com/chart.ashx?t={symbol}&ty=c&ta=1&p=d"
