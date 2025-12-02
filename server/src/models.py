from typing import Optional, List
from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Chest(Base):
    __tablename__ = "chests"

    id: Mapped[int] = mapped_column(primary_key=True)
    prefab_name: Mapped[str] = mapped_column(String(100), nullable=False)
    creator_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Position - stored as separate columns for x, y, z
    position_x: Mapped[float] = mapped_column(Float, nullable=False)
    position_y: Mapped[float] = mapped_column(Float, nullable=False)
    position_z: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Sector - stored as separate columns for x, y
    sector_x: Mapped[int] = mapped_column(Integer, nullable=False)
    sector_y: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Rotation - stored as separate columns for x, y, z
    rotation_x: Mapped[float] = mapped_column(Float, nullable=False)
    rotation_y: Mapped[float] = mapped_column(Float, nullable=False)
    rotation_z: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationship to items
    items: Mapped[List["Item"]] = relationship(back_populates="chest", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # ID of the chest this item belongs to
    chest_id: Mapped[int] = mapped_column(ForeignKey("chests.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False,  index=True) # Item names like "BlackMetalScrap"
    quantity: Mapped[int] = mapped_column(Integer, nullable=False) # Quantity of the item
    durability: Mapped[int] = mapped_column(Integer, nullable=False) # Durability of the item
    quality: Mapped[int] = mapped_column(Integer, nullable=False) # Quality of the item
    
    # Position of the item within the chest
    position_x: Mapped[int] = mapped_column(Integer, nullable=False)
    position_y: Mapped[int] = mapped_column(Integer, nullable=False)

    equipped: Mapped[bool] = mapped_column(nullable=False) # Whether the item is equipped
    variant: Mapped[int] = mapped_column(Integer, nullable=False) # Variant of the item
    crafter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0) # ID of the crafter
    crafter_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, default=None) # Name of the crafter

    # Relationship to chest
    chest: Mapped["Chest"] = relationship(back_populates="items")
