class SmscApiError(Exception):
    """Raised if SMSC API response status is not 200 or it has "ERROR" in response."""

    pass
