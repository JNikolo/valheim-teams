"""
Custom exceptions for the Valheim Teams API.

Provides specific exception types for different error scenarios,
enabling better error handling and more informative error messages.
"""


class ValheimAPIException(Exception):
    """
    Base exception for all Valheim API errors.
    
    All custom exceptions should inherit from this base class.
    This allows for easy catching of all API-related errors.
    """
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ResourceNotFoundError(ValheimAPIException):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: int | str):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, status_code=404)
        self.resource_type = resource_type
        self.resource_id = resource_id


class WorldNotFoundError(ResourceNotFoundError):
    """Raised when a world is not found."""
    def __init__(self, world_id: int | str):
        super().__init__("World", world_id)


class ChestNotFoundError(ResourceNotFoundError):
    """Raised when a chest is not found."""
    def __init__(self, chest_id: int):
        super().__init__("Chest", chest_id)


class ItemNotFoundError(ResourceNotFoundError):
    """Raised when an item is not found."""
    def __init__(self, item_id: int):
        super().__init__("Item", item_id)


class WorldNotNewerError(ValheimAPIException):
    """Raised when uploaded world save is not newer than existing one."""
    def __init__(self, upload_net_time: float, existing_net_time: float):
        message = (
            f"Uploaded save is not newer than existing world. "
            f"Upload net_time: {upload_net_time}, "
            f"Existing net_time: {existing_net_time}"
        )
        super().__init__(message, status_code=400)
        self.upload_net_time = upload_net_time
        self.existing_net_time = existing_net_time


class InvalidFileFormatError(ValheimAPIException):
    """Raised when an uploaded file has an invalid format."""
    def __init__(self, file_type: str, details: str | None = None):
        message = f"Invalid {file_type} file format"
        if details:
            message += f": {details}"
        super().__init__(message, status_code=422)
        self.file_type = file_type


class DatabaseError(ValheimAPIException):
    """Raised when a database operation fails."""
    def __init__(self, operation: str, details: str | None = None):
        message = f"Database operation failed: {operation}"
        if details:
            message += f" - {details}"
        super().__init__(message, status_code=500)
        self.operation = operation


class ParsingError(ValheimAPIException):
    """Raised when parsing Valheim save files fails."""
    def __init__(self, file_type: str, details: str | None = None):
        message = f"Failed to parse {file_type} file"
        if details:
            message += f": {details}"
        super().__init__(message, status_code=422)
        self.file_type = file_type