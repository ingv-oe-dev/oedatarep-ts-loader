class TSLoaderException(Exception):
    """Exception raised for custom errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Default message."):
        self.message = message
        super().__init__(self.message)

class RecordMissingFiles(TSLoaderException):
    """
        Exception raised due to missing files in record definition
        (one between csv and json has not been loaded)
    """
    def __init__(self, message="No TS files found."):
        self.message = (f"No TS files (csv,json) "
                        f"in record definition.")
        super().__init__(self.message)

class HeaderFileMissing(TSLoaderException):
    """
        Exception raised when Header file is missing in record definition
        (only csv has been uploaded)
    """
    def __init__(self):
        self.message = (f"No .json file Header "
                        f"found in record definition for csv.")
        super().__init__(self.message)

class TSDataFileMissing(TSLoaderException):
    """
        Exception raised when TS DAta file is missing in record definition
        (only json has been uploaded)
    """
    def __init__(self):
        self.message = (f"No .csv file Data "
                        f"found in record definition for header.")
        super().__init__(self.message)
