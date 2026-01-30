// Type definitions matching backend models

export type ClaimStatus = 
  | 'submitted'
  | 'ai_analysis_pending'
  | 'ai_analysis_in_progress'
  | 'verified'
  | 'ai_verified'
  | 'ai_rejected'
  | 'ai_analyzed'
  | 'authority_reviewed'
  | 'community_reviewed'
  | 'approved'
  | 'rejected'
  | 'minted';

export type ClaimType = 
  | 'mangrove_restoration'
  | 'solar_installation'
  | 'wind_installation'
  | 'reforestation'
  | 'wetland_restoration'
  | 'avoided_deforestation'
  | 'other';

export type GeometryType = 'point' | 'buffer' | 'polygon';
export type GeometrySource = 'user_point' | 'user_drawn' | 'authority_defined';

export interface GeoLocation {
  latitude: number;
  longitude: number;
  location_name?: string;
}

export interface CarbonImpactEstimate {
  min_tonnes_co2e: number;
  max_tonnes_co2e: number;
  estimation_methodology?: string;
  time_horizon_years: number;
}

export interface Claim {
  id: string;
  claim_type: ClaimType;
  title: string;
  description: string;
  location?: GeoLocation;
  geometry_geojson?: any;
  geometry_type?: GeometryType;
  geometry_source?: GeometrySource;
  area_hectares?: number;
  carbon_impact_estimate: CarbonImpactEstimate;
  action_start_date: string;
  action_end_date?: string;
  stated_assumptions: string[];
  known_limitations: string[];
  submitter_name: string;
  submitter_contact?: string;
  status: ClaimStatus;
  created_at: string;
  updated_at: string;
  verification_id?: string;
}

export interface ClaimSubmission {
  claim_type: ClaimType;
  title: string;
  description: string;
  location?: GeoLocation;
  geometry_geojson?: any;
  area_hectares?: number;
  carbon_impact_estimate: CarbonImpactEstimate;
  action_start_date: string;
  action_end_date?: string;
  stated_assumptions?: string[];
  known_limitations?: string[];
  submitter_name: string;
  submitter_contact?: string;
}

export type EvidenceType = 'system_ai' | 'user_upload' | 'document' | 'community_report';

export interface Evidence {
  id: string;
  claim_id: string;
  type: EvidenceType;
  source: string;
  title: string;
  description: string;
  data_ref: string;
  confidence_weight: number;
  hash: string;
  created_at: string;
}

export interface EvidenceSummary {
  id: string;
  type: EvidenceType;
  source: string;
  title: string;
  confidence_weight: number;
  hash: string;
  created_at: string;
  data_ref?: string;
}

export type ReviewDecision = 'approve' | 'reject';
export type ReviewRole = 'authority' | 'community';

export interface ReviewRecord {
  id: string;
  claim_id: string;
  reviewer_id: string;
  role: ReviewRole;
  decision: ReviewDecision;
  confidence_score?: number;
  positives: string[];
  concerns: string[];
  notes?: string;
  created_at: string;
}

export interface ReviewSubmission {
  claim_id: string;
  reviewer_id: string;
  decision: ReviewDecision;
  confidence_score?: number;
  positives?: string[];
  concerns?: string[];
  notes?: string;
}

export type CreditStatus = 'active' | 'at_risk' | 'partially_burned' | 'fully_burned';

export interface MintedCredit {
  token_id: string;
  claim_id: string;
  amount_tonnes_co2e: number;
  status: CreditStatus;
  remaining_tonnes_co2e: number;
  baseline_ndvi?: number;
  minted_at: string;
  is_simulated: boolean;
  label: string;
}

export interface VerificationResult {
  id: string;
  claim_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  outcome?: 'approved' | 'rejected' | 'needs_review' | 'inconclusive';
  verified_impact?: {
    min_tonnes_co2e: number;
    max_tonnes_co2e: number;
    point_estimate_tonnes_co2e?: number;
    confidence: 'high' | 'medium' | 'low' | 'very_low';
    methodology_used: string;
    deviation_from_claim_percent?: number;
  };
  overall_confidence: 'high' | 'medium' | 'low' | 'very_low';
  summary?: string;
  created_at: string;
  completed_at?: string;
}

export interface AIConsistencyResult {
  claim_id: string;
  claimed_min_co2e: number;
  claimed_max_co2e: number;
  estimated_min_co2e: number;
  estimated_max_co2e: number;
  deviation_percent: number;
  verdict: 'strongly_supports' | 'partially_supports' | 'contradicts';
  confidence_score: number; // 0.0 to 1.0
  explanation: string;
  created_at: string;
}

export interface MonitoringRun {
  id: string;
  claim_id: string;
  credit_id: string;
  run_date: string;
  current_ndvi: number;
  baseline_ndvi: number;
  ndvi_delta: number;
  degradation_percent: number;
  burn_amount_tonnes_co2e: number;
  credit_status_before: CreditStatus;
  credit_status_after: CreditStatus;
  notes?: string;
}

export interface PublicClaimResponse {
  claim: Claim;
  verification?: VerificationResult;
  authority_review?: ReviewRecord;
  community_review?: ReviewRecord;
  minted_credit?: MintedCredit;
  evidence: EvidenceSummary[];
  status: ClaimStatus;
  can_mint: boolean;
  mint_eligibility_reason: string;
  ai_verdict?: AIConsistencyResult;
  credit_status?: CreditStatus;
  credit_remaining_co2e?: number;
  monitoring_history: MonitoringRun[];
}

export interface TransparencyReport {
  claim_id: string;
  lifecycle_timeline: any[];
  ai_verdict_summary?: {
    verdict: string;
    confidence: string;
    score: number;
  };
  credit_health_status?: {
    status: CreditStatus;
    health_score: number;
  };
}

export interface ApiResponse<T> {
  success?: boolean;
  data?: T;
  error?: string;
  message?: string;
}
