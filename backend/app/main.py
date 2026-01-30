"""
CarbonChain MVP - FastAPI Application

Minimal API layer for climate action claim submission and verification.
Includes human governance layer for trust and transparency.
Includes evidence & provenance system for auditability.
Uses in-memory storage for MVP demonstration purposes.

GOVERNANCE FLOW:
1. Submit claim → SUBMITTED
2. AI analysis → AI_ANALYZED (creates SYSTEM_AI evidence, analysis completed, not approved)
3. Authority review → AUTHORITY_REVIEWED (or REJECTED)
4. Community review → COMMUNITY_REVIEWED (or REJECTED)
5. Mint credits → MINTED (only if both reviews approved)

EVIDENCE SYSTEM:
- All verification and review actions create immutable evidence records
- Evidence includes SHA256 hashes for integrity verification
- Evidence is publicly accessible for transparency
"""

import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.app.models.ai_verdict import AIConsistencyResult
from backend.app.models.claim import Claim, ClaimStatus, ClaimSubmission
from backend.app.models.evidence import (
    Evidence,
    EvidenceSubmission,
    EvidenceSummary,
    EvidenceType,
)
from backend.app.models.monitoring import MonitoringRun
from backend.app.models.review import (
    MintedCredit,
    ReviewRecord,
    ReviewSubmission,
)
from backend.app.models.transparency import TransparencyReport
from backend.app.models.verification import (
    VerificationRequest,
    VerificationResult,
)
from backend.app.services import (
    ai_consistency_service,
    claim_service,
    credit_monitoring_service,
    evidence_service,
    review_service,
    transparency_service,
    verification_service,
)

# -----------------------------------------------------------------------------#
# File upload configuration
# -----------------------------------------------------------------------------#
DATA_DIR = Path("data")
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB per file
ALLOWED_IMAGE_EXTS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_VIDEO_EXTS = {"mp4", "mov", "webm"}
ALLOWED_EXTS = ALLOWED_IMAGE_EXTS | ALLOWED_VIDEO_EXTS


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------
class PublicClaimResponse(BaseModel):
    """
    Public view of a claim with verification, review, and evidence details.

    This response provides full transparency into the governance process,
    including immutable evidence records with integrity hashes.
    """

    claim: Claim
    verification: Optional[VerificationResult] = None
    authority_review: Optional[ReviewRecord] = None
    community_review: Optional[ReviewRecord] = None
    minted_credit: Optional[MintedCredit] = None
    evidence: list[EvidenceSummary] = []
    status: ClaimStatus
    can_mint: bool = False
    mint_eligibility_reason: str = ""
    # AI Claim Consistency Verdict (public transparency)
    ai_verdict: Optional[AIConsistencyResult] = None
    # Credit Lifecycle Integrity (post-mint monitoring)
    credit_status: Optional[str] = None  # CreditStatus value if credit exists
    credit_remaining_co2e: Optional[float] = None  # Remaining CO2e if credit exists
    monitoring_history: list[MonitoringRun] = []  # Monitoring runs for the credit


class MintRequest(BaseModel):
    """Request to mint carbon credits for a verified claim."""

    claim_id: UUID = Field(..., description="ID of the claim to mint credits for")
    amount_tonnes_co2e: float = Field(
        ..., ge=0, description="Amount of CO2e to mint (typically from verified impact)"
    )


class MonitoringRequest(BaseModel):
    """Request to run post-mint monitoring for a credit."""

    claim_id: UUID = Field(
        ..., description="ID of the claim associated with the credit"
    )


class AuthorityGeometrySubmission(BaseModel):
    """Authority-defined geometry replacement."""

    geometry_geojson: dict = Field(
        ...,
        description="GeoJSON Polygon or MultiPolygon representing authority-defined boundary.",
    )


# -----------------------------------------------------------------------------
# FastAPI Application
# -----------------------------------------------------------------------------
app = FastAPI(
    title="CarbonChain MVP",
    description="Climate action claim submission and verification platform",
    version="0.1.0",
)

