from typing import Optional
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)  # Primary key for the item
    
    # ID of the chest this item belongs to
    chest_id: Mapped[int] = mapped_column(ForeignKey("chests.id", ondelete="CASCADE"), nullable=False)

    # Item names like "BlackMetalScrap"
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)  # Quantity of the item
    durability: Mapped[int] = mapped_column(Integer, nullable=False)  # Durability of the item
    quality: Mapped[int] = mapped_column(Integer, nullable=False)  # Quality of the item

    # Position of the item within the chest
    position_x: Mapped[int] = mapped_column(Integer, nullable=False)
    position_y: Mapped[int] = mapped_column(Integer, nullable=False)

    equipped: Mapped[bool] = mapped_column(nullable=False)  # Whether the item is equipped
    variant: Mapped[int] = mapped_column(Integer, nullable=False)  # Variant of the item
    crafter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # ID of the crafter
    
    # Optional: Name of the crafter
    crafter_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, default=None)

    # Relationship to chest
    chest: Mapped["Chest"] = relationship(back_populates="items")
