from typing import List
from sqlalchemy import String, Integer, BigInteger, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from .base import Base


class World(Base):
    __tablename__ = "worlds"

    id: Mapped[int] = mapped_column(primary_key=True)  # Primary key for the world

    # Unique identifier for the world
    uid: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        unique=True,
        index=True
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False)  # Version of the world
    net_time: Mapped[float] = mapped_column(Float, nullable=False)  # Network time of the world
    modified_time: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Last modified time (Unix timestamp in milliseconds)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # Name of the world
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Seed of the world
    seed_name: Mapped[str] = mapped_column(String(100), nullable=False)  # Seed name of the world

    # Timestamps for record keeping
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc)
    )

    # Relationship to chests
    chests: Mapped[List["Chest"]] = relationship(
        back_populates="world",
        cascade="all, delete-orphan"
    )
