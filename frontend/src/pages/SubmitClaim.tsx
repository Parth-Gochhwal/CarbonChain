import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
  CheckCircle, 
  AlertCircle, 
  ArrowRight, 
  ArrowLeft,
  MapPin,
  FileText,
  Upload,
  Leaf,
  Sparkles
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import PageContainer from '../components/layout/PageContainer';
import MapSelector from '../components/claim/MapSelector';
import EvidenceUploader from '../components/claim/EvidenceUploader';
import { claimsApi } from '../services/api';
import type { ClaimSubmission, ClaimType } from '../types';

interface FormData {
  claim_type: ClaimType;
  title: string;
  description: string;
  location?: { lat: number; lng: number; polygon?: [number, number][] };
  geometry_geojson?: any;
  area_hectares?: number;
  carbon_impact_estimate: {
    min_tonnes_co2e: number;
    max_tonnes_co2e: number;
    estimation_methodology?: string;
    time_horizon_years: number;
  };
  action_start_date: string;
  action_end_date?: string;
  stated_assumptions: string[];
  known_limitations: string[];
  submitter_name: string;
  submitter_contact?: string;
  evidenceFiles: File[];
}

const CLAIM_TYPES: { value: ClaimType; label: string; icon: string }[] = [
  { value: 'mangrove_restoration', label: 'Mangrove Restoration', icon: '🌊' },
  { value: 'reforestation', label: 'Reforestation', icon: '🌳' },
  { value: 'solar_installation', label: 'Solar Installation', icon: '☀️' },
  { value: 'wind_installation', label: 'Wind Installation', icon: '💨' },
  { value: 'wetland_restoration', label: 'Wetland Restoration', icon: '🌿' },
  { value: 'avoided_deforestation', label: 'Avoided Deforestation', icon: '🛡️' },
  { value: 'other', label: 'Other', icon: '📋' },
];

