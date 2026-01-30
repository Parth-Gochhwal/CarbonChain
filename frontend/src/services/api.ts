import axios from 'axios';
import type { 
  Claim, 
  ClaimSubmission, 
  PublicClaimResponse,
  ReviewSubmission,
  ReviewRecord,
  Evidence,
  MintedCredit,
  VerificationResult,
  TransparencyReport
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Claims API
export const claimsApi = {
  // Submit a new claim
  submitClaim: async (claimData: ClaimSubmission): Promise<Claim> => {
    const response = await api.post<Claim>('/claims', claimData);
    return response.data;
  },

  // Get all claims
  getClaims: async (): Promise<Claim[]> => {
    const response = await api.get<Claim[]>('/claims');
    return response.data;
  },

  // Get claim by ID
  getClaim: async (id: string): Promise<Claim> => {
    const response = await api.get<Claim>(`/claims/${id}`);
    return response.data;
  },

  // Get public claim view (includes all related data)
  getPublicClaim: async (id: string): Promise<PublicClaimResponse> => {
    const response = await api.get<PublicClaimResponse>(`/public/claims/${id}`);
    return response.data;
  },

  // Upload evidence files for a claim
  uploadEvidence: async (claimId: string, files: File[]): Promise<Evidence[]> => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    const response = await api.post<Evidence[]>(
      `/claims/${claimId}/evidence/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // Update claim geometry (authority)
  updateGeometry: async (claimId: string, geometryGeojson: any): Promise<Claim> => {
    const response = await api.put<Claim>(
      `/claims/${claimId}/geometry/authority`,
      { geometry_geojson: geometryGeojson }
    );
    return response.data;
  },
};

// Review API
export const reviewApi = {
  // Submit authority review
  submitAuthorityReview: async (review: ReviewSubmission): Promise<ReviewRecord> => {
    const response = await api.post<ReviewRecord>('/reviews/authority', review);
    return response.data;
  },

  // Submit community review
  submitCommunityReview: async (review: ReviewSubmission): Promise<ReviewRecord> => {
    const response = await api.post<ReviewRecord>('/reviews/community', review);
    return response.data;
  },

  // Get reviews for a claim
  getClaimReviews: async (claimId: string): Promise<ReviewRecord[]> => {
    const response = await api.get<ReviewRecord[]>(`/claims/${claimId}/reviews`);
    return response.data;
  },
};

// Verification API
export const verificationApi = {
  // Trigger verification
  verifyClaim: async (claimId: string): Promise<VerificationResult> => {
    const response = await api.post<VerificationResult>('/verify', { claim_id: claimId });
    return response.data;
  },

  // Get verification by ID
  getVerification: async (verificationId: string): Promise<VerificationResult> => {
    const response = await api.get<VerificationResult>(`/verifications/${verificationId}`);
    return response.data;
  },
};

// Credits API
export const creditsApi = {
  // Mint credits for a claim
  mintCredits: async (claimId: string, amountTonnesCo2e: number): Promise<MintedCredit> => {
    const response = await api.post<MintedCredit>('/mint', {
      claim_id: claimId,
      amount_tonnes_co2e: amountTonnesCo2e,
    });
    return response.data;
  },

  // Get minted credit by token ID
  getCredit: async (tokenId: string): Promise<MintedCredit> => {
    const response = await api.get<MintedCredit>(`/credits/${tokenId}`);
    return response.data;
  },
};

// Evidence API
export const evidenceApi = {
  // Get evidence for a claim
  getClaimEvidence: async (claimId: string): Promise<Evidence[]> => {
    const response = await api.get<Evidence[]>(`/claims/${claimId}/evidence`);
    return response.data;
  },

  // Get evidence by ID
  getEvidence: async (evidenceId: string): Promise<Evidence> => {
    const response = await api.get<Evidence>(`/evidence/${evidenceId}`);
    return response.data;
  },

  // Verify evidence integrity
  verifyEvidenceIntegrity: async (evidenceId: string): Promise<{
    is_valid: boolean;
    message: string;
    evidence_id: string;
    hash: string;
  }> => {
    const response = await api.get(`/evidence/${evidenceId}/verify`);
    return response.data;
  },
};

// Transparency API
export const transparencyApi = {
  // Get transparency report
  getTransparencyReport: async (claimId: string): Promise<TransparencyReport> => {
    const response = await api.get<TransparencyReport>(
      `/public/claims/${claimId}/transparency`
    );
    return response.data;
  },
};

// Monitoring API
export const monitoringApi = {
  // Run credit monitoring
  runMonitoring: async (creditId: string, claimId: string): Promise<any> => {
    const response = await api.post(`/credits/${creditId}/monitor`, {
      claim_id: claimId,
    });
    return response.data;
  },
};

export default api;
