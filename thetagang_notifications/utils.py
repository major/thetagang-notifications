"""Small utilities for small tasks."""
import logging

import requests
import tld
import yfinance

log = logging.getLogger(__name__)


# IEX logo URLs.
IEX_PRIMARY_LOGO_URL = "https://storage.googleapis.com/iexcloud-hl37opg/api/logos"
IEX_SECONDARY_LOGO_URL = "https://storage.googleapis.com/iex/api/logos"

# When IEX does not have a logo for a stock, it returns a 403 or returns a placeholder
# image with an ugly, wavy picture. The picture has a common MD5 hash that we can
# detect and work around.
IEX_PLACEHOLDER_IMAGE_HASH = "md5=ZLE6FlAxyV8t6arLO5AFeg=="


def get_stock_logo(symbol: str) -> str | None:
    """Get a stock logo like a honeybadger and never give up."""
    result = get_logo_iex(f"{IEX_PRIMARY_LOGO_URL}/{symbol}.png")

    if result:
        return result

    result = get_logo_iex(f"{IEX_SECONDARY_LOGO_URL}/{symbol}.png")

    if result:
        return result

    return get_logo_clearbit(symbol)


def get_base_domain(url: str) -> str:
    """Take a URL and get the base domain, such as example.com or example.co.uk."""
    return str(tld.get_fld(url, fix_protocol=True))


def get_logo_iex(url: str) -> str | None:
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


def website_for_symbol(symbol: str) -> str | None:
    """Convert a stock ticker to a website."""
    try:
        yf_obj = yfinance.Ticker(symbol)
        return str(yf_obj.info.get("website"))
    except requests.exceptions.HTTPError:
        return None


def get_logo_clearbit(symbol: str) -> str | None:
    """Get a logo using clearbit, which requires a domain name."""
    website = website_for_symbol(symbol)
    if not website:
        return None

    return f"https://logo.clearbit.com/{tld.get_fld(website)}"
