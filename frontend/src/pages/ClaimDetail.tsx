import React, { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  MapPin, 
  Calendar, 
  User, 
  Leaf, 
  Image as ImageIcon,
  Video,
  FileText,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  XCircle,
  Shield,
  Eye,
  TrendingUp,
  Hash,
  Coins
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import PageContainer from '../components/layout/PageContainer';
import ClaimTimeline from '../components/claim/ClaimTimeline';
import { claimsApi, creditsApi } from '../services/api';
import type { PublicClaimResponse } from '../types';
import { formatDate, formatCO2e, getStatusColor, getStatusLabel } from '../lib/utils';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ClaimDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const [claimData, setClaimData] = useState<PublicClaimResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [aiAnalysisInProgress, setAiAnalysisInProgress] = useState(false);
  const [minting, setMinting] = useState(false);

  useEffect(() => {
    let pollInterval: NodeJS.Timeout | null = null;
    
    const fetchClaim = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        const data = await claimsApi.getPublicClaim(id);
        setClaimData(data);
        
        // Check if AI analysis is pending or in progress
        // Also check if claim was rejected by AI (ai_rejected)
        if (data.status === 'ai_analysis_pending' || data.status === 'ai_analysis_in_progress') {
          setAiAnalysisInProgress(true);
        } else {
          setAiAnalysisInProgress(false);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to load claim');
      } finally {
        setLoading(false);
      }
    };

    fetchClaim();
    
    // Poll for AI analysis completion if pending or in progress
    // CRITICAL: Start polling based on initial state or location state
    const shouldStartPolling = location.state?.aiAnalysisPending;
    
    if (shouldStartPolling) {
      setAiAnalysisInProgress(true);
      pollInterval = setInterval(async () => {
        try {
          if (!id) {
            if (pollInterval) clearInterval(pollInterval);
            return;
          }
          
          const data = await claimsApi.getPublicClaim(id);
          setClaimData(data);
          
          // Stop polling when status becomes AI_VERIFIED, AI_REJECTED, or any final state
          // CRITICAL: Must stop polling on AI_REJECTED to prevent infinite loading
          if (data.status === 'ai_verified' || data.status === 'ai_rejected' || 
              data.status === 'ai_analyzed' || data.status === 'authority_reviewed' || 
              data.status === 'rejected' || data.status === 'approved' || data.status === 'minted') {
            setAiAnalysisInProgress(false);
            if (pollInterval) {
              clearInterval(pollInterval);
              pollInterval = null;
            }
          }
        } catch (err) {
          console.error('Error polling claim status:', err);
          // On error, stop polling to prevent infinite retries
          setAiAnalysisInProgress(false);
          if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
          }
        }
      }, 3000); // Poll every 3 seconds for faster updates
    }
    
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
    };
  }, [id, location.state]);
  
  // Separate effect to handle polling when claimData status changes
  useEffect(() => {
    let pollInterval: NodeJS.Timeout | null = null;
    
    if (!claimData || !id) return;
    
    const shouldPoll = claimData.status === 'ai_analysis_pending' || 
                      claimData.status === 'ai_analysis_in_progress';
    
    if (shouldPoll && !aiAnalysisInProgress) {
      setAiAnalysisInProgress(true);
    }
    
    if (shouldPoll) {
      pollInterval = setInterval(async () => {
        try {
          const data = await claimsApi.getPublicClaim(id);
          setClaimData(data);
          
          // Stop polling when status becomes final
          if (data.status === 'ai_verified' || data.status === 'ai_rejected' || 
              data.status === 'ai_analyzed' || data.status === 'authority_reviewed' || 
              data.status === 'rejected' || data.status === 'approved' || data.status === 'minted') {
            setAiAnalysisInProgress(false);
            if (pollInterval) {
              clearInterval(pollInterval);
              pollInterval = null;
            }
          }
        } catch (err) {
          console.error('Error polling claim status:', err);
          setAiAnalysisInProgress(false);
          if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
          }
        }
      }, 3000);
    }
    
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
    };
  }, [claimData?.status, id, aiAnalysisInProgress]);

  // Show AI analysis in progress state OR rejection state
  if (claimData && (aiAnalysisInProgress || claimData.status === 'ai_rejected')) {
    // Show rejection state if claim was rejected by AI
    if (claimData.status === 'ai_rejected') {
      return (
        <PageContainer className="py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-2xl mx-auto text-center"
          >
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <XCircle className="h-10 w-10 text-red-600" />
            </div>
            <h2 className="text-3xl font-bold text-slate-900 mb-4">No Positive Carbon Impact Detected</h2>
            <p className="text-lg text-slate-600 mb-6">
              Our AI system analyzed your claim using satellite imagery and NDVI computation.
              The analysis shows no positive carbon sequestration or indicates degradation.
            </p>
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-6">
              <div className="text-sm text-red-800 space-y-2">
                <p className="font-semibold">Analysis Results:</p>
                <ul className="list-disc list-inside space-y-1 text-left max-w-md mx-auto">
                  <li>Satellite data processed successfully</li>
                  <li>NDVI change detection completed</li>
                  <li>Carbon impact estimated from vegetation data</li>
                  <li>Result: No positive carbon impact or degradation detected</li>
                </ul>
              </div>
            </div>
            <p className="text-sm text-slate-500 mb-6">
              This means the satellite data shows either no gain in vegetation or actual degradation.
              Evidence cards below show the detailed analysis results.
            </p>
            <Button onClick={() => window.history.back()} variant="outline">
              Go Back
            </Button>
          </motion.div>
        </PageContainer>
      );
    }
    
    // Show in-progress state
    const statusText = claimData.status === 'ai_analysis_pending' 
      ? 'AI Analysis Pending' 
      : 'Analyzing Satellite Imagery and NDVI';
    
    return (
      <PageContainer className="py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-2xl mx-auto text-center"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-20 h-20 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-6"
          />
          <h2 className="text-3xl font-bold text-slate-900 mb-4">{statusText}</h2>
          <p className="text-lg text-slate-600 mb-6">
            Our AI system is analyzing your claim using satellite imagery and NDVI computation.
            This may take a few moments...
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-6">
            <div className="text-sm text-blue-800 space-y-2">
              <p className="font-semibold">What's happening:</p>
              <ul className="list-disc list-inside space-y-1 text-left max-w-md mx-auto">
                <li>Processing Sentinel-2 satellite imagery</li>
                <li>Computing NDVI change detection</li>
                <li>Estimating carbon impact from vegetation data</li>
                <li>Generating consistency verdict</li>
              </ul>
            </div>
          </div>
          <p className="text-sm text-slate-500">
            This page will automatically update when analysis completes.
          </p>
        </motion.div>
      </PageContainer>
    );
  }

  if (loading) {
    return (
      <PageContainer className="py-12">
        <div className="flex items-center justify-center min-h-[400px]">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center"
          >
            <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-slate-600 text-lg">Loading claim details...</p>
          </motion.div>
        </div>
      </PageContainer>
    );
  }

  if (error || !claimData) {
    return (
      <PageContainer className="py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md mx-auto"
        >
          <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="h-10 w-10 text-red-600" />
          </div>
          <h2 className="text-3xl font-bold text-slate-900 mb-2">Claim Not Found</h2>
          <p className="text-slate-600 mb-6">{error || 'The requested claim could not be found.'}</p>
          <Button onClick={() => window.history.back()}>
            Go Back
          </Button>
        </motion.div>
      </PageContainer>
    );
  }

  const { claim, verification, authority_review, community_review, minted_credit, evidence, ai_verdict, credit_status, credit_remaining_co2e, can_mint, mint_eligibility_reason } = claimData;

  const handleMint = async () => {
    if (!claimData || !verification || !can_mint) return;
    
    try {
      setMinting(true);
      const amount = verification.verified_impact?.point_estimate_tonnes_co2e || 
                     (verification.verified_impact ? 
                       (verification.verified_impact.min_tonnes_co2e + verification.verified_impact.max_tonnes_co2e) / 2 : 
                       0);
      
      await creditsApi.mintCredits(claim.id, amount);
      
      // Refresh claim data
      const updatedData = await claimsApi.getPublicClaim(claim.id);
      setClaimData(updatedData);
    } catch (error: any) {
      console.error('Error minting credits:', error);
      alert(error.response?.data?.detail || 'Failed to mint credits');
    } finally {
      setMinting(false);
    }
  };

  const getEvidenceIcon = (type: string) => {
    switch (type) {
      case 'user_upload':
      case 'document':
        return ImageIcon;
      case 'system_ai':
        return Shield; // Use Shield icon for AI-generated evidence
      case 'satellite_image':
        return MapPin;
      default:
        return FileText;
    }
  };

  const isImage = (dataRef: string, evidenceType?: string) => {
    // Check for image file extensions
    if (/\.(jpg|jpeg|png|webp)$/i.test(dataRef)) return true;
    // SYSTEM_AI evidence with /uploads path is likely an image
    if (evidenceType === 'system_ai' && dataRef.startsWith('/uploads')) return true;
    return false;
  };

  const isVideo = (dataRef: string) => {
    return /\.(mp4|mov|webm)$/i.test(dataRef);
  };

  const getEvidenceUrl = (dataRef: string) => {
    if (!dataRef) return null;
    if (dataRef.startsWith('http')) return dataRef;
    if (dataRef.startsWith('/uploads')) return `${API_BASE_URL}${dataRef}`;
    // Handle GEE references - these are not directly viewable, return null
    if (dataRef.startsWith('gee://') || dataRef.startsWith('ai-consistency://')) return null;
    return `${API_BASE_URL}/uploads${dataRef}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      <PageContainer className="py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          {/* Success Message */}
          {location.state?.message && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-6 bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 rounded-2xl shadow-lg"
            >
              <div className="flex items-center space-x-3 text-emerald-800">
                <CheckCircle className="h-6 w-6" />
                <span className="font-semibold text-lg">{location.state.message}</span>
              </div>
            </motion.div>
          )}

          {/* Header */}
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <Badge className={`${getStatusColor(claim.status)} text-sm px-4 py-1.5`}>
                  {getStatusLabel(claim.status)}
                </Badge>
                {ai_verdict && (
                  <Badge className={`${
                    ai_verdict.verdict === 'consistent' 
                      ? 'bg-emerald-100 text-emerald-800' 
                      : ai_verdict.verdict === 'inconsistent'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-yellow-100 text-yellow-800'
                  } text-sm px-4 py-1.5`}>
                    AI: {ai_verdict.verdict}
                  </Badge>
                )}
              </div>
              <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 mb-4 leading-tight">
                {claim.title}
              </h1>
              <div className="flex flex-wrap items-center gap-6 text-sm text-slate-600">
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4" />
                  <span className="font-medium">{claim.submitter_name}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Calendar className="h-4 w-4" />
                  <span>{formatDate(claim.created_at)}</span>
                </div>
                {claim.location && (
                  <div className="flex items-center space-x-2">
                    <MapPin className="h-4 w-4" />
                    <span>{claim.location.latitude.toFixed(4)}, {claim.location.longitude.toFixed(4)}</span>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm" className="flex items-center">
                <ExternalLink className="h-4 w-4 mr-2" />
                Share
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-8">
              {/* Claim Details */}
              <Card className="border-0 shadow-xl">
                <CardHeader>
                  <CardTitle className="text-2xl">Project Description</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-slate-700 leading-relaxed mb-8 text-lg">
                    {claim.description}
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="p-6 bg-gradient-to-br from-primary-50 to-primary-100 rounded-2xl">
                      <h4 className="font-semibold text-primary-900 mb-2 flex items-center">
                        <Leaf className="h-5 w-5 mr-2" />
                        Carbon Impact Range
                      </h4>
                      <div className="text-3xl font-bold text-primary-900 mb-1">
                        {formatCO2e(claim.carbon_impact_estimate.min_tonnes_co2e)} - {formatCO2e(claim.carbon_impact_estimate.max_tonnes_co2e)}
                      </div>
                      <p className="text-sm text-primary-700">Estimated CO₂ reduction</p>
                    </div>
                    
                    <div className="p-6 bg-gradient-to-br from-secondary-50 to-secondary-100 rounded-2xl">
                      <h4 className="font-semibold text-secondary-900 mb-2 flex items-center">
                        <MapPin className="h-5 w-5 mr-2" />
                        Project Area
                      </h4>
                      <div className="text-3xl font-bold text-secondary-900 mb-1">
                        {claim.area_hectares ? `${claim.area_hectares.toFixed(1)} ha` : 'N/A'}
                      </div>
                      <p className="text-sm text-secondary-700">Geographic coverage</p>
                    </div>
                  </div>

                  {claim.geometry_type && (
                    <div className="mt-6 p-4 bg-slate-50 rounded-xl">
                      <div className="text-sm text-slate-600">
                        <strong>Geometry Type:</strong> {claim.geometry_type} • 
                        <strong> Source:</strong> {claim.geometry_source?.replace('_', ' ')}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* AI Verdict */}
              {ai_verdict && (
                <Card className="border-0 shadow-xl bg-gradient-to-br from-blue-50 to-cyan-50">
                  <CardHeader>
                    <CardTitle className="text-2xl flex items-center">
                      <Shield className="h-6 w-6 mr-2" />
                      AI Consistency Verdict
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <div>
                          <div className="text-sm text-slate-600 mb-1">Verdict</div>
                          <div className="text-xl font-bold text-slate-900 capitalize">
                            {ai_verdict.verdict.replace('_', ' ')}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-slate-600 mb-1">Confidence Score</div>
                          <div className="text-xl font-bold text-slate-900">
                            {typeof ai_verdict.confidence_score === 'number' && !isNaN(ai_verdict.confidence_score)
                              ? `${(ai_verdict.confidence_score * 100).toFixed(0)}%`
                              : 'Calculating...'}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-slate-600 mb-1">Deviation</div>
                          <div className={`text-xl font-bold ${ai_verdict.deviation_percent >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                            {typeof ai_verdict.deviation_percent === 'number' && !isNaN(ai_verdict.deviation_percent)
                              ? `${ai_verdict.deviation_percent >= 0 ? '+' : ''}${ai_verdict.deviation_percent.toFixed(1)}%`
                              : 'N/A'}
                          </div>
                        </div>
                      </div>
                      <div className="mb-4 p-3 bg-white/60 rounded-lg">
                        <div className="text-sm font-semibold text-slate-900 mb-2">Carbon Impact Comparison</div>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="text-slate-600">Claimed Range</div>
                            <div className="font-bold text-slate-900">
                              {ai_verdict.claimed_min_co2e.toFixed(1)} - {ai_verdict.claimed_max_co2e.toFixed(1)} tCO₂e
                            </div>
                          </div>
                          <div>
                            <div className="text-slate-600">AI Estimated Range</div>
                            <div className="font-bold text-slate-900">
                              {ai_verdict.estimated_min_co2e.toFixed(1)} - {ai_verdict.estimated_max_co2e.toFixed(1)} tCO₂e
                            </div>
                          </div>
                        </div>
                      </div>
                      <p className="text-slate-700 leading-relaxed">{ai_verdict.explanation}</p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Evidence */}
              <Card className="border-0 shadow-xl">
                <CardHeader>
                  <CardTitle className="text-2xl flex items-center">
                    <Eye className="h-6 w-6 mr-2" />
                    Supporting Evidence ({evidence.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {evidence.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {evidence
                        .filter(ev => ev && ev.id && ev.title) // Skip empty or invalid evidence
                        .map((ev) => {
                        const Icon = getEvidenceIcon(ev.type);
                        const url = ev.data_ref ? getEvidenceUrl(ev.data_ref) : null;
                        const isImg = url && isImage(ev.data_ref || '', ev.type);
                        const isVid = url && isVideo(ev.data_ref || '');
                        
                        // For SYSTEM_AI evidence without image, show description as text content
                        const isTextEvidence = ev.type === 'system_ai' && !isImg && !isVid && ev.description;
                        
                        return (
                          <motion.div
                            key={ev.id}
                            whileHover={{ scale: 1.02, y: -4 }}
                            className="group cursor-pointer"
                          >
                            <div className="relative overflow-hidden rounded-xl border-2 border-slate-200 hover:border-primary-400 transition-all bg-white">
                              {isImg && url ? (
                                <img
                                  src={url}
                                  alt={ev.title}
                                  className="w-full h-48 object-cover"
                                />
                              ) : isVid && url ? (
                                <div className="w-full h-48 bg-slate-100 flex items-center justify-center">
                                  <Video className="h-12 w-12 text-slate-400" />
                                </div>
                              ) : isTextEvidence ? (
                                <div className="w-full min-h-48 bg-gradient-to-br from-blue-50 to-cyan-50 p-4">
                                  <div className="flex items-center mb-2">
                                    <Icon className="h-5 w-5 text-blue-600 mr-2" />
                                    <p className="text-sm font-semibold text-slate-900">{ev.title}</p>
                                  </div>
                                  <p className="text-xs text-slate-700 line-clamp-4 leading-relaxed">
                                    {ev.description}
                                  </p>
                                </div>
                              ) : (
                                <div className="w-full h-48 bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center">
                                  <Icon className="h-12 w-12 text-slate-400" />
                                </div>
                              )}
                              
                              <div className="p-4">
                                <p className="text-sm font-semibold text-slate-900 truncate mb-1">
                                  {ev.title}
                                </p>
                                <div className="flex items-center justify-between text-xs text-slate-500">
                                  <span>{ev.type.replace('_', ' ')}</span>
                                  <span>{formatDate(ev.created_at)}</span>
                                </div>
                                {ev.hash && (
                                  <div className="mt-2 flex items-center gap-1 text-xs text-slate-400">
                                    <Hash className="h-3 w-3" />
                                    <span className="font-mono truncate">{ev.hash.substring(0, 12)}...</span>
                                  </div>
                                )}
                              </div>
                              
                              {url && (
                                <a
                                  href={url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-all duration-200 flex items-center justify-center"
                                >
                                  <ExternalLink className="h-6 w-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                                </a>
                              )}
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <FileText className="h-16 w-16 mx-auto mb-4 text-slate-300" />
                      <p className="text-lg">
                        {claim.status === 'ai_analysis_pending' || claim.status === 'ai_analysis_in_progress'
                          ? 'AI analysis in progress. Evidence will appear here once analysis completes.'
                          : 'No evidence files uploaded'}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Reviews */}
              {authority_review && (
                <Card className="border-0 shadow-xl">
                  <CardHeader>
                    <CardTitle className="text-2xl flex items-center">
                      <Shield className="h-6 w-6 mr-2" />
                      Authority Review
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-start space-x-4">
                      <div className={`p-3 rounded-2xl ${
                        authority_review.decision === 'approve' 
                          ? 'bg-emerald-100 text-emerald-600' 
                          : 'bg-red-100 text-red-600'
                      }`}>
                        {authority_review.decision === 'approve' ? (
                          <CheckCircle className="h-6 w-6" />
                        ) : (
                          <XCircle className="h-6 w-6" />
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-3">
                          <Badge className={
                            authority_review.decision === 'approve' 
                              ? 'bg-emerald-100 text-emerald-800' 
                              : 'bg-red-100 text-red-800'
                          }>
                            {authority_review.decision === 'approve' ? 'Approved' : 'Rejected'}
                          </Badge>
                          <span className="text-sm text-slate-600">
                            by {authority_review.reviewer_id}
                          </span>
                        </div>
                        
                        {authority_review.notes && (
                          <p className="text-slate-700 mb-3 leading-relaxed">{authority_review.notes}</p>
                        )}
                        
                        {authority_review.positives.length > 0 && (
                          <div className="mb-3">
                            <div className="text-sm font-semibold text-emerald-700 mb-1">Positives:</div>
                            <ul className="text-sm text-slate-600 space-y-1">
                              {authority_review.positives.map((p, i) => (
                                <li key={i}>• {p}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {authority_review.concerns.length > 0 && (
                          <div>
                            <div className="text-sm font-semibold text-red-700 mb-1">Concerns:</div>
                            <ul className="text-sm text-slate-600 space-y-1">
                              {authority_review.concerns.map((c, i) => (
                                <li key={i}>• {c}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        <p className="text-xs text-slate-500 mt-3">
                          Reviewed on {formatDate(authority_review.created_at)}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {community_review && (
                <Card className="border-0 shadow-xl">
                  <CardHeader>
                    <CardTitle className="text-2xl flex items-center">
                      <Eye className="h-6 w-6 mr-2" />
                      Community Review
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-start space-x-4">
                      <div className={`p-3 rounded-2xl ${
                        community_review.decision === 'approve' 
                          ? 'bg-emerald-100 text-emerald-600' 
                          : 'bg-red-100 text-red-600'
                      }`}>
                        {community_review.decision === 'approve' ? (
                          <CheckCircle className="h-6 w-6" />
                        ) : (
                          <XCircle className="h-6 w-6" />
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-3">
                          <Badge className={
                            community_review.decision === 'approve' 
                              ? 'bg-emerald-100 text-emerald-800' 
                              : 'bg-red-100 text-red-800'
                          }>
                            {community_review.decision === 'approve' ? 'Approved' : 'Rejected'}
                          </Badge>
                          <span className="text-sm text-slate-600">
                            by {community_review.reviewer_id}
                          </span>
                        </div>
                        
                        {community_review.notes && (
                          <p className="text-slate-700 mb-3 leading-relaxed">{community_review.notes}</p>
                        )}
                        
                        <p className="text-xs text-slate-500">
                          Reviewed on {formatDate(community_review.created_at)}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-8">
              {/* Timeline */}
              <ClaimTimeline claim={claim} />

              {/* Mint Button or Credit Status */}
              {can_mint && !minted_credit ? (
                <Card className="border-0 shadow-xl bg-gradient-to-br from-emerald-50 to-green-50">
                  <CardHeader>
                    <CardTitle className="text-2xl flex items-center">
                      <Coins className="h-6 w-6 mr-2" />
                      Mint Carbon Credits
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="p-4 bg-white/60 rounded-xl">
                        <div className="text-sm text-slate-600 mb-2">Eligible Amount</div>
                        <div className="text-2xl font-bold text-emerald-900">
                          {verification?.verified_impact?.point_estimate_tonnes_co2e 
                            ? formatCO2e(verification.verified_impact.point_estimate_tonnes_co2e)
                            : verification?.verified_impact
                            ? `${formatCO2e(verification.verified_impact.min_tonnes_co2e)} - ${formatCO2e(verification.verified_impact.max_tonnes_co2e)}`
                            : 'N/A'}
                        </div>
                        <div className="text-xs text-slate-500 mt-1">Based on verified impact</div>
                      </div>
                      
                      <Button
                        onClick={handleMint}
                        disabled={minting}
                        className="w-full bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 shadow-lg"
                      >
                        <Coins className="h-4 w-4 mr-2" />
                        {minting ? 'Minting...' : 'Mint Credits'}
                      </Button>
                      
                      <p className="text-xs text-slate-600 text-center">
                        {mint_eligibility_reason}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ) : minted_credit ? (
                <Card className="border-0 shadow-xl bg-gradient-to-br from-primary-50 to-primary-100">
                  <CardHeader>
                    <CardTitle className="text-2xl flex items-center">
                      <TrendingUp className="h-6 w-6 mr-2" />
                      Carbon Credits
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center space-y-4">
                      <div>
                        <div className="text-4xl font-bold text-primary-900 mb-1">
                          {minted_credit.amount_tonnes_co2e.toFixed(1)}
                        </div>
                        <p className="text-sm text-primary-700">Credits Issued (tCO₂e)</p>
                      </div>
                      
                      <div>
                        <div className="text-2xl font-bold text-primary-900 mb-1">
                          {credit_remaining_co2e?.toFixed(1) || minted_credit.remaining_tonnes_co2e.toFixed(1)}
                        </div>
                        <p className="text-sm text-primary-700">Remaining (tCO₂e)</p>
                      </div>
                      
                      <Badge 
                        className={`${
                          credit_status === 'active' || minted_credit.status === 'active'
                            ? 'bg-emerald-100 text-emerald-800'
                            : minted_credit.status === 'at_risk'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        } text-sm px-4 py-1.5`}
                      >
                        {credit_status || minted_credit.status}
                      </Badge>
                      
                      <div className="text-xs text-slate-600 space-y-1 pt-4 border-t border-primary-200">
                        <div className="flex justify-between">
                          <span>Minted:</span>
                          <span>{formatDate(minted_credit.minted_at)}</span>
                        </div>
                        {minted_credit.baseline_ndvi && (
                          <div className="flex justify-between">
                            <span>Baseline NDVI:</span>
                            <span>{minted_credit.baseline_ndvi.toFixed(3)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : null}

              {/* Verification */}
              {verification && (
                <Card className="border-0 shadow-xl">
                  <CardHeader>
                    <CardTitle className="text-xl">Verification</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3 text-sm">
                      <div>
                        <div className="text-slate-600 mb-1">Status</div>
                        <Badge className="bg-blue-100 text-blue-800">
                          {verification.status}
                        </Badge>
                      </div>
                      {verification.outcome && (
                        <div>
                          <div className="text-slate-600 mb-1">Outcome</div>
                          <Badge className={
                            verification.outcome === 'approved'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-red-100 text-red-800'
                          }>
                            {verification.outcome}
                          </Badge>
                        </div>
                      )}
                      {verification.verified_impact && (
                        <div>
                          <div className="text-slate-600 mb-1">Verified Impact</div>
                          <div className="font-semibold text-slate-900">
                            {formatCO2e(verification.verified_impact.min_tonnes_co2e)} - {formatCO2e(verification.verified_impact.max_tonnes_co2e)}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </motion.div>
      </PageContainer>
    </div>
  );
};

export default ClaimDetail;
