import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Shield, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Eye, 
  Calendar,
  User,
  TrendingUp
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import PageContainer from '../components/layout/PageContainer';
import { claimsApi, reviewApi } from '../services/api';
import type { Claim, ReviewSubmission, PublicClaimResponse } from '../types';
import { formatDate, formatCO2e, getStatusColor, getStatusLabel } from '../lib/utils';

const AuthorityDashboard: React.FC = () => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [selectedClaimFull, setSelectedClaimFull] = useState<PublicClaimResponse | null>(null); // Full claim data with AI analysis
  const [reviewData, setReviewData] = useState<ReviewSubmission>({
    claim_id: '',
    reviewer_id: 'Authority Reviewer #001',
    decision: 'approve',
    positives: [''],
    concerns: [''],
    notes: '',
  });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchClaims();
  }, []);

  const fetchClaims = async () => {
    try {
      setLoading(true);
      const allClaims = await claimsApi.getClaims();
      // Filter for claims that need authority review (ai_verified status)
      // REAL MRV: Only show claims that have completed AI analysis with positive impact
      // Exclude ai_rejected claims (they don't need authority review)
      const pendingClaims = allClaims.filter(c => 
        c.status === 'ai_verified' || c.status === 'ai_analyzed' || c.status === 'verified'
      );
      setClaims(pendingClaims);
      console.log(`[Authority Dashboard] Found ${pendingClaims.length} claims ready for review (total: ${allClaims.length})`);
    } catch (error) {
      console.error('Error fetching claims:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (decision: 'approve' | 'reject') => {
    if (!selectedClaim || !reviewData.notes?.trim()) return;

    try {
      setSubmitting(true);
      const submission: ReviewSubmission = {
        ...reviewData,
        claim_id: selectedClaim.id,
        decision,
      };
      
      await reviewApi.submitAuthorityReview(submission);
      
      // Refresh claims list
      await fetchClaims();
      setSelectedClaim(null);
      setReviewData({
        claim_id: '',
        reviewer_id: 'Authority Reviewer #001',
        decision: 'approve',
        positives: [''],
        concerns: [''],
        notes: '',
      });
    } catch (error: any) {
      console.error('Error submitting review:', error);
      alert(error.response?.data?.detail || 'Failed to submit review');
    } finally {
      setSubmitting(false);
    }
  };

  const stats = [
    {
      label: 'Pending Reviews',
      value: claims.length,
      icon: Clock,
      color: 'text-yellow-600 bg-yellow-100',
      gradient: 'from-yellow-500 to-orange-500'
    },
    {
      label: 'Approved Today',
      value: '12',
      icon: CheckCircle,
      color: 'text-emerald-600 bg-emerald-100',
      gradient: 'from-emerald-500 to-green-500'
    },
    {
      label: 'Total CO₂e Verified',
      value: '2.4k',
      icon: TrendingUp,
      color: 'text-blue-600 bg-blue-100',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      label: 'Trust Score',
      value: '98.5%',
      icon: Shield,
      color: 'text-primary-600 bg-primary-100',
      gradient: 'from-primary-500 to-primary-700'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      <PageContainer className="py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-5xl font-extrabold text-slate-900 mb-3">
                Authority Dashboard
              </h1>
              <p className="text-xl text-slate-600">
                Review and validate carbon credit claims with expert oversight
              </p>
            </div>
            
            <div className="flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-primary-50 to-primary-100 rounded-2xl border-2 border-primary-200 shadow-lg">
              <Shield className="h-6 w-6 text-primary-600" />
              <span className="text-primary-700 font-semibold">Certified Authority</span>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ y: -4, scale: 1.02 }}
                >
                  <Card className="border-0 shadow-xl hover:shadow-2xl transition-all bg-white">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-slate-600 mb-2">{stat.label}</p>
                          <p className="text-3xl font-bold text-slate-900">{stat.value}</p>
                        </div>
                        <div className={`p-4 rounded-2xl bg-gradient-to-br ${stat.gradient} shadow-lg`}>
                          <Icon className="h-7 w-7 text-white" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Claims List */}
            <Card className="border-0 shadow-xl">
              <CardHeader>
                <CardTitle className="text-2xl flex items-center">
                  <Clock className="h-6 w-6 mr-2 text-yellow-600" />
                  <span>Pending Reviews ({claims.length})</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-12">
                    <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-slate-600">Loading claims...</p>
                  </div>
                ) : claims.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <CheckCircle className="h-16 w-16 mx-auto mb-4 text-slate-300" />
                    <p className="text-lg font-medium">No claims pending review</p>
                    <p className="text-sm mt-2">All claims have been reviewed</p>
                  </div>
                ) : (
                  <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                    {claims.map((claim) => (
                      <motion.div
                        key={claim.id}
                        whileHover={{ scale: 1.01, x: 4 }}
                        className={`p-5 border-2 rounded-2xl cursor-pointer transition-all ${
                          selectedClaim?.id === claim.id
                            ? 'border-primary-500 bg-gradient-to-br from-primary-50 to-primary-100 shadow-lg'
                            : 'border-slate-200 hover:border-primary-300 bg-white'
                        }`}
                        onClick={async () => {
                          setSelectedClaim(claim);
                          setReviewData(prev => ({ ...prev, claim_id: claim.id }));
                          // Fetch full claim data with AI analysis
                          try {
                            const fullData = await claimsApi.getPublicClaim(claim.id);
                            setSelectedClaimFull(fullData);
                          } catch (error) {
                            console.error('Error fetching full claim data:', error);
                            setSelectedClaimFull(null);
                          }
                        }}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <h4 className="font-semibold text-slate-900 flex-1 text-lg">
                            {claim.title}
                          </h4>
                          <Badge className={`${getStatusColor(claim.status)} ml-2`}>
                            {getStatusLabel(claim.status)}
                          </Badge>
                        </div>
                        
                        <p className="text-sm text-slate-600 mb-4 line-clamp-2">
                          {claim.description.substring(0, 120)}...
                        </p>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm text-slate-600 mb-3">
                          <div className="flex items-center space-x-2">
                            <User className="h-4 w-4" />
                            <span className="truncate">{claim.submitter_name}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Calendar className="h-4 w-4" />
                            <span>{formatDate(claim.created_at)}</span>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between pt-3 border-t border-slate-200">
                          <div className="text-sm">
                            <span className="font-semibold text-primary-900 text-base">
                              {formatCO2e(claim.carbon_impact_estimate.min_tonnes_co2e)} - {formatCO2e(claim.carbon_impact_estimate.max_tonnes_co2e)}
                            </span>
                          </div>
                          
                          <Link to={`/claim/${claim.id}`}>
                            <Button variant="ghost" size="sm" className="flex items-center">
                              <Eye className="h-4 w-4 mr-1" />
                              View
                            </Button>
                          </Link>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Review Panel */}
            <Card className="border-0 shadow-xl">
              <CardHeader>
                <CardTitle className="text-2xl flex items-center">
                  <Eye className="h-6 w-6 mr-2 text-blue-600" />
                  <span>Claim Review</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {selectedClaim ? (
                  <div className="space-y-6">
                    {/* Claim Summary */}
                    <div className="p-5 bg-gradient-to-br from-slate-50 to-slate-100 rounded-2xl">
                      <h3 className="font-bold text-slate-900 mb-2 text-lg">
                        {selectedClaim.title}
                      </h3>
                      <p className="text-sm text-slate-600 mb-4 line-clamp-3">
                        {selectedClaim.description}
                      </p>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-semibold text-slate-700">Carbon Impact:</span>
                          <div className="text-primary-900 font-bold mt-1">
                            {formatCO2e(selectedClaim.carbon_impact_estimate.min_tonnes_co2e)} - {formatCO2e(selectedClaim.carbon_impact_estimate.max_tonnes_co2e)}
                          </div>
                        </div>
                        <div>
                          <span className="font-semibold text-slate-700">Project Type:</span>
                          <div className="text-slate-900 font-medium mt-1 capitalize">
                            {selectedClaim.claim_type.replace('_', ' ')}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* AI Analysis Section */}
                    {selectedClaimFull && (selectedClaimFull.verification || selectedClaimFull.ai_verdict) && (
                      <div className="p-5 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl border-2 border-blue-200">
                        <h3 className="font-bold text-slate-900 mb-3 text-lg flex items-center">
                          <Shield className="h-5 w-5 mr-2 text-blue-600" />
                          AI Analysis Results
                        </h3>
                        
                        {selectedClaimFull.verification && selectedClaimFull.verification.verified_impact && (
                          <div className="mb-4 space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                              <div className="text-sm">
                                <span className="font-semibold text-slate-700">AI Verified CO₂ Range:</span>
                                <div className="text-blue-900 font-bold mt-1">
                                  {formatCO2e(selectedClaimFull.verification.verified_impact.min_tonnes_co2e)} - {formatCO2e(selectedClaimFull.verification.verified_impact.max_tonnes_co2e)} tCO₂e
                                </div>
                              </div>
                              <div className="text-sm">
                                <span className="font-semibold text-slate-700">Confidence Level:</span>
                                <div className="text-slate-900 font-medium mt-1 capitalize">
                                  {selectedClaimFull.verification.verified_impact.confidence}
                                </div>
                              </div>
                            </div>
                            
                            {/* Extract NDVI values from methodology_used if available */}
                            {selectedClaimFull.verification.verified_impact.methodology_used && (
                              <div className="text-xs text-slate-600 p-2 bg-white/60 rounded">
                                <div className="font-semibold mb-1">NDVI Analysis:</div>
                                {(() => {
                                  const methodology = selectedClaimFull.verification.verified_impact.methodology_used;
                                  const ndviMatch = methodology.match(/NDVI delta: ([+-]?\d+\.\d+)/);
                                  const baselineMatch = methodology.match(/Baseline=([\d.]+)/);
                                  const monitoringMatch = methodology.match(/Monitoring=([\d.]+)/);
                                  
                                  return (
                                    <div className="space-y-1">
                                      {baselineMatch && (
                                        <div>Baseline NDVI: {parseFloat(baselineMatch[1]).toFixed(4)}</div>
                                      )}
                                      {monitoringMatch && (
                                        <div>Monitoring NDVI: {parseFloat(monitoringMatch[1]).toFixed(4)}</div>
                                      )}
                                      {ndviMatch && (
                                        <div className="font-semibold">Delta NDVI: {parseFloat(ndviMatch[1]).toFixed(4)}</div>
                                      )}
                                    </div>
                                  );
                                })()}
                              </div>
                            )}
                            
                            {selectedClaimFull.verification.summary && (
                              <div className="text-xs text-slate-600 mt-2 p-2 bg-white/60 rounded">
                                <div className="font-semibold mb-1">Verification Summary:</div>
                                {selectedClaimFull.verification.summary}
                              </div>
                            )}
                            
                            {selectedClaimFull.verification.verification_notes && (
                              <div className="text-xs text-slate-600 mt-2 p-2 bg-white/60 rounded">
                                <div className="font-semibold mb-1">Verification Notes:</div>
                                {selectedClaimFull.verification.verification_notes}
                              </div>
                            )}
                          </div>
                        )}
                        
                        {selectedClaimFull.ai_verdict && (
                          <div className="space-y-3 border-t border-blue-200 pt-3">
                            <div className="grid grid-cols-2 gap-3">
                              <div className="text-sm">
                                <span className="font-semibold text-slate-700">Consistency Verdict:</span>
                                <div className="text-slate-900 font-bold mt-1 capitalize">
                                  {selectedClaimFull.ai_verdict.verdict.replace('_', ' ')}
                                </div>
                              </div>
                              <div className="text-sm">
                                <span className="font-semibold text-slate-700">Confidence Score:</span>
                                <div className="text-blue-900 font-bold mt-1">
                                  {typeof selectedClaimFull.ai_verdict.confidence_score === 'number' && !isNaN(selectedClaimFull.ai_verdict.confidence_score)
                                    ? `${(selectedClaimFull.ai_verdict.confidence_score * 100).toFixed(0)}%`
                                    : 'N/A'}
                                </div>
                              </div>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-3">
                              <div className="text-sm">
                                <span className="font-semibold text-slate-700">Claimed CO₂ Range:</span>
                                <div className="text-slate-900 font-medium mt-1">
                                  {formatCO2e(selectedClaimFull.ai_verdict.claimed_min_co2e)} - {formatCO2e(selectedClaimFull.ai_verdict.claimed_max_co2e)} tCO₂e
                                </div>
                              </div>
                              <div className="text-sm">
                                <span className="font-semibold text-slate-700">AI Estimated CO₂ Range:</span>
                                <div className="text-blue-900 font-bold mt-1">
                                  {formatCO2e(selectedClaimFull.ai_verdict.estimated_min_co2e)} - {formatCO2e(selectedClaimFull.ai_verdict.estimated_max_co2e)} tCO₂e
                                </div>
                              </div>
                            </div>
                            
                            <div className="text-sm">
                              <span className="font-semibold text-slate-700">Deviation from Claim:</span>
                              <div className={`font-bold mt-1 ${selectedClaimFull.ai_verdict.deviation_percent >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                {typeof selectedClaimFull.ai_verdict.deviation_percent === 'number' && !isNaN(selectedClaimFull.ai_verdict.deviation_percent)
                                  ? `${selectedClaimFull.ai_verdict.deviation_percent >= 0 ? '+' : ''}${selectedClaimFull.ai_verdict.deviation_percent.toFixed(1)}%`
                                  : 'N/A'}
                              </div>
                            </div>
                            
                            {selectedClaimFull.ai_verdict.explanation && (
                              <div className="text-xs text-slate-600 mt-2 p-2 bg-white/60 rounded">
                                <div className="font-semibold mb-1">AI Explanation:</div>
                                {selectedClaimFull.ai_verdict.explanation}
                              </div>
                            )}
                            
                            {selectedClaimFull.ai_verdict.ndvi_analysis && (
                              <div className="text-xs text-slate-600 mt-2 p-2 bg-white/60 rounded">
                                <div className="font-semibold mb-1">NDVI Analysis:</div>
                                <div className="space-y-1">
                                  <div>Baseline NDVI: {selectedClaimFull.ai_verdict.ndvi_analysis.baseline_ndvi?.toFixed(4) || 'N/A'}</div>
                                  <div>Monitoring NDVI: {selectedClaimFull.ai_verdict.ndvi_analysis.current_ndvi?.toFixed(4) || 'N/A'}</div>
                                  <div className="font-semibold">Delta NDVI: {selectedClaimFull.ai_verdict.ndvi_analysis.delta_ndvi?.toFixed(4) || 'N/A'}</div>
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Review Form */}
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        Reviewer ID
                      </label>
                      <Input
                        value={reviewData.reviewer_id}
                        onChange={(e) => setReviewData(prev => ({ ...prev, reviewer_id: e.target.value }))}
                        placeholder="Your reviewer identifier"
                        className="mb-4"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        Review Notes *
                      </label>
                      <Textarea
                        value={reviewData.notes || ''}
                        onChange={(e) => setReviewData(prev => ({ ...prev, notes: e.target.value }))}
                        placeholder="Provide detailed notes about your review decision..."
                        rows={5}
                        className="mb-4"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        Positive Points (Optional)
                      </label>
                      {reviewData.positives?.map((positive, index) => (
                        <Input
                          key={index}
                          value={positive}
                          onChange={(e) => {
                            const newPositives = [...(reviewData.positives || [])];
                            newPositives[index] = e.target.value;
                            setReviewData(prev => ({ ...prev, positives: newPositives }));
                          }}
                          placeholder={`Positive point ${index + 1}`}
                          className="mb-2"
                        />
                      ))}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setReviewData(prev => ({ 
                          ...prev, 
                          positives: [...(prev.positives || []), ''] 
                        }))}
                      >
                        + Add Positive Point
                      </Button>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        Concerns (Optional)
                      </label>
                      {reviewData.concerns?.map((concern, index) => (
                        <Input
                          key={index}
                          value={concern}
                          onChange={(e) => {
                            const newConcerns = [...(reviewData.concerns || [])];
                            newConcerns[index] = e.target.value;
                            setReviewData(prev => ({ ...prev, concerns: newConcerns }));
                          }}
                          placeholder={`Concern ${index + 1}`}
                          className="mb-2"
                        />
                      ))}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setReviewData(prev => ({ 
                          ...prev, 
                          concerns: [...(prev.concerns || []), ''] 
                        }))}
                      >
                        + Add Concern
                      </Button>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex space-x-3 pt-4">
                      <Button
                        onClick={() => handleReview('approve')}
                        disabled={!reviewData.notes?.trim() || submitting}
                        className="flex-1 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 shadow-lg"
                      >
                        <CheckCircle className="h-4 w-4 mr-2" />
                        {submitting ? 'Submitting...' : 'Approve'}
                      </Button>
                      
                      <Button
                        onClick={() => handleReview('reject')}
                        disabled={!reviewData.notes?.trim() || submitting}
                        className="flex-1 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 shadow-lg"
                      >
                        <XCircle className="h-4 w-4 mr-2" />
                        {submitting ? 'Submitting...' : 'Reject'}
                      </Button>
                    </div>

                    {/* View Full Details */}
                    <Link to={`/claim/${selectedClaim.id}`}>
                      <Button variant="outline" className="w-full">
                        <Eye className="h-4 w-4 mr-2" />
                        View Full Details
                      </Button>
                    </Link>
                  </div>
                ) : (
                  <div className="text-center py-16 text-slate-500">
                    <Eye className="h-16 w-16 mx-auto mb-4 text-slate-300" />
                    <p className="text-lg font-medium">Select a claim to review</p>
                    <p className="text-sm mt-2">Choose a claim from the list to begin review</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Guidelines */}
          <Card className="border-0 shadow-xl bg-gradient-to-br from-blue-50 to-cyan-50">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center">
                <Shield className="h-6 w-6 mr-2" />
                Authority Review Guidelines
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h4 className="font-bold text-slate-900 mb-4 text-lg">Approval Criteria</h4>
                  <ul className="text-sm text-slate-700 space-y-3">
                    <li className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-emerald-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>AI verification shows high confidence alignment</span>
                    </li>
                    <li className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-emerald-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Evidence clearly supports claimed carbon impact</span>
                    </li>
                    <li className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-emerald-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Project methodology is scientifically sound</span>
                    </li>
                    <li className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-emerald-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Location and timeline are verifiable</span>
                    </li>
                    <li className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-emerald-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Additionality requirements are met</span>
                    </li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-bold text-slate-900 mb-4 text-lg">Rejection Reasons</h4>
                  <ul className="text-sm text-slate-700 space-y-3">
                    <li className="flex items-start">
                      <XCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Insufficient or unclear evidence</span>
                    </li>
                    <li className="flex items-start">
                      <XCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Overestimated carbon impact claims</span>
                    </li>
                    <li className="flex items-start">
                      <XCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Methodology concerns or gaps</span>
                    </li>
                    <li className="flex items-start">
                      <XCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Potential double counting issues</span>
                    </li>
                    <li className="flex items-start">
                      <XCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Non-additional activities</span>
                    </li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </PageContainer>
    </div>
  );
};

export default AuthorityDashboard;
