"""Custom Exceptions for the ORM"""


class AugmentedRetrievalInvalidQueryError(ValueError):
    def __init__(self, query: str, details: str) -> None:
        """
        Indicates that an invalid query was generated for an augmented retrieval

        Keyword Arguments:
            query (str): The invalid query
            details (str): Details about why the query is invalid
        """
        super().__init__(f"{query} is not a valid query: {details}")


class MissingTableObjectAttributeError(ValueError):
    def __init__(self, attribute_name: str) -> None:
        """
        Indicates that a required attribute was not provided to a TableObject

        Keyword Arguments:
            attribute_name (str): The name of the attribute that was not provided
        """
        super().__init__(f"Required argument {attribute_name}, was not provided")


class TableScanQueryError(ValueError):
    def __init__(self, attribute_name: str, attribute_type: str) -> None:
        """
        Indicates that an invalid attribute_name was provided for a given attribute_type

        Keyword Arguments:
            attribute_name (str): The name of the attribute that was invalid
            attribute_type (str): The type of attribute that was invalid
        """
        super().__init__(f"{attribute_name} is not a valid {attribute_type}")


class TableScanInvalidComparisonError(TableScanQueryError):
    def __init__(self, comparison_name: str) -> None:
        """
        Raised when an invalid comparison operator was provided

        Keyword Arguments:
            comparison_name (str): The name of the invalid comparison operator
        """
        super().__init__(attribute_name=comparison_name, attribute_type="comparison operator")


class TableScanInvalidAttributeError(TableScanQueryError):
    def __init__(self, attribute_name: str) -> None:
        """
        Raised when attempting to scan using an invalid attribute

        Keyword Arguments:
            attribute_name (str): The name of the invalid attribute
        """
        super().__init__(attribute_name=attribute_name, attribute_type="table object attribute")


class TableScanMissingAttributeError(ValueError):
    def __init__(self, attribute_name: str) -> None:
        """
        Used when a attribute is missing from a table scan

        Keyword Arguments:
            attribute_name (str): The name of the missing attribute
        """
        super().__init__(f"{attribute_name} was not provided")
