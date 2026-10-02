class AuthenticationFailException(Exception):

    def __init__(self, message):
        super().__init__(message)

class DuplicateRequestException(Exception):

    def __init__(self, message):
        super().__init__(message)

class MissingHeadersException(Exception):

    def __init__(self, message):
        super().__init__(message)