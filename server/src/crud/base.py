from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel

from ..models.base import Base
from ..logging_config import get_logger

logger = get_logger(__name__)

# Type variables for generic CRUD operations
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for CRUD operations.
    
    Provides generic Create, Read, Update, Delete operations that can be
    inherited by specific entity CRUD classes.
    
    Type Parameters:
        ModelType: The SQLAlchemy model class
        CreateSchemaType: The Pydantic schema for creating objects
        UpdateSchemaType: The Pydantic schema for updating objects
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD object with a model class.
        
        Args:
            model: A SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Retrieve a single record by ID.
        
        Args:
            db: Database session
            id: Primary key value
            
        Returns:
            Model instance or None if not found
        """
        return db.get(self.model, id)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Retrieve multiple records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
        """
        stmt = select(self.model).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get_all(self, db: Session) -> List[ModelType]:
        """
        Retrieve all records.
        
        Args:
            db: Database session
            
        Returns:
            List of all model instances
        """
        return list(db.scalars(select(self.model)).all())

    def count(self, db: Session) -> int:
        """
        Count total number of records.
        
        Args:
            db: Database session
            
        Returns:
            Total count of records
        """
        stmt = select(func.count()).select_from(self.model)
        return db.scalar(stmt) or 0

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Pydantic schema with creation data
            
        Returns:
            Created model instance
        """
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.flush()
        logger.debug(f"Created {self.model.__name__} record")
        return db_obj

    def create_bulk(
        self, db: Session, *, objs_in: List[CreateSchemaType]
    ) -> List[ModelType]:
        """
        Create multiple records in bulk.
        
        Args:
            db: Database session
            objs_in: List of Pydantic schemas with creation data
            
        Returns:
            List of created model instances
        """
        db_objs = [self.model(**obj.model_dump()) for obj in objs_in]
        db.add_all(db_objs)
        db.flush()
        logger.debug(f"Bulk created {len(db_objs)} {self.model.__name__} records")
        return db_objs

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """
        Update an existing record.
        
        Args:
            db: Database session
            db_obj: Existing model instance to update
            obj_in: Pydantic schema or dict with update data
            
        Returns:
            Updated model instance
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.flush()
        return db_obj

    def delete(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """
        Delete a record by ID.
        
        Args:
            db: Database session
            id: Primary key value
            
        Returns:
            Deleted model instance or None if not found
        """
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.flush()
            logger.debug(f"Deleted {self.model.__name__} record with ID: {id}")
        else:
            logger.debug(f"{self.model.__name__} record not found for deletion: {id}")
        return obj
