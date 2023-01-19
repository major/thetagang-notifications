"""Calculate different aspects of a trade."""
from datetime import datetime

from dateutil import parser


def breakeven(trade):
    """Return the breakeven on a cash secured or naked put."""
    match trade["type"]:
        case "CASH SECURED PUT":
            strike = trade["short_put"]
            breakeven = float(strike) - trade["price_filled"]
        case "COVERED CALL" | "SHORT NAKED CALL":
            strike = trade["short_call"]
            breakeven = float(strike) + trade["price_filled"]
        case _:
            return None

    return f"{breakeven:.2f}"


def call_break_even(strike, premium):
    """Return the break even on a call."""
    return strike + premium


def days_to_expiration(expiration_date):
    """Return the days to expiration."""
    parsed_expiration = parse_expiration(expiration_date)
    # The thetagang website calculates DTEs with one extra day,
    # so add one more here to match.
    return (parsed_expiration - datetime.now()).days + 1


def parse_expiration(expiration_date):
    """Parse the expiration date."""
    return parser.parse(expiration_date, ignoretz=True)


def pretty_expiration(expiration_date):
    """Return the expiration date in a pretty format."""
    dte = days_to_expiration(expiration_date)
    expiration_format = "%-m/%d" if dte <= 365 else "%-m/%d/%y"
    return parse_expiration(expiration_date).strftime(expiration_format)


def put_break_even(strike, premium):
    """Return the break even on a put."""
    return strike - premium


def short_option_potential_return(strike, premium):
    """Return the potential return on a short option."""
    return round((premium / (strike - premium)) * 100, 2)


def short_annualized_return(strike, premium, days_to_expiration):
    """Get the annualized return on a short option."""
    short_potential_return = short_option_potential_return(strike, premium)
    # Use 1 for DTE if this is a same day trade.
    # Computers don't like dividing by 0.
    dte = max(days_to_expiration, 1)
    return round((short_potential_return / dte) * 365, 2)
