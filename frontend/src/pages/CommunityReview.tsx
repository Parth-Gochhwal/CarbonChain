import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Users, 
  MessageSquare, 
  Eye, 
  ThumbsUp, 
  ThumbsDown,
  Calendar,
  MapPin,
  Leaf,
  CheckCircle,
  AlertCircle,
  Shield
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

const CommunityReview: React.FC = () => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [claimData, setClaimData] = useState<PublicClaimResponse | null>(null);
  const [reviewData, setReviewData] = useState<ReviewSubmission>({
    claim_id: '',
    reviewer_id: 'Community Member',
    decision: 'approve',
    confidence_score: 0.8,
    positives: [''],
    concerns: [''],
    notes: '',
  });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [loadingClaimData, setLoadingClaimData] = useState(false);

  useEffect(() => {
    fetchClaims();
  }, []);

  const fetchClaims = async () => {
    try {
      setLoading(true);
      const allClaims = await claimsApi.getClaims();
      // Filter claims that are open for community review (ONLY authority_reviewed status)
      const reviewableClaims = allClaims.filter(claim => 
        claim.status === 'authority_reviewed'
      );
      setClaims(reviewableClaims);
    } catch (error) {
      console.error('Error fetching claims:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClaimSelect = async (claim: Claim) => {
    setSelectedClaim(claim);
    setReviewData(prev => ({ ...prev, claim_id: claim.id }));
    
    // Fetch full claim data including AI + authority review
    try {
      setLoadingClaimData(true);
      const data = await claimsApi.getPublicClaim(claim.id);
      setClaimData(data);
    } catch (error) {
      console.error('Error fetching claim data:', error);
    } finally {
      setLoadingClaimData(false);
    }
  };

  const handleSubmitReview = async (decision: 'approve' | 'reject') => {
    if (!selectedClaim || !reviewData.notes?.trim()) return;

    try {
      setSubmitting(true);
      const submission: ReviewSubmission = {
        ...reviewData,
        claim_id: selectedClaim.id,
        decision,
      };
      
      await reviewApi.submitCommunityReview(submission);
      
      // Refresh claims list
      await fetchClaims();
      setSelectedClaim(null);
      setClaimData(null);
      setReviewData({
        claim_id: '',
        reviewer_id: 'Community Member',
        decision: 'approve',
        confidence_score: 0.8,
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
      label: 'Open for Review',
      value: claims.length,
      icon: Eye,
      color: 'text-blue-600 bg-blue-100',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      label: 'Total Reviews',
      value: '47',
      icon: MessageSquare,
      color: 'text-emerald-600 bg-emerald-100',
      gradient: 'from-emerald-500 to-green-500'
    },
    {
      label: 'Community Members',
      value: '1.2k',
      icon: Users,
      color: 'text-purple-600 bg-purple-100',
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      label: 'Verified CO₂e',
      value: '2.4k',
      icon: Leaf,
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
          <div className="text-center">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h1 className="text-5xl md:text-6xl font-extrabold text-slate-900 mb-4">
                Community Review
              </h1>
              <p className="text-xl text-slate-600 mb-8 max-w-3xl mx-auto leading-relaxed">
                Join the community in reviewing approved carbon credit claims. 
                Your feedback helps maintain transparency and trust in the verification process.
              </p>
              
              <div className="inline-flex items-center justify-center space-x-3 px-6 py-3 bg-gradient-to-r from-purple-50 to-pink-50 rounded-2xl border-2 border-purple-200 shadow-lg">
                <Users className="h-6 w-6 text-purple-600" />
                <span className="text-purple-700 font-semibold text-lg">Community Powered</span>
              </div>
            </motion.div>
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
                  <Eye className="h-6 w-6 mr-2 text-blue-600" />
                  <span>Claims Open for Review ({claims.length})</span>
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
                    <MessageSquare className="h-16 w-16 mx-auto mb-4 text-slate-300" />
                    <p className="text-lg font-medium">No claims available for review</p>
                    <p className="text-sm mt-2">All claims have been reviewed or are pending authority approval</p>
                  </div>
                ) : (
                  <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                    {claims.map((claim) => (
                      <motion.div
                        key={claim.id}
                        whileHover={{ scale: 1.01, x: 4 }}
                        className={`p-5 border-2 rounded-2xl cursor-pointer transition-all ${
                          selectedClaim?.id === claim.id
                            ? 'border-purple-500 bg-gradient-to-br from-purple-50 to-pink-50 shadow-lg'
                            : 'border-slate-200 hover:border-purple-300 bg-white'
                        }`}
                        onClick={() => handleClaimSelect(claim)}
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
                            <Calendar className="h-4 w-4" />
                            <span>{formatDate(claim.created_at)}</span>
                          </div>
                          {claim.location && (
                            <div className="flex items-center space-x-2">
                              <MapPin className="h-4 w-4" />
                              <span>{claim.location.latitude.toFixed(2)}, {claim.location.longitude.toFixed(2)}</span>
                            </div>
                          )}
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
                  <MessageSquare className="h-6 w-6 mr-2 text-emerald-600" />
                  <span>Submit Review</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loadingClaimData ? (
                  <div className="text-center py-12">
                    <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-slate-600">Loading claim details...</p>
                  </div>
                ) : selectedClaim ? (
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

                    {/* AI Verdict */}
                    {claimData?.ai_verdict && (
                      <div className="p-5 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl border border-blue-200">
                        <h4 className="font-bold text-slate-900 mb-3 flex items-center">
                          <Shield className="h-5 w-5 mr-2 text-blue-600" />
                          AI Consistency Verdict
                        </h4>
                        <div className="grid grid-cols-2 gap-4 mb-3">
                          <div>
                            <div className="text-xs text-slate-600 mb-1">Verdict</div>
                            <Badge className={
                              claimData.ai_verdict.verdict === 'strongly_supports'
                                ? 'bg-emerald-100 text-emerald-800'
                                : claimData.ai_verdict.verdict === 'partially_supports'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-red-100 text-red-800'
                            }>
                              {claimData.ai_verdict.verdict.replace('_', ' ')}
                            </Badge>
                          </div>
                          <div>
                            <div className="text-xs text-slate-600 mb-1">Confidence</div>
                            <div className="text-sm font-bold text-slate-900">
                              {(claimData.ai_verdict.confidence_score * 100).toFixed(0)}%
                            </div>
                          </div>
                        </div>
                        <div className="text-xs text-slate-700 mb-2">
                          <strong>AI Estimate:</strong> {formatCO2e(claimData.ai_verdict.estimated_min_co2e)} - {formatCO2e(claimData.ai_verdict.estimated_max_co2e)}
                        </div>
                        <div className="text-xs text-slate-700">
                          <strong>Deviation:</strong> {claimData.ai_verdict.deviation_percent >= 0 ? '+' : ''}{claimData.ai_verdict.deviation_percent.toFixed(1)}%
                        </div>
                      </div>
                    )}

                    {/* Authority Review */}
                    {claimData?.authority_review && (
                      <div className="p-5 bg-gradient-to-br from-emerald-50 to-green-50 rounded-2xl border border-emerald-200">
                        <h4 className="font-bold text-slate-900 mb-3 flex items-center">
                          <Shield className="h-5 w-5 mr-2 text-emerald-600" />
                          Authority Review
                        </h4>
                        <div className="mb-3">
                          <Badge className={
                            claimData.authority_review.decision === 'approve'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-red-100 text-red-800'
                          }>
                            {claimData.authority_review.decision === 'approve' ? 'Approved' : 'Rejected'}
                          </Badge>
                          <span className="text-xs text-slate-600 ml-2">
                            by {claimData.authority_review.reviewer_id}
                          </span>
                        </div>
                        {claimData.authority_review.notes && (
                          <p className="text-sm text-slate-700 mb-3">{claimData.authority_review.notes}</p>
                        )}
                        {claimData.authority_review.positives.length > 0 && (
                          <div className="mb-2">
                            <div className="text-xs font-semibold text-emerald-700 mb-1">Positives:</div>
                            <ul className="text-xs text-slate-600 space-y-1">
                              {claimData.authority_review.positives.map((p, i) => (
                                <li key={i}>• {p}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {claimData.authority_review.concerns.length > 0 && (
                          <div>
                            <div className="text-xs font-semibold text-red-700 mb-1">Concerns:</div>
                            <ul className="text-xs text-slate-600 space-y-1">
                              {claimData.authority_review.concerns.map((c, i) => (
                                <li key={i}>• {c}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}

                    {/* SYSTEM_AI Evidence Summary */}
                    {claimData?.evidence && claimData.evidence.filter(e => e.type === 'system_ai').length > 0 && (
                      <div className="p-5 bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl border border-purple-200">
                        <h4 className="font-bold text-slate-900 mb-3 flex items-center">
                          <Shield className="h-5 w-5 mr-2 text-purple-600" />
                          AI MRV Evidence ({claimData.evidence.filter(e => e.type === 'system_ai').length})
                        </h4>
                        <div className="space-y-2">
                          {claimData.evidence
                            .filter(e => e.type === 'system_ai')
                            .map((ev) => (
                              <div key={ev.id} className="text-xs text-slate-700">
                                <div className="font-semibold">{ev.title}</div>
                                {ev.hash && (
                                  <div className="text-slate-500 font-mono text-xs mt-1">
                                    Hash: {ev.hash.substring(0, 16)}...
                                  </div>
                                )}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    <Link to={`/claim/${selectedClaim.id}`}>
                      <Button variant="outline" className="w-full mb-4">
                        <Eye className="h-4 w-4 mr-2" />
                        View Full Details
                      </Button>
                    </Link>

                    {/* Review Form */}
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        Your Name/Identifier
                      </label>
                      <Input
                        value={reviewData.reviewer_id}
                        onChange={(e) => setReviewData(prev => ({ ...prev, reviewer_id: e.target.value }))}
                        placeholder="Your name or identifier"
                        className="mb-4"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        Confidence Score (0.0 - 1.0)
                      </label>
                      <Input
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={reviewData.confidence_score || 0.8}
                        onChange={(e) => setReviewData(prev => ({ 
                          ...prev, 
                          confidence_score: parseFloat(e.target.value) || 0.8 
                        }))}
                        placeholder="0.8"
                        className="mb-4"
                      />
                      <p className="text-xs text-slate-500 mb-4">
                        Your confidence in this review decision (0.0 = no confidence, 1.0 = fully confident)
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        Review Notes *
                      </label>
                      <Textarea
                        value={reviewData.notes || ''}
                        onChange={(e) => setReviewData(prev => ({ ...prev, notes: e.target.value }))}
                        placeholder="Share your thoughts on this carbon credit claim. Consider the evidence quality, methodology, and impact credibility..."
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
                        onClick={() => handleSubmitReview('approve')}
                        disabled={!reviewData.notes?.trim() || submitting}
                        className="flex-1 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 shadow-lg"
                      >
                        <CheckCircle className="h-4 w-4 mr-2" />
                        {submitting ? 'Submitting...' : 'Approve'}
                      </Button>
                      
                      <Button
                        onClick={() => handleSubmitReview('reject')}
                        disabled={!reviewData.notes?.trim() || submitting}
                        className="flex-1 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 shadow-lg"
                      >
                        <AlertCircle className="h-4 w-4 mr-2" />
                        {submitting ? 'Submitting...' : 'Reject'}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-16 text-slate-500">
                    <MessageSquare className="h-16 w-16 mx-auto mb-4 text-slate-300" />
                    <p className="text-lg font-medium">Select a claim to review</p>
                    <p className="text-sm mt-2">Choose a claim from the list to begin your review</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Guidelines */}
          <Card className="border-0 shadow-xl bg-gradient-to-br from-purple-50 to-pink-50">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center">
                <Users className="h-6 w-6 mr-2" />
                Community Review Guidelines
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h4 className="font-bold text-slate-900 mb-4 text-lg flex items-center">
                    <ThumbsUp className="h-5 w-5 text-emerald-600 mr-2" />
                    What to Look For
                  </h4>
                  <ul className="text-sm text-slate-700 space-y-3">
                    <li className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-emerald-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Clear and comprehensive evidence</span>
                    </li>
                    <li className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-emerald-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Realistic carbon impact estimates</span>
                    </li>
                    <li className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-emerald-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Transparent methodology</span>
                    </li>
                    <li className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-emerald-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Verifiable project location</span>
                    </li>
                    <li className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-emerald-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Consistent with AI and authority reviews</span>
                    </li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-bold text-slate-900 mb-4 text-lg flex items-center">
                    <ThumbsDown className="h-5 w-5 text-red-600 mr-2" />
                    Red Flags
                  </h4>
                  <ul className="text-sm text-slate-700 space-y-3">
                    <li className="flex items-start">
                      <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Insufficient or unclear evidence</span>
                    </li>
                    <li className="flex items-start">
                      <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Unrealistic impact claims</span>
                    </li>
                    <li className="flex items-start">
                      <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Vague project descriptions</span>
                    </li>
                    <li className="flex items-start">
                      <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Inconsistent data or timelines</span>
                    </li>
                    <li className="flex items-start">
                      <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Potential greenwashing indicators</span>
                    </li>
                  </ul>
                </div>
              </div>
              
              <div className="mt-8 p-6 bg-white/60 rounded-2xl border border-purple-200">
                <p className="text-sm text-slate-800 leading-relaxed">
                  <strong className="text-purple-900">Remember:</strong> Your reviews help maintain the integrity of the carbon credit system. 
                  Be constructive, fair, and focus on the evidence and methodology presented. 
                  Community reviews are a crucial part of our transparent governance model.
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </PageContainer>
    </div>
  );
};

export default CommunityReview;
