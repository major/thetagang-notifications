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


def short_call_breakeven(strike, premium):
    """Return the breakeven on a short call."""
    return f"{float(strike) + premium:.2f}"


def short_put_breakeven(strike, premium):
    """Return the breakeven on a short put."""
    return f"{float(strike) - premium:.2f}"
