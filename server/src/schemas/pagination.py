from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List

# Generic type for paginated data
T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints.
    
    Use as a dependency in route handlers.
    """
    skip: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip (offset)"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of records to return"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.
    
    Includes metadata about pagination along with the data.
    """
    items: List[T]
    total: int = Field(description="Total number of items available")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Maximum items requested")
    has_more: bool = Field(description="Whether more items are available")
    
    @classmethod
    def create(cls, items: List[T], total: int, skip: int, limit: int):
        """
        Factory method to create a paginated response.
        
        Args:
            items: List of items for current page
            total: Total count of all items
            skip: Number of items skipped
            limit: Maximum items per page
            
        Returns:
            PaginatedResponse instance
        """
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total
        )
