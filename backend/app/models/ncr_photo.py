"""NCR Photo model for mobile NCR photo attachments."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class NCRPhoto(Base):
    """NCR photo attachment model for mobile quality inspections."""

    __tablename__ = "ncr_photos"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    ncr_id = Column(Integer, ForeignKey("ncr_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    photo_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # MinIO storage path
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)  # e.g., image/jpeg, image/png
    caption = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    organization = relationship("Organization", back_populates="ncr_photos")
    ncr_report = relationship("NCRReport", back_populates="photos")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<NCRPhoto(id={self.id}, ncr_id={self.ncr_id}, name='{self.photo_name}')>"

    @property
    def file_size_mb(self) -> float:
        """Return file size in megabytes."""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0.0

    @property
    def is_image(self) -> bool:
        """Check if file is an image type."""
        if self.mime_type:
            return self.mime_type.startswith('image/')
        return False