const SubmitClaim: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadingEvidence, setUploadingEvidence] = useState(false);
  
  const [formData, setFormData] = useState<FormData>({
    claim_type: 'reforestation',
    title: '',
    description: '',
    carbon_impact_estimate: {
      min_tonnes_co2e: 0,
      max_tonnes_co2e: 0,
      time_horizon_years: 1,
    },
    action_start_date: new Date().toISOString().split('T')[0],
    stated_assumptions: [''],
    known_limitations: [''],
    submitter_name: '',
    evidenceFiles: [],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const steps = [
    { id: 1, title: 'Project Type', description: 'Select your climate action type', icon: Leaf },
    { id: 2, title: 'Details', description: 'Describe your project', icon: FileText },
    { id: 3, title: 'Location', description: 'Select project location', icon: MapPin },
    { id: 4, title: 'Impact', description: 'Estimate carbon impact', icon: Sparkles },
    { id: 5, title: 'Evidence', description: 'Upload supporting files', icon: Upload },
    { id: 6, title: 'Review', description: 'Review and submit', icon: CheckCircle },
  ];

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};

    switch (step) {
      case 1:
        if (!formData.claim_type) newErrors.claim_type = 'Please select a project type';
        break;
      
      case 2:
        if (!formData.title.trim()) newErrors.title = 'Title is required';
        if (formData.title.length < 5) newErrors.title = 'Title must be at least 5 characters';
        if (!formData.description.trim()) newErrors.description = 'Description is required';
        if (formData.description.length < 20) newErrors.description = 'Description must be at least 20 characters';
        if (!formData.submitter_name.trim()) newErrors.submitter_name = 'Your name is required';
        break;
      
      case 3:
        if (!formData.location && !formData.geometry_geojson) {
          newErrors.location = 'Please select a location on the map';
        }
        break;
      
      case 4:
        if (formData.carbon_impact_estimate.min_tonnes_co2e <= 0) {
          newErrors.carbon_impact = 'Minimum CO₂ impact must be greater than 0';
        }
        if (formData.carbon_impact_estimate.max_tonnes_co2e <= formData.carbon_impact_estimate.min_tonnes_co2e) {
          newErrors.carbon_impact = 'Maximum CO₂ impact must be greater than minimum';
        }
        if (!formData.action_start_date) {
          newErrors.action_start_date = 'Action start date is required';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, steps.length));
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(4) || (!formData.location && !formData.geometry_geojson)) return;

    setIsSubmitting(true);
    try {
      // Prepare submission data
      const submission: ClaimSubmission = {
        claim_type: formData.claim_type,
        title: formData.title,
        description: formData.description,
        location: formData.location ? {
          latitude: formData.location.lat,
          longitude: formData.location.lng,
        } : undefined,
        geometry_geojson: formData.geometry_geojson,
        area_hectares: formData.area_hectares,
        carbon_impact_estimate: {
          min_tonnes_co2e: formData.carbon_impact_estimate.min_tonnes_co2e,
          max_tonnes_co2e: formData.carbon_impact_estimate.max_tonnes_co2e,
          estimation_methodology: formData.carbon_impact_estimate.estimation_methodology,
          time_horizon_years: formData.carbon_impact_estimate.time_horizon_years,
        },
        action_start_date: new Date(formData.action_start_date).toISOString(),
        action_end_date: formData.action_end_date ? new Date(formData.action_end_date).toISOString() : undefined,
        stated_assumptions: formData.stated_assumptions.filter(a => a.trim()),
        known_limitations: formData.known_limitations.filter(l => l.trim()),
        submitter_name: formData.submitter_name,
        submitter_contact: formData.submitter_contact,
      };

      // Create claim
      const claim = await claimsApi.submitClaim(submission);

      // Upload evidence files if any
      if (formData.evidenceFiles.length > 0) {
        setUploadingEvidence(true);
        try {
          await claimsApi.uploadEvidence(claim.id, formData.evidenceFiles);
        } catch (error) {
          console.error('Error uploading evidence:', error);
          // Continue even if evidence upload fails
        } finally {
          setUploadingEvidence(false);
        }
      }

      // Navigate to claim detail page immediately - it will handle AI analysis polling
      navigate(`/claim/${claim.id}`, { 
        state: { 
          message: 'Claim submitted successfully! AI analysis is starting...',
          aiAnalysisPending: claim.status === 'ai_analysis_pending' || claim.status === 'ai_analysis_in_progress'
        }
      });
    } catch (error: any) {
      console.error('Error submitting claim:', error);
      // Display backend error message instead of blank screen
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to submit claim. Please try again.';
      setErrors({ 
        submit: errorMessage
      });
      // Don't navigate on error - stay on form so user can see error and retry
    } finally {
      setIsSubmitting(false);
      setUploadingEvidence(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <Card className="border-0 shadow-xl">
              <CardHeader>
                <CardTitle className="text-2xl">Select Project Type</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {CLAIM_TYPES.map((type) => (
                    <motion.button
                      key={type.value}
                      whileHover={{ scale: 1.02, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setFormData(prev => ({ ...prev, claim_type: type.value }))}
                      className={`p-6 rounded-2xl border-2 text-left transition-all ${
                        formData.claim_type === type.value
                          ? 'border-primary-500 bg-primary-50 shadow-lg'
                          : 'border-gray-200 hover:border-primary-300 bg-white'
                      }`}
                    >
                      <div className="text-4xl mb-3">{type.icon}</div>
                      <div className="font-semibold text-gray-900">{type.label}</div>
                    </motion.button>
                  ))}
                </div>
                {errors.claim_type && (
                  <p className="mt-4 text-sm text-red-600 flex items-center">
                    <AlertCircle className="h-4 w-4 mr-1" />
                    {errors.claim_type}
                  </p>
                )}
              </CardContent>
            </Card>
          </motion.div>
        );

      case 2:
        return (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <Card className="border-0 shadow-xl">
              <CardHeader>
                <CardTitle className="text-2xl">Project Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Project Title *
                  </label>
                  <Input
                    value={formData.title}
                    onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="e.g., Amazon Rainforest Restoration Project"
                    className={errors.title ? 'border-red-500' : ''}
                  />
                  {errors.title && (
                    <p className="mt-1 text-sm text-red-600 flex items-center">
                      <AlertCircle className="h-4 w-4 mr-1" />
                      {errors.title}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Project Description *
                  </label>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe your carbon reduction project in detail. Include methodology, timeline, and expected outcomes..."
                    rows={8}
                    className={errors.description ? 'border-red-500' : ''}
                  />
                  <div className="flex justify-between mt-2">
                    {errors.description ? (
                      <p className="text-sm text-red-600 flex items-center">
                        <AlertCircle className="h-4 w-4 mr-1" />
                        {errors.description}
                      </p>
                    ) : (
                      <p className="text-sm text-gray-500">
                        {formData.description.length}/20 characters minimum
                      </p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Your Name *
                    </label>
                    <Input
                      value={formData.submitter_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, submitter_name: e.target.value }))}
                      placeholder="John Doe or Organization Name"
                      className={errors.submitter_name ? 'border-red-500' : ''}
                    />
                    {errors.submitter_name && (
                      <p className="mt-1 text-sm text-red-600 flex items-center">
                        <AlertCircle className="h-4 w-4 mr-1" />
                        {errors.submitter_name}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Contact Email (Optional)
                    </label>
                    <Input
                      type="email"
                      value={formData.submitter_contact || ''}
                      onChange={(e) => setFormData(prev => ({ ...prev, submitter_contact: e.target.value }))}
                      placeholder="contact@example.com"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        );

      case 3:
        return (
          <MapSelector
            onLocationSelect={(location) => {
              setFormData(prev => ({ 
                ...prev, 
                location,
                area_hectares: location.polygon ? calculateArea(location.polygon) : undefined
              }));
            }}
            initialLocation={formData.location}
          />
        );

      case 4:
        return (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <Card className="border-0 shadow-xl">
              <CardHeader>
                <CardTitle className="text-2xl">Carbon Impact Estimation</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Minimum CO₂e Reduction (tonnes) *
                    </label>
                    <Input
                      type="number"
                      min="0"
                      step="0.1"
                      value={formData.carbon_impact_estimate.min_tonnes_co2e || ''}
                      onChange={(e) => setFormData(prev => ({
                        ...prev,
                        carbon_impact_estimate: {
                          ...prev.carbon_impact_estimate,
                          min_tonnes_co2e: Number(e.target.value)
                        }
                      }))}
                      placeholder="0.0"
                      className={errors.carbon_impact ? 'border-red-500' : ''}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Maximum CO₂e Reduction (tonnes) *
                    </label>
                    <Input
                      type="number"
                      min="0"
                      step="0.1"
                      value={formData.carbon_impact_estimate.max_tonnes_co2e || ''}
                      onChange={(e) => setFormData(prev => ({
                        ...prev,
                        carbon_impact_estimate: {
                          ...prev.carbon_impact_estimate,
                          max_tonnes_co2e: Number(e.target.value)
                        }
                      }))}
                      placeholder="0.0"
                      className={errors.carbon_impact ? 'border-red-500' : ''}
                    />
                  </div>
                </div>

                {errors.carbon_impact && (
                  <p className="text-sm text-red-600 flex items-center">
                    <AlertCircle className="h-4 w-4 mr-1" />
                    {errors.carbon_impact}
                  </p>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Time Horizon (years) *
                    </label>
                    <Input
                      type="number"
                      min="1"
                      value={formData.carbon_impact_estimate.time_horizon_years}
                      onChange={(e) => setFormData(prev => ({
                        ...prev,
                        carbon_impact_estimate: {
                          ...prev.carbon_impact_estimate,
                          time_horizon_years: Number(e.target.value)
                        }
                      }))}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Action Start Date *
                    </label>
                    <Input
                      type="date"
                      value={formData.action_start_date}
                      onChange={(e) => setFormData(prev => ({ ...prev, action_start_date: e.target.value }))}
                      className={errors.action_start_date ? 'border-red-500' : ''}
                    />
                    {errors.action_start_date && (
                      <p className="mt-1 text-sm text-red-600">{errors.action_start_date}</p>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Estimation Methodology (Optional)
                  </label>
                  <Textarea
                    value={formData.carbon_impact_estimate.estimation_methodology || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      carbon_impact_estimate: {
                        ...prev.carbon_impact_estimate,
                        estimation_methodology: e.target.value
                      }
                    }))}
                    placeholder="Brief description of how the estimate was calculated (e.g., IPCC Tier 1 defaults)"
                    rows={3}
                  />
                </div>

                <div className="p-6 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-3 flex items-center">
                    <Sparkles className="h-5 w-5 mr-2" />
                    Estimation Guidelines
                  </h4>
                  <ul className="text-sm text-blue-800 space-y-2">
                    <li>• Provide conservative estimates based on scientific methodology</li>
                    <li>• Consider project timeline and permanence</li>
                    <li>• Account for leakage and additionality</li>
                    <li>• AI verification will validate your estimates</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        );

      case 5:
        return (
          <EvidenceUploader
            onFilesChange={(files) => setFormData(prev => ({ ...prev, evidenceFiles: files }))}
            maxFiles={20}
            acceptedTypes={['image/*', 'video/*']}
          />
        );

      case 6:
        return (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <Card className="border-0 shadow-xl">
              <CardHeader>
                <CardTitle className="text-2xl">Review Your Claim</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-semibold text-gray-900 text-lg">Project Details</h4>
                    <div className="space-y-2 text-sm">
                      <div><strong>Type:</strong> {CLAIM_TYPES.find(t => t.value === formData.claim_type)?.label}</div>
                      <div><strong>Title:</strong> {formData.title}</div>
                      <div><strong>Description:</strong> {formData.description.substring(0, 100)}...</div>
                      <div><strong>Submitter:</strong> {formData.submitter_name}</div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-semibold text-gray-900 text-lg">Carbon Impact</h4>
                    <div className="space-y-2 text-sm">
                      <div><strong>Range:</strong> {formData.carbon_impact_estimate.min_tonnes_co2e} - {formData.carbon_impact_estimate.max_tonnes_co2e} tCO₂e</div>
                      <div><strong>Time Horizon:</strong> {formData.carbon_impact_estimate.time_horizon_years} years</div>
                      <div><strong>Start Date:</strong> {new Date(formData.action_start_date).toLocaleDateString()}</div>
                      <div><strong>Evidence Files:</strong> {formData.evidenceFiles.length}</div>
                    </div>
                  </div>
                </div>

                {formData.location && (
                  <div className="p-4 bg-slate-50 rounded-xl">
                    <h4 className="font-semibold text-gray-900 mb-2">Location</h4>
                    <div className="text-sm text-gray-700">
                      <strong>Coordinates:</strong> {formData.location.lat.toFixed(6)}, {formData.location.lng.toFixed(6)}
                    </div>
                  </div>
                )}

                <div className="p-6 bg-gradient-to-br from-emerald-50 to-green-50 rounded-2xl border border-emerald-200">
                  <div className="flex items-center space-x-3 text-emerald-800 mb-2">
                    <CheckCircle className="h-6 w-6" />
                    <span className="font-semibold text-lg">Ready to Submit</span>
                  </div>
                  <p className="text-sm text-emerald-700">
                    Your claim will be processed by our AI verification system and then reviewed by certified authorities.
                  </p>
                </div>

                {errors.submit && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
                    <p className="text-sm text-red-600 flex items-center">
                      <AlertCircle className="h-4 w-4 mr-2" />
                      {errors.submit}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        );

      default:
        return null;
    }
  };

  const calculateArea = (polygon: [number, number][]): number => {
    if (polygon.length < 3) return 0;
    let area = 0;
    for (let i = 0; i < polygon.length; i++) {
      const j = (i + 1) % polygon.length;
      area += polygon[i][0] * polygon[j][1];
      area -= polygon[j][0] * polygon[i][1];
    }
    return Math.abs(area / 2) * 111320 * 111320 / 10000; // Convert to hectares
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      <PageContainer className="py-12">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <h1 className="text-5xl font-extrabold text-slate-900 mb-4">
              Submit Your Climate Claim
            </h1>
            <p className="text-xl text-slate-600">
              Follow the steps below to submit your carbon reduction project
            </p>
          </motion.div>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <div className="text-sm font-medium text-slate-600">
                Step {currentStep} of {steps.length}
              </div>
              <div className="text-sm font-medium text-primary-600">
                {Math.round((currentStep / steps.length) * 100)}% Complete
              </div>
            </div>
            <Progress value={(currentStep / steps.length) * 100} className="h-3" />
          </div>

          {/* Step Indicators */}
          <div className="hidden md:flex justify-between mb-8">
            {steps.map((step) => {
              const Icon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = currentStep > step.id;
              
              return (
                <div key={step.id} className="flex flex-col items-center flex-1">
                  <motion.div
                    whileHover={{ scale: 1.1 }}
                    className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all ${
                      isCompleted
                        ? 'bg-primary-600 text-white shadow-lg'
                        : isActive
                        ? 'bg-primary-100 text-primary-600 border-2 border-primary-600'
                        : 'bg-gray-200 text-gray-400'
                    }`}
                  >
                    {isCompleted ? (
                      <CheckCircle className="h-6 w-6" />
                    ) : (
                      <Icon className="h-6 w-6" />
                    )}
                  </motion.div>
                  <div className={`text-xs font-medium text-center ${isActive ? 'text-primary-600' : 'text-gray-500'}`}>
                    {step.title}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Step Content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {renderStepContent()}
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex justify-between mt-8">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentStep === 1 || isSubmitting}
              className="flex items-center"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Previous
            </Button>

            <div className="space-x-2">
              {currentStep < steps.length ? (
                <Button onClick={handleNext} className="flex items-center">
                  Next
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={isSubmitting || uploadingEvidence}
                  className="min-w-[160px] flex items-center justify-center bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 shadow-lg"
                >
                  {isSubmitting || uploadingEvidence ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>{uploadingEvidence ? 'Uploading Evidence...' : 'Submitting...'}</span>
                    </div>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 mr-2" />
                      Submit Claim
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      </PageContainer>
    </div>
  );
};

export default SubmitClaim;
