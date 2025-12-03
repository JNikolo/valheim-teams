from typing import Optional, List
from sqlalchemy import String, Integer, BigInteger, Float, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, timezone
class Base(DeclarativeBase):
    pass

class Chest(Base):
    __tablename__ = "chests"

    id: Mapped[int] = mapped_column(primary_key=True) # Primary key for the chest

    # Foreign key to the world this chest belongs to
    world_id: Mapped[int] = mapped_column(
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    prefab_name: Mapped[str] = mapped_column(String(100), nullable=False) # Prefab name of the chest
    creator_id: Mapped[int] = mapped_column(Integer, nullable=False) # ID of the creator of the chest
    
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
    # Relationship to world
    world: Mapped["World"] = relationship(back_populates="chests")

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True) # Primary key for the item
    
    # ID of the chest this item belongs to
    chest_id: Mapped[int] = mapped_column(ForeignKey("chests.id", ondelete="CASCADE"), nullable=False)

    # Item names like "BlackMetalScrap"
    name: Mapped[str] = mapped_column(String(200), nullable=False,  index=True)
    
    quantity: Mapped[int] = mapped_column(Integer, nullable=False) # Quantity of the item
    durability: Mapped[int] = mapped_column(Integer, nullable=False) # Durability of the item
    quality: Mapped[int] = mapped_column(Integer, nullable=False) # Quality of the item

    # Position of the item within the chest
    position_x: Mapped[int] = mapped_column(Integer, nullable=False)
    position_y: Mapped[int] = mapped_column(Integer, nullable=False)

    equipped: Mapped[bool] = mapped_column(nullable=False) # Whether the item is equipped
    variant: Mapped[int] = mapped_column(Integer, nullable=False) # Variant of the item
    crafter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0) # ID of the crafter
    
    # Optional: Name of the crafter
    crafter_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, default=None)

    # Relationship to chest
    chest: Mapped["Chest"] = relationship(back_populates="items")

class World(Base):
    __tablename__ = "worlds"

    id: Mapped[int] = mapped_column(primary_key=True) # Primary key for the world

    # Unique identifier for the world
    uid: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        unique=True,
        index=True
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False) # Version of the world
    net_time: Mapped[float] = mapped_column(Float, nullable=False) # Network time of the world
    modified_time: Mapped[int] = mapped_column(BigInteger, nullable=False) # Last modified time (Unix timestamp in milliseconds)
    name: Mapped[str] = mapped_column(String(100), nullable=False) # Name of the world
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False) # Seed of the world
    seed_name: Mapped[str] = mapped_column(String(100), nullable=False) # Seed name of the world

    # Timestamps for record keeping
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable = False,
        default = datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable = False,
        default = datetime.now(timezone.utc),
        onupdate = datetime.now(timezone.utc)
    )

    # Relationship to chests
    chests: Mapped[List["Chest"]] = relationship(
        back_populates="world",
        cascade="all, delete-orphan"
    )