# -----------------------------------------------------------------------------
# CORS Middleware (MVP demo - allow all origins)
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files (read-only)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    """Root endpoint - health check."""
    return {"status": "ok", "message": "CarbonChain MVP API is running"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "CarbonChain MVP"}


@app.post("/debug/claims-raw")
async def debug_claim_raw(payload: dict):
    """Debug endpoint to test raw payload acceptance without Pydantic validation."""
    return payload


@app.post(
    "/claims",
    response_model=Claim,
    status_code=status.HTTP_201_CREATED,
)
def create_claim(
    payload: dict,
    background_tasks: BackgroundTasks,
) -> Claim:
    """
    Submit a new climate action claim.

    Creates a Claim object from the submission, assigns a unique ID,
    sets initial status to SUBMITTED, and stores it in memory.
    
    ORCHESTRATION: After claim creation, automatically triggers AI MRV verification
    in the background. This ensures:
    - Claim status progresses from SUBMITTED → AI_ANALYZED
    - SYSTEM_AI evidence is created automatically
    - AI consistency verdict is generated
    - Claim becomes visible in authority dashboard

    Args:
        submission: The claim submission data from the claimant.
        background_tasks: FastAPI background task handler for async verification.

    Returns:
        The created Claim object with system-generated fields populated.
    """
    # STEP 3: Force manual Pydantic validation for definitive error reporting
    try:
        submission = ClaimSubmission.model_validate(payload)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Pydantic validation failed: {str(e)}"
        )
    
    try:
        claim = claim_service.create_claim(submission)
        
        # ORCHESTRATION FIX: Set status to AI_ANALYSIS_PENDING immediately
        # This allows frontend to show "AI analysis pending" state
        # Claim creation returns immediately, AI MRV runs in background
        claim.status = ClaimStatus.AI_ANALYSIS_PENDING
        claim.updated_at = datetime.utcnow()
        
        # ORCHESTRATION FIX: Automatically trigger AI MRV verification after claim creation
        # This runs in the background to avoid blocking the HTTP response
        # The verification will:
        # 1. Update status to AI_ANALYSIS_IN_PROGRESS
        # 2. Run real Earth Engine NDVI computation
        # 3. Compute real CO₂ estimates
        # 4. Update claim.status to AI_VERIFIED
        # 5. Create SYSTEM_AI evidence records with real data
        # 6. Generate AI consistency verdict with real values
        # 7. Make claim visible in authority dashboard
        background_tasks.add_task(_trigger_ai_verification, claim.id)
        
        print(f"[ORCHESTRATION] Claim {claim.id} created. Status: {claim.status.value}. AI verification queued in background.")
        
        return claim
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

