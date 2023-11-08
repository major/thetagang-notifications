"""Exceptions used in this project."""


class AnnualizedReturnError(Exception):
    """Exception when we cannot calculate the annualized return."""

    def __init__(self, trade_type: str) -> None:
        """Initialize the exception."""
        super().__init__(f"Annualized return not available for: {trade_type}")


class BreakEvenError(Exception):
    """Exception when we cannot calculate the break even."""

    def __init__(self, trade_type: str) -> None:
        """Initialize the exception."""
        super().__init__(f"Break even not available for: {trade_type}")


class PotentialReturnError(Exception):
    """Exception when we cannot calculate the potential return."""

    def __init__(self, trade_type: str) -> None:
        """Initialize the exception."""
        super().__init__(f"Potential return not available for: {trade_type}")
