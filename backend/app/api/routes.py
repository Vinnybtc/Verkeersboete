"""
API routes for the Verkeersboete agent.
"""

import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.models import Case, CaseStatus, Fine, User
from app.schemas.schemas import (
    AuthorizationRequest,
    CaseFullResponse,
    CaseResponse,
    FineExtracted,
    FineResponse,
    ProcessFineRequest,
    ProcessFineResponse,
    UserCreate,
    UserResponse,
)
from app.services.legal_agent import analyze_fine, format_legal_grounds
from app.services.ocr_service import process_document
from app.services.pdf_generator import generate_bezwaarschrift

logger = logging.getLogger(__name__)
router = APIRouter()


# --- User endpoints ---


@router.post("/users", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is al geregistreerd.")

    user = User(**user_data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden.")
    return user


@router.post("/users/authorize", response_model=UserResponse)
def authorize_user(auth: AuthorizationRequest, db: Session = Depends(get_db)):
    """Sign the authorization (machtiging) for a user."""
    user = db.query(User).filter(User.id == auth.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden.")

    user.authorization_signed = auth.signed
    user.authorization_date = datetime.utcnow() if auth.signed else None
    db.commit()
    db.refresh(user)
    return user


# --- Upload & Process endpoints ---


@router.post("/upload-fine", response_model=FineResponse)
async def upload_fine(
    user_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a traffic fine document (image or PDF).
    Performs OCR and extracts structured data.
    """
    # Validate user
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden.")

    # Validate file type
    allowed_types = {
        "image/jpeg", "image/png", "image/tiff",
        "application/pdf",
    }
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Ongeldig bestandstype: {file.content_type}. "
                   f"Toegestaan: JPEG, PNG, TIFF, PDF.",
        )

    # Save uploaded file
    settings.ensure_dirs()
    file_ext = Path(file.filename).suffix if file.filename else ".jpg"
    stored_filename = f"{uuid.uuid4().hex}{file_ext}"
    stored_path = str(Path(settings.upload_dir) / stored_filename)

    with open(stored_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run OCR
    try:
        extracted, raw_text, confidence = process_document(stored_path)
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR-verwerking mislukt: {str(e)}")

    # Parse overtreding_datum
    overtreding_dt = None
    if extracted.overtreding_datum:
        try:
            overtreding_dt = datetime.strptime(extracted.overtreding_datum, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Could not parse date: {extracted.overtreding_datum}")

    # Store fine in database
    fine = Fine(
        user_id=user.id,
        beschikkingsnummer=extracted.beschikkingsnummer,
        overtreding_datum=overtreding_dt,
        feitcode=extracted.feitcode,
        omschrijving=extracted.omschrijving,
        locatie=extracted.locatie,
        bedrag=extracted.bedrag,
        instantie=extracted.instantie,
        ocr_raw_text=raw_text,
        ocr_confidence=confidence,
        original_filename=file.filename,
        stored_filepath=stored_path,
    )
    db.add(fine)
    db.commit()
    db.refresh(fine)

    return fine


@router.post("/process-fine", response_model=ProcessFineResponse)
async def process_fine(
    fine_id: str,
    request: ProcessFineRequest,
    db: Session = Depends(get_db),
):
    """
    Full autonomous pipeline: analyze fine and generate bezwaarschrift.

    This endpoint orchestrates the complete process:
    1. Retrieve the uploaded fine data.
    2. Run legal analysis.
    3. Generate bezwaarschrift PDF.
    4. Create a case record for tracking.
    """
    # Validate user
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden.")

    if not user.authorization_signed:
        raise HTTPException(
            status_code=403,
            detail="Machtiging is vereist. Teken eerst de machtiging via /users/authorize.",
        )

    # Get fine
    fine = db.query(Fine).filter(Fine.id == uuid.UUID(fine_id)).first()
    if not fine:
        raise HTTPException(status_code=404, detail="Boete niet gevonden.")

    if fine.user_id != user.id:
        raise HTTPException(status_code=403, detail="Boete behoort niet tot deze gebruiker.")

    # Check for existing case
    existing_case = db.query(Case).filter(Case.fine_id == fine.id).first()
    if existing_case:
        raise HTTPException(
            status_code=400,
            detail="Er is al een zaak aangemaakt voor deze boete.",
        )

    # Build extracted data from stored fine
    extracted = FineExtracted(
        beschikkingsnummer=fine.beschikkingsnummer,
        overtreding_datum=fine.overtreding_datum.strftime("%Y-%m-%d") if fine.overtreding_datum else None,
        feitcode=fine.feitcode,
        omschrijving=fine.omschrijving,
        locatie=fine.locatie,
        bedrag=fine.bedrag,
        instantie=fine.instantie,
    )

    # Step 1: Legal Analysis
    try:
        analysis = analyze_fine(extracted, fine.ocr_raw_text or "")
    except Exception as e:
        logger.error(f"Legal analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Juridische analyse mislukt: {str(e)}")

    legal_grounds_text = format_legal_grounds(analysis)
    success_prob = analysis.get("slagingskans", 0.0)

    # Step 2: Generate bezwaarschrift PDF
    bezwaarschrift_path: Optional[str] = None
    if analysis.get("bezwaargronden"):
        try:
            user_info = {
                "name": user.name,
                "address": user.address or "",
                "postal_code": user.postal_code or "",
                "city": user.city or "",
                "email": user.email,
                "phone": user.phone or "",
            }
            bezwaarschrift_path = generate_bezwaarschrift(
                extracted, analysis, user_info
            )
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            # Non-fatal: continue without PDF

    # Step 3: Create case
    case = Case(
        user_id=user.id,
        fine_id=fine.id,
        status=CaseStatus.DOCUMENT_GENERATED if bezwaarschrift_path else CaseStatus.ANALYSIS_COMPLETE,
        legal_grounds=legal_grounds_text,
        success_probability=success_prob,
        analysis_summary=analysis.get("samenvatting", ""),
        bezwaarschrift_path=bezwaarschrift_path,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    return ProcessFineResponse(
        case_id=case.id,
        status=case.status.value,
        extracted_data=extracted,
        legal_analysis=legal_grounds_text,
        success_probability=success_prob,
        bezwaarschrift_path=bezwaarschrift_path,
        message="Boete succesvol geanalyseerd en bezwaarschrift gegenereerd."
        if bezwaarschrift_path
        else "Boete geanalyseerd. Geen voldoende gronden voor bezwaar gevonden.",
    )


# --- Case endpoints ---


@router.get("/cases/{case_id}", response_model=CaseFullResponse)
def get_case(case_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get full case details including fine and user info."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Zaak niet gevonden.")

    return CaseFullResponse(
        case=CaseResponse.model_validate(case),
        fine=FineResponse.model_validate(case.fine),
        user=UserResponse.model_validate(case.user),
    )


@router.get("/users/{user_id}/cases", response_model=list[CaseResponse])
def get_user_cases(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get all cases for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden.")

    cases = db.query(Case).filter(Case.user_id == user_id).all()
    return cases


@router.patch("/cases/{case_id}/status")
def update_case_status(
    case_id: uuid.UUID,
    status: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Update case status (for tracking submitted/won/lost)."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Zaak niet gevonden.")

    try:
        new_status = CaseStatus(status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Ongeldige status. Geldige waarden: {[s.value for s in CaseStatus]}",
        )

    case.status = new_status
    if notes:
        case.notes = notes
    if new_status == CaseStatus.SUBMITTED:
        case.submitted_at = datetime.utcnow()
    if new_status in (CaseStatus.WON, CaseStatus.LOST, CaseStatus.REJECTED):
        case.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(case)
    return {"message": f"Status bijgewerkt naar: {new_status.value}", "case_id": str(case.id)}
