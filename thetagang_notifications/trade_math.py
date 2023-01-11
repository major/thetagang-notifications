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
