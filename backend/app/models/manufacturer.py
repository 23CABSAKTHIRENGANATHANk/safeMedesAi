import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    name = Column(Text, nullable=False, unique=True, index=True)
    country = Column(Text, nullable=True)
    license_number = Column(Text, nullable=True, unique=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # No direct ORM relationship defined to avoid join/foreign-key issues
    # (medicine records are stored separately in `medicine_records`).

    def __repr__(self):
        return f"<Manufacturer id={self.id} name={self.name!r}>"
