from typing import List
from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Chest(Base):
    __tablename__ = "chests"

    id: Mapped[int] = mapped_column(primary_key=True)  # Primary key for the chest

    # Foreign key to the world this chest belongs to
    world_id: Mapped[int] = mapped_column(
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    prefab_name: Mapped[str] = mapped_column(String(100), nullable=False)  # Prefab name of the chest
    creator_id: Mapped[int] = mapped_column(Integer, nullable=False)  # ID of the creator of the chest
    
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
