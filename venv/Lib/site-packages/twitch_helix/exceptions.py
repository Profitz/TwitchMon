class HelixError(Exception):
    pass


class HelixMissingParameter(HelixError):
    pass


class HelixInternalServerError(HelixError):
    pass


class HelixExpiredToken(HelixError):
    pass
