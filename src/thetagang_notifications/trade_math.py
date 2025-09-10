"""Calculate different aspects of a trade."""

from datetime import datetime

from dateutil import parser


def breakeven(trade: dict) -> str | None:
    """Return the breakeven on a cash secured or naked put."""
    match trade["type"]:
        case "CASH SECURED PUT":
            strike = trade["short_put"]
            break_even = float(strike) - trade["price_filled"]
        case "COVERED CALL" | "SHORT NAKED CALL":
            strike = trade["short_call"]
            break_even = float(strike) + trade["price_filled"]
        case _:
            return None

    return f"{break_even:.2f}"


def days_to_expiration(expiration_date: str) -> int:
    """Return the days to expiration."""
    parsed_expiration = parse_expiration(expiration_date)
    # The thetagang website calculates DTEs with one extra day,
    # so add one more here to match.
    return int((parsed_expiration - datetime.now()).days + 1)


def parse_expiration(expiration_date: str) -> datetime:
    """Parse the expiration date."""
    return parser.parse(expiration_date, ignoretz=True)


def pretty_expiration(expiration_date: str) -> str:
    """Return the expiration date in a pretty format."""
    dte = days_to_expiration(expiration_date)
    expiration_format = "%-m/%d" if dte <= 365 else "%-m/%d/%y"
    return parse_expiration(expiration_date).strftime(expiration_format)


def pretty_strike(strike_price: float) -> str:
    """Return the options strike price in a friendly format.

    Report the number without decimals if it's an even number, like
    $388. Use decimals if it has a decimal, like $388.50.
    """
    strike_price = float(strike_price)
    return f"${strike_price:.0f}" if strike_price.is_integer() else f"${strike_price:.2f}"


def pretty_premium(premium: float) -> str:
    """Return the options premium in a friendly format.

    Premium should *always* have two decimals, even if it's an integer.
    """
    return f"${premium:.2f}"


def call_break_even(strike: float, premium: float) -> str:
    """Return the break even on a call."""
    return pretty_strike(strike + premium)


def put_break_even(strike: float, premium: float) -> str:
    """Return the break even on a put."""
    return pretty_strike(strike - premium)


def short_option_potential_return(strike: float, premium: float) -> float:
    """Return the potential return on a short option."""
    return round((premium / (strike - premium)) * 100, 2)


def short_annualized_return(strike: float, premium: float, days_left: int) -> float:
    """Get the annualized return on a short option."""
    short_potential_return = short_option_potential_return(strike, premium)
    # Use 1 for DTE if this is a same day trade.
    # Computers don't like dividing by 0.
    dte = max(days_left, 1)
    return round((short_potential_return / dte) * 365, 2)


def percentage_profit(winner: bool, wager: float, result: float) -> int:
    """Return the percentage profit/loss on a trade."""
    long_trade = wager > result
    match (winner, long_trade):
        case (True, True):
            # Winning long option trade.
            return int(((wager - result) / wager) * 100)
        case (True, False):
            # Winning short option trade.
            return int(((result - wager) / wager) * 100)
        case (False, True):
            # Losing long option trade.
            return int(((wager - result) / wager) * 100)
        case (False, False):
            # Losing short option trade.
            return int(((result - wager) / wager) * 100)
        case _:
            return 0
