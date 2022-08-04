class TSLoaderException(Exception):
    """Exception raised for custom errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Default message."):
        self.message = message
        super().__init__(self.message)
