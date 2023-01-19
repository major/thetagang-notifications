"""Calculate different aspects of a trade."""


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


def put_break_even(strike, premium):
    """Return the break even on a put."""
    return strike - premium


def short_option_potential_return(strike, premium):
    """Return the potential return on a short option."""
    return round((premium / (strike - premium)) * 100, 2)
