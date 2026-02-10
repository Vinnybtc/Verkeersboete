import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class CaseStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    OCR_COMPLETE = "ocr_complete"
    ANALYSIS_COMPLETE = "analysis_complete"
    DOCUMENT_GENERATED = "document_generated"
    SUBMITTED = "submitted"
    WON = "won"
    LOST = "lost"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    address = Column(Text, nullable=True)
    postal_code = Column(String(10), nullable=True)
    city = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    authorization_signed = Column(Boolean, default=False)
    authorization_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    fines = relationship("Fine", back_populates="user")
    cases = relationship("Case", back_populates="user")


class Fine(Base):
    __tablename__ = "fines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Extracted fields from CJIB document
    beschikkingsnummer = Column(String(50), nullable=True)
    overtreding_datum = Column(DateTime, nullable=True)
    feitcode = Column(String(20), nullable=True)
    omschrijving = Column(Text, nullable=True)
    locatie = Column(String(500), nullable=True)
    bedrag = Column(Float, nullable=True)
    instantie = Column(String(255), nullable=True)

    # Raw OCR data
    ocr_raw_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)

    # File reference
    original_filename = Column(String(255), nullable=True)
    stored_filepath = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="fines")
    case = relationship("Case", back_populates="fine", uselist=False)


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    fine_id = Column(UUID(as_uuid=True), ForeignKey("fines.id"), unique=True, nullable=False)

    status = Column(Enum(CaseStatus), default=CaseStatus.UPLOADED)

    # Legal analysis results
    legal_grounds = Column(Text, nullable=True)
    success_probability = Column(Float, nullable=True)
    analysis_summary = Column(Text, nullable=True)

    # Generated documents
    bezwaarschrift_path = Column(String(500), nullable=True)

    # Tracking
    submitted_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="cases")
    fine = relationship("Fine", back_populates="case")
