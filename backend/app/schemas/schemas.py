from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


# --- User schemas ---

class UserCreate(BaseModel):
    name: str
    email: str
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    address: Optional[str]
    postal_code: Optional[str]
    city: Optional[str]
    phone: Optional[str]
    authorization_signed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthorizationRequest(BaseModel):
    user_id: UUID
    signed: bool


# --- Fine schemas ---

class FineExtracted(BaseModel):
    beschikkingsnummer: Optional[str] = None
    overtreding_datum: Optional[str] = None
    feitcode: Optional[str] = None
    omschrijving: Optional[str] = None
    locatie: Optional[str] = None
    bedrag: Optional[float] = None
    instantie: Optional[str] = None


class FineResponse(BaseModel):
    id: UUID
    user_id: UUID
    beschikkingsnummer: Optional[str]
    overtreding_datum: Optional[datetime]
    feitcode: Optional[str]
    omschrijving: Optional[str]
    locatie: Optional[str]
    bedrag: Optional[float]
    instantie: Optional[str]
    ocr_confidence: Optional[float]
    original_filename: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Case schemas ---

class CaseResponse(BaseModel):
    id: UUID
    user_id: UUID
    fine_id: UUID
    status: str
    legal_grounds: Optional[str]
    success_probability: Optional[float]
    analysis_summary: Optional[str]
    bezwaarschrift_path: Optional[str]
    submitted_at: Optional[datetime]
    resolved_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseFullResponse(BaseModel):
    case: CaseResponse
    fine: FineResponse
    user: UserResponse


# --- Process request ---

class ProcessFineRequest(BaseModel):
    user_id: UUID


class ProcessFineResponse(BaseModel):
    case_id: UUID
    status: str
    extracted_data: FineExtracted
    legal_analysis: str
    success_probability: float
    bezwaarschrift_path: Optional[str]
    message: str