def _trigger_ai_verification(claim_id: UUID) -> None:
    """
    Background task to trigger AI MRV verification for a newly created claim.
    
    ORCHESTRATION: This function is called automatically after claim creation.
    It ensures the AI verification pipeline runs without blocking the HTTP response.
    
    SAFETY GUARDS:
    - Prevents double verification by checking claim status
    - Logs verification start and completion
    - Handles errors gracefully (logs but doesn't crash)
    
    Args:
        claim_id: The UUID of the claim to verify.
    """
    try:
        # Get the claim (it should exist since we just created it)
        claim = claim_service.get_claim_by_id(claim_id)
        if claim is None:
            print(f"[ORCHESTRATION ERROR] Claim {claim_id} not found for verification")
            return
        
        # SAFETY GUARD: Prevent double verification
        # Only verify if claim is in SUBMITTED, AI_ANALYSIS_PENDING, or AI_ANALYSIS_IN_PROGRESS status
        if claim.status not in (ClaimStatus.SUBMITTED, ClaimStatus.AI_ANALYSIS_PENDING, ClaimStatus.AI_ANALYSIS_IN_PROGRESS):
            print(f"[ORCHESTRATION] Claim {claim_id} already verified (status: {claim.status.value}). Skipping.")
            return
        
        # Update status to IN_PROGRESS before starting computation
        claim.status = ClaimStatus.AI_ANALYSIS_IN_PROGRESS
        claim.updated_at = datetime.utcnow()
        print(f"[ORCHESTRATION] Starting AI MRV verification for claim {claim_id}...")
        
        # Trigger the existing verification service
        # This will:
        # 1. Create VerificationResult (APPROVED or REJECTED based on CO₂ estimate)
        # 2. Update claim.status to AI_VERIFIED (positive impact) or AI_REJECTED (negative/zero impact)
        # 3. Create SYSTEM_AI evidence (MRV analysis) - ALWAYS, even on failure
        # 4. Generate AI consistency verdict (only for approved claims)
        # 5. Create SYSTEM_AI evidence (consistency verdict) - only for approved claims
        verification = verification_service.verify_claim(claim)
        
        # ORCHESTRATION COMPLETION GUARANTEE: Claim must exit AI analysis stage
        # Status should now be AI_VERIFIED or AI_REJECTED (never stuck in pending/in_progress)
        if claim.status not in (ClaimStatus.AI_VERIFIED, ClaimStatus.AI_REJECTED):
            print(f"[ORCHESTRATION ERROR] Claim {claim_id} did not exit AI analysis stage. Current status: {claim.status.value}")
            # Force transition to rejected if somehow stuck
            claim.status = ClaimStatus.AI_REJECTED
            claim.updated_at = datetime.utcnow()
        
        print(f"[ORCHESTRATION] AI MRV verification completed for claim {claim_id}. "
              f"Status: {claim.status.value}, Outcome: {verification.outcome.value}, Verification ID: {verification.id}")
        
    except Exception as e:
        # ORCHESTRATION ERROR HANDLING: Ensure claim exits AI analysis stage even on exception
        # Log error and transition to rejected state to prevent infinite pending
        print(f"[ORCHESTRATION ERROR] Failed to verify claim {claim_id}: {str(e)}")
        print(f"[ORCHESTRATION ERROR] Exception type: {type(e).__name__}")
        print(f"[ORCHESTRATION ERROR] Stack trace:\n{traceback.format_exc()}")
        
        # Get claim again to ensure we have latest state
        claim = claim_service.get_claim_by_id(claim_id)
        if claim and claim.status in (ClaimStatus.AI_ANALYSIS_PENDING, ClaimStatus.AI_ANALYSIS_IN_PROGRESS):
            # Force transition to rejected to unblock frontend
            claim.status = ClaimStatus.AI_REJECTED
            claim.updated_at = datetime.utcnow()
            print(f"[ORCHESTRATION ERROR] Claim {claim_id} forced to AI_REJECTED due to verification error")


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent traversal and strip directories."""
    name = Path(filename).name  # drop any path components
    # Replace spaces and restrict to safe characters
    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in {"-", "_", ".", " "}).strip()
    return safe_name.replace(" ", "_") or "upload"


def _ext_allowed(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTS


def _is_video(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_VIDEO_EXTS


async def _persist_upload(file: UploadFile, dest: Path) -> int:
    """
    Stream file content to disk with size enforcement.

    Returns:
        Total bytes written.
    """
    total = 0
    with dest.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)  # 1MB chunks to avoid memory bloat
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File {file.filename} exceeds max size of 50MB",
                )
            out.write(chunk)
    return total


@app.post(
    "/claims/{claim_id}/evidence/upload",
    response_model=list[Evidence],
    status_code=status.HTTP_201_CREATED,
)
async def upload_claim_evidence(
    claim_id: UUID, files: List[UploadFile] = File(...)
) -> list[Evidence]:
    """
    Upload one or more media files as claimant evidence.

    - Accepts multipart/form-data with field name "files"
    - Supports images (jpg, jpeg, png, webp) and videos (mp4, mov, webm)
    - Stores files under data/uploads/claims/{claim_id}/ with UUID prefix
    - Creates immutable USER_UPLOAD evidence records (confidence_weight=0.6)
    """
    claim = claim_service.get_claim_by_id(claim_id)
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found",
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files uploaded. Use field name 'files'.",
        )

    claim_dir = UPLOAD_DIR / "claims" / str(claim_id)
    claim_dir.mkdir(parents=True, exist_ok=True)

    created: list[Evidence] = []

    for upload in files:
        safe_name = _sanitize_filename(upload.filename or "upload")
        if not safe_name or not _ext_allowed(safe_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed for {upload.filename}. Allowed: {', '.join(sorted(ALLOWED_EXTS))}",
            )

        new_name = f"{uuid4()}_{safe_name}"
        dest_path = claim_dir / new_name

        await _persist_upload(upload, dest_path)

        is_video = _is_video(safe_name)
        title = "Claimant-uploaded video" if is_video else "Claimant-uploaded photo"
        data_ref = f"/uploads/claims/{claim_id}/{new_name}"

        submission = EvidenceSubmission(
            claim_id=claim_id,
            type=EvidenceType.USER_UPLOAD,
            source="claimant",
            title=title,
            description="User-submitted visual evidence for claim verification",
            data_ref=data_ref,
            confidence_weight=0.6,
        )
        created.append(evidence_service.create_evidence(submission))

    return created


@app.get(
    "/claims",
    response_model=list[Claim],
)
def list_claims() -> list[Claim]:
    """
    List all claims in memory.

    Returns:
        A list of all Claim objects currently stored.
    """
    return list(claim_service.claims_db.values())


@app.put(
    "/claims/{claim_id}/geometry/authority",
    response_model=Claim,
)
def replace_claim_geometry_authority(
    claim_id: UUID, submission: AuthorityGeometrySubmission
) -> Claim:
    """
    Replace claim geometry with an authority-defined polygon.

    Geometry is validated and stored as POLYGON with AUTHORITY_DEFINED source.
    """
    claim = claim_service.get_claim_by_id(claim_id)
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found",
        )
    try:
        return claim_service.update_claim_geometry_authority(
            claim_id, submission.geometry_geojson
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.get(
    "/claims/{claim_id}",
    response_model=Claim,
)
def get_claim(claim_id: UUID) -> Claim:
    """
    Retrieve a claim by its unique ID.

    Args:
        claim_id: The UUID of the claim to retrieve.

    Returns:
        The Claim object if found.

    Raises:
        HTTPException: 404 if claim not found.
    """
    claim = claim_service.get_claim_by_id(claim_id)
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found",
        )
    return claim


@app.post(
    "/verify",
    response_model=VerificationResult,
    status_code=status.HTTP_201_CREATED,
)
def verify_claim(request: VerificationRequest) -> VerificationResult:
    """
    Verify a climate action claim (mock implementation).

    This MVP endpoint simulates verification by:
    - Creating a VerificationResult with COMPLETED status and APPROVED outcome
    - Generating a mock verified carbon impact based on the claim's estimate
    - Updating the claim's status to VERIFIED

    Args:
        request: The verification request containing the claim ID.

    Returns:
        The VerificationResult with mock verification data.

    Raises:
        HTTPException: 404 if the referenced claim is not found.
    """
    claim = claim_service.get_claim_by_id(request.claim_id)
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {request.claim_id} not found",
        )
    return verification_service.verify_claim(claim)


@app.get(
    "/verifications/{verification_id}",
    response_model=VerificationResult,
)
def get_verification(verification_id: UUID) -> VerificationResult:
    """
    Retrieve a verification result by its unique ID.

    Args:
        verification_id: The UUID of the verification to retrieve.

    Returns:
        The VerificationResult object if found.

    Raises:
        HTTPException: 404 if verification not found.
    """
    verification = verification_service.get_verification_by_id(verification_id)
    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification with id {verification_id} not found",
        )
    return verification


@app.get(
    "/public/claims/{claim_id}",
    response_model=PublicClaimResponse,
)
def get_public_claim(claim_id: UUID) -> PublicClaimResponse:
    """
    Public view of a claim with verification and review details.

    This endpoint provides transparency into the full governance process:
    - AI verification results
    - Authority (government/regulator) review
    - Community (NGO/public) review
    - Minting status

    Args:
        claim_id: The UUID of the claim to retrieve.

    Returns:
        A combined view of the claim, verification, reviews, and status.

    Raises:
        HTTPException: 404 if claim not found.
    """
    claim = claim_service.get_claim_by_id(claim_id)
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found",
        )

    verification = None
    if claim.verification_id is not None:
        verification = verification_service.get_verification_by_id(
            claim.verification_id
        )

    # Get reviews
    authority_reviews = review_service.get_reviews_by_claim(
        claim_id, role=review_service.ReviewRole.AUTHORITY
    )
    community_reviews = review_service.get_reviews_by_claim(
        claim_id, role=review_service.ReviewRole.COMMUNITY
    )

    authority_review = authority_reviews[0] if authority_reviews else None
    community_review = community_reviews[0] if community_reviews else None

    # Get minted credit if any
    minted_credit = review_service.get_minted_credit_by_claim(claim_id)

    # Check mint eligibility
    can_mint, mint_reason = review_service.can_mint_credits(claim_id)

    # Get evidence summaries (includes hashes for integrity verification)
    evidence_summaries = evidence_service.get_evidence_summaries_for_claim(claim_id)

    # Get AI consistency verdict (if available)
    ai_verdict = ai_consistency_service.get_consistency_result_by_claim_id(claim_id)

    # Get credit lifecycle information (if credit exists)
    credit_status = None
    credit_remaining_co2e = None
    monitoring_history = []
    if minted_credit:
        credit_status = minted_credit.status.value
        credit_remaining_co2e = minted_credit.remaining_tonnes_co2e
        monitoring_history = credit_monitoring_service.get_monitoring_runs_by_claim(
            claim_id
        )

    return PublicClaimResponse(
        claim=claim,
        verification=verification,
        authority_review=authority_review,
        community_review=community_review,
        minted_credit=minted_credit,
        evidence=evidence_summaries,
        status=claim.status,
        can_mint=can_mint,
        mint_eligibility_reason=mint_reason,
        ai_verdict=ai_verdict,
        credit_status=credit_status,
        credit_remaining_co2e=credit_remaining_co2e,
        monitoring_history=monitoring_history,
    )


# -----------------------------------------------------------------------------
# Review Endpoints (Governance Layer)
# -----------------------------------------------------------------------------


@app.post(
    "/reviews/authority",
    response_model=ReviewRecord,
    status_code=status.HTTP_201_CREATED,
)
def submit_authority_review(submission: ReviewSubmission) -> ReviewRecord:
    """
    Submit an authority (government/regulator) review for a claim.

    PRECONDITION: Claim must be in AI_ANALYZED status (or legacy AI_VERIFIED/VERIFIED).

    This represents the first human oversight step after AI verification.
    Authority reviewers are typically government regulators or certified auditors.

    On APPROVE: Claim status → AUTHORITY_REVIEWED
    On REJECT: Claim status → REJECTED

    Args:
        submission: The review submission data.

    Returns:
        The created ReviewRecord.

    Raises:
        HTTPException: 400 if workflow preconditions not met.
        HTTPException: 404 if claim not found.
    """
    try:
        return review_service.submit_authority_review(submission)
    except review_service.ReviewError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.post(
    "/reviews/community",
    response_model=ReviewRecord,
    status_code=status.HTTP_201_CREATED,
)
def submit_community_review(submission: ReviewSubmission) -> ReviewRecord:
    """
    Submit a community (NGO/public) review for a claim.

    PRECONDITION: Claim must be in AUTHORITY_REVIEWED status.

    This represents the public transparency step in the governance process.
    Community reviewers can be NGOs, environmental groups, or public observers.

    On APPROVE: Claim status → COMMUNITY_REVIEWED
    On REJECT: Claim status → REJECTED

    Args:
        submission: The review submission data.

    Returns:
        The created ReviewRecord.

    Raises:
        HTTPException: 400 if workflow preconditions not met.
        HTTPException: 404 if claim not found.
    """
    try:
        return review_service.submit_community_review(submission)
    except review_service.ReviewError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.get(
    "/claims/{claim_id}/reviews",
    response_model=list[ReviewRecord],
)
def get_claim_reviews(claim_id: UUID) -> list[ReviewRecord]:
    """
    Get all reviews for a specific claim.

    Returns both authority and community reviews in submission order.

    Args:
        claim_id: The UUID of the claim.

    Returns:
        List of ReviewRecord objects for the claim.

    Raises:
        HTTPException: 404 if claim not found.
    """
    claim = claim_service.get_claim_by_id(claim_id)
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found",
        )

    return review_service.get_reviews_by_claim(claim_id)


# -----------------------------------------------------------------------------
# Minting Endpoints (Simulated Carbon Credits)
# -----------------------------------------------------------------------------


@app.post(
    "/mint",
    response_model=MintedCredit,
    status_code=status.HTTP_201_CREATED,
)
def mint_carbon_credits(request: MintRequest) -> MintedCredit:
    """
    Mint simulated carbon credits for a verified claim.

    IMPORTANT: This is a SIMULATED mint operation for MVP demonstration.
    Real implementation would interact with a blockchain (e.g., ERC-20 tokens).

    PRECONDITIONS:
    - Claim must be in COMMUNITY_REVIEWED status
    - Authority review must have APPROVED
    - Community review must have APPROVED
    - Credits must not already be minted for this claim

    Args:
        request: The mint request with claim ID and amount.

    Returns:
        The created MintedCredit object (simulated).

    Raises:
        HTTPException: 400 if minting preconditions not met.
    """
    try:
        return review_service.mint_credits(
            claim_id=request.claim_id,
            amount_tonnes_co2e=request.amount_tonnes_co2e,
        )
    except review_service.ReviewError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.get(
    "/credits/{token_id}",
    response_model=MintedCredit,
)
def get_minted_credit(token_id: UUID) -> MintedCredit:
    """
    Retrieve a minted credit by its token ID.

    Args:
        token_id: The UUID of the token.

    Returns:
        The MintedCredit object if found.

    Raises:
        HTTPException: 404 if token not found.
    """
    credit = review_service.get_minted_credit_by_id(token_id)
    if credit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit with token_id {token_id} not found",
        )
    return credit


# -----------------------------------------------------------------------------
# Evidence Endpoints (Provenance & Auditability)
# -----------------------------------------------------------------------------


@app.post(
    "/claims/{claim_id}/evidence",
    response_model=Evidence,
    status_code=status.HTTP_201_CREATED,
)
def create_claim_evidence(claim_id: UUID, submission: EvidenceSubmission) -> Evidence:
    """
    Create a new evidence record for a claim.

    IMMUTABILITY: Once created, evidence records cannot be modified or deleted.
    This ensures auditability and prevents tampering with the verification chain.

    The evidence hash is computed automatically from immutable fields and can
    be used by any party to verify data integrity.

    Args:
        claim_id: The UUID of the claim (must match submission.claim_id).
        submission: The evidence submission data.

    Returns:
        The created Evidence object with hash computed.

    Raises:
        HTTPException: 400 if claim_id doesn't match submission.
        HTTPException: 404 if claim not found.
    """
    # Verify claim exists
    claim = claim_service.get_claim_by_id(claim_id)
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found",
        )

    # Verify claim_id matches
    if submission.claim_id != claim_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"claim_id in path ({claim_id}) must match claim_id in body ({submission.claim_id})",
        )

    return evidence_service.create_evidence(submission)


@app.get(
    "/claims/{claim_id}/evidence",
    response_model=list[Evidence],
)
def get_claim_evidence(claim_id: UUID) -> list[Evidence]:
    """
    Get all evidence records for a specific claim.

    Returns evidence in chronological order (oldest first).
    Each evidence record includes a SHA256 hash for integrity verification.

    TRANSPARENCY: This endpoint is designed for public access.
    Authority reviewers, community reviewers, and the public can all
    access evidence to verify the claim's provenance.

    Args:
        claim_id: The UUID of the claim.

    Returns:
        List of Evidence objects for the claim.

    Raises:
        HTTPException: 404 if claim not found.
    """
    claim = claim_service.get_claim_by_id(claim_id)
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found",
        )

    return evidence_service.get_evidence_for_claim(claim_id)


@app.get(
    "/evidence/{evidence_id}",
    response_model=Evidence,
)
def get_evidence(evidence_id: UUID) -> Evidence:
    """
    Retrieve a specific evidence record by its ID.

    Args:
        evidence_id: The UUID of the evidence.

    Returns:
        The Evidence object if found.

    Raises:
        HTTPException: 404 if evidence not found.
    """
    evidence = evidence_service.get_evidence_by_id(evidence_id)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with id {evidence_id} not found",
        )
    return evidence


@app.post(
    "/credits/{credit_id}/monitor",
    response_model=MonitoringRun,
    status_code=status.HTTP_201_CREATED,
)
def run_credit_monitoring(
    credit_id: UUID,
    request: MonitoringRequest,
) -> MonitoringRun:
    """
    Run post-mint monitoring for a credit.

    This endpoint triggers a manual monitoring run that:
    - Retrieves current NDVI using Sentinel-2 pipeline
    - Compares against baseline NDVI recorded at mint time
    - Applies deterministic burn rules based on degradation
    - Updates credit status and remaining amount if needed
    - Creates immutable SYSTEM_AI evidence record

    Args:
        credit_id: The UUID of the credit to monitor.
        request: The monitoring request containing claim_id.

    Returns:
        The created MonitoringRun object.

    Raises:
        HTTPException: 400 if monitoring fails or preconditions not met.
    """
    try:
        return credit_monitoring_service.run_monitoring(request.claim_id, credit_id)
    except credit_monitoring_service.MonitoringError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.get(
    "/public/claims/{claim_id}/transparency",
    response_model=TransparencyReport,
)
def get_transparency_report(claim_id: UUID) -> TransparencyReport:
    """
    Get public transparency report for a claim.

    This endpoint provides a read-only, canonical view of:
    - Complete lifecycle timeline
    - AI consistency verdict summary
    - Credit health status (if credit exists)

    All data is derived from existing immutable records (evidence, reviews, credits).
    This view enables public auditability and trust verification.

    IMPORTANT:
    - AI verdict represents alignment confidence, NOT approval
    - Credit health is derived from credit lifecycle data, not manually set
    - All evidence is immutable and hash-verifiable

    Args:
        claim_id: The UUID of the claim.

    Returns:
        TransparencyReport with complete transparency data.

    Raises:
        HTTPException: 404 if claim not found.
    """
    try:
        return transparency_service.build_transparency_report(claim_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@app.get(
    "/evidence/{evidence_id}/verify",
)
def verify_evidence_integrity(evidence_id: UUID) -> dict:
    """
    Verify the integrity of an evidence record by checking its hash.

    This endpoint allows any party to verify that evidence has not been
    tampered with since creation. The hash is recomputed from the stored
    fields and compared to the stored hash.

    TRUST: This is a key endpoint for establishing trust in the evidence chain.
    External auditors, regulators, and the public can use this to verify
    that evidence data has not been altered.

    Args:
        evidence_id: The UUID of the evidence to verify.

    Returns:
        Dictionary with verification result:
        - is_valid: True if hash matches, False otherwise
        - message: Human-readable verification result
        - evidence_id: The evidence ID that was verified
        - hash: The stored hash value
    """
    is_valid, message = evidence_service.verify_evidence_integrity(evidence_id)

    evidence = evidence_service.get_evidence_by_id(evidence_id)
    stored_hash = evidence.hash if evidence else None

    return {
        "is_valid": is_valid,
        "message": message,
        "evidence_id": str(evidence_id),
        "hash": stored_hash,
    }
