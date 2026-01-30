# CarbonChain MVP

Climate action claim submission and verification platform with AI MRV, human governance, and credit lifecycle integrity.

## Public Transparency View

The Public Transparency View (Layer 6) provides a read-only, canonical view of claim lifecycle data for public auditability and trust verification.

### Features

- **Canonical Timeline**: Complete chronological view of all claim lifecycle events
  - Claim submission
  - AI MRV analysis
  - AI consistency verdict
  - Authority review
  - Community review
  - Credit minting
  - Credit monitoring runs

- **AI Verdict Summary**: Clear presentation of AI consistency evaluation
  - Verdict category (STRONGLY_SUPPORTS, PARTIALLY_SUPPORTS, CONTRADICTS)
  - Claimed vs AI-estimated ranges
  - Deviation percentage
  - Confidence score
  - Explanation of reasoning

- **Credit Health Status**: Derived credit health status based on post-mint monitoring
  - HEALTHY: Credit is active with no degradation
  - DEGRADED: Credit has been partially burned or is at risk
  - INVALIDATED: Credit has been fully burned

### Important Clarifications

- **AI Verdict ≠ Approval**: The AI verdict represents alignment confidence between the claim and independent satellite-based MRV estimates, NOT approval. Approval requires human governance (authority + community review).

- **Credit Health is Derived**: Credit health status is automatically computed from credit lifecycle data, not manually set. All status changes are backed by immutable evidence records.

- **Immutable Evidence**: All timeline events are backed by immutable evidence records with SHA256 hashes. Evidence integrity can be verified using the evidence verification endpoint, ensuring complete auditability and preventing tampering.

### API Endpoint

```
GET /public/claims/{claim_id}/transparency
```

Returns a `TransparencyReport` containing:
- `timeline`: List of chronological timeline events
- `ai_verdict`: AI consistency verdict summary (if available)
- `credit_health`: Credit health status (if credit exists)

### Frontend Page

The `PublicTransparency.jsx` page provides a user-friendly view of the transparency report with:
- Vertical timeline visualization
- AI verdict summary card with clear labeling
- Credit health badge with explanation
- Source attribution for all events (AI-derived vs Human-verified)

All views are read-only with no editing, actions, or minting buttons.
