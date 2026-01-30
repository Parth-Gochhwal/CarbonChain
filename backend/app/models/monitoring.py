"""
CarbonChain - Credit Monitoring Models

This module defines the data contracts for post-mint credit monitoring.
Monitoring runs track NDVI changes over time to detect credit degradation.

DESIGN PRINCIPLES:
1. APPEND-ONLY: Monitoring runs are immutable once created
2. DETERMINISTIC: Burn decisions are based on explicit thresholds
3. AUDITABLE: Every monitoring run creates SYSTEM_AI evidence
4. CONSERVATIVE: System errs on the side of caution when detecting degradation
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MonitoringOutcome(str, Enum):
    """
    Outcome of a monitoring run.
    
    OK: No degradation detected, credit remains valid
    WARNING: Degradation detected but below burn threshold
    FAILURE: Degradation exceeds threshold, burn triggered
    """
    OK = "ok"
    WARNING = "warning"
    FAILURE = "failure"


class MonitoringRun(BaseModel):
    """
    Record of a single post-mint monitoring run.
    
    Monitoring runs are append-only and immutable once created.
    Each run compares current NDVI against baseline NDVI recorded at mint time.
    
    BURN RULES (deterministic):
    - delta_ndvi >= -0.05 → OK
    - -0.05 > delta_ndvi >= -0.15 → WARNING → CreditStatus.AT_RISK
    - -0.15 > delta_ndvi >= -0.30 → FAILURE → Partial burn
    - delta_ndvi < -0.30 → FAILURE → Full burn
    
    Partial burn calculation:
    burn_percentage = abs(delta_ndvi) / 0.30 (capped at 1.0)
    """
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this monitoring run"
    )
    claim_id: UUID = Field(
        ...,
        description="ID of the claim associated with this monitoring run"
    )
    credit_id: UUID = Field(
        ...,
        description="ID of the credit being monitored"
    )
    run_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Date/time when this monitoring run was performed"
    )
    baseline_ndvi: float = Field(
        ...,
        description="Baseline NDVI value recorded at mint time"
    )
    current_ndvi: float = Field(
        ...,
        description="Current NDVI value from this monitoring run"
    )
    delta_ndvi: float = Field(
        ...,
        description="Change in NDVI (current - baseline)"
    )
    outcome: MonitoringOutcome = Field(
        ...,
        description="Outcome of this monitoring run (OK, WARNING, or FAILURE)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this monitoring run was recorded"
    )

    class Config:
        """Pydantic configuration for the MonitoringRun model."""
        json_schema_extra = {
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440002",
                "claim_id": "550e8400-e29b-41d4-a716-446655440000",
                "credit_id": "660e8400-e29b-41d4-a716-446655440001",
                "run_date": "2025-06-15T10:00:00Z",
                "baseline_ndvi": 0.58,
                "current_ndvi": 0.52,
                "delta_ndvi": -0.06,
                "outcome": "warning",
                "created_at": "2025-06-15T10:00:05Z"
            }
        }
"""
CarbonChain - Credit Monitoring Models

This module defines the data contracts for post-mint credit monitoring.
Monitoring runs track NDVI changes over time to detect credit degradation.

DESIGN PRINCIPLES:
1. APPEND-ONLY: Monitoring runs are immutable once created
2. DETERMINISTIC: Burn decisions are based on explicit thresholds
3. AUDITABLE: Every monitoring run creates SYSTEM_AI evidence
4. CONSERVATIVE: System errs on the side of caution when detecting degradation
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MonitoringOutcome(str, Enum):
    """
    Outcome of a monitoring run.
    
    OK: No degradation detected, credit remains valid
    WARNING: Degradation detected but below burn threshold
    FAILURE: Degradation exceeds threshold, burn triggered
    """
    OK = "ok"
    WARNING = "warning"
    FAILURE = "failure"


class MonitoringRun(BaseModel):
    """
    Record of a single post-mint monitoring run.
    
    Monitoring runs are append-only and immutable once created.
    Each run compares current NDVI against baseline NDVI recorded at mint time.
    
    BURN RULES (deterministic):
    - delta_ndvi >= -0.05 → OK
    - -0.05 > delta_ndvi >= -0.15 → WARNING → CreditStatus.AT_RISK
    - -0.15 > delta_ndvi >= -0.30 → FAILURE → Partial burn
    - delta_ndvi < -0.30 → FAILURE → Full burn
    
    Partial burn calculation:
    burn_percentage = abs(delta_ndvi) / 0.30 (capped at 1.0)
    """
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this monitoring run"
    )
    claim_id: UUID = Field(
        ...,
        description="ID of the claim associated with this monitoring run"
    )
    credit_id: UUID = Field(
        ...,
        description="ID of the credit being monitored"
    )
    run_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Date/time when this monitoring run was performed"
    )
    baseline_ndvi: float = Field(
        ...,
        description="Baseline NDVI value recorded at mint time"
    )
    current_ndvi: float = Field(
        ...,
        description="Current NDVI value from this monitoring run"
    )
    delta_ndvi: float = Field(
        ...,
        description="Change in NDVI (current - baseline)"
    )
    outcome: MonitoringOutcome = Field(
        ...,
        description="Outcome of this monitoring run (OK, WARNING, or FAILURE)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this monitoring run was recorded"
    )

    class Config:
        """Pydantic configuration for the MonitoringRun model."""
        json_schema_extra = {
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440002",
                "claim_id": "550e8400-e29b-41d4-a716-446655440000",
                "credit_id": "660e8400-e29b-41d4-a716-446655440001",
                "run_date": "2025-06-15T10:00:00Z",
                "baseline_ndvi": 0.58,
                "current_ndvi": 0.52,
                "delta_ndvi": -0.06,
                "outcome": "warning",
                "created_at": "2025-06-15T10:00:05Z"
            }
        }
