import React from 'react';
import { motion } from 'framer-motion';
import { Brain, CheckCircle, XCircle, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import type { AIConsistencyResult } from '../../types';

interface AIVerdictCardProps {
  verdict: AIConsistencyResult;
  className?: string;
}

const AIVerdictCard: React.FC<AIVerdictCardProps> = ({ verdict, className = '' }) => {
  const getVerdictIcon = () => {
    switch (verdict.verdict) {
      case 'consistent':
        return <CheckCircle className="h-6 w-6 text-green-600" />;
      case 'inconsistent':
        return <XCircle className="h-6 w-6 text-red-600" />;
      default:
        return <AlertTriangle className="h-6 w-6 text-yellow-600" />;
    }
  };

  const getVerdictColor = () => {
    switch (verdict.verdict) {
      case 'consistent':
        return 'success';
      case 'inconsistent':
        return 'destructive';
      default:
        return 'warning';
    }
  };

  const getVerdictLabel = () => {
    switch (verdict.verdict) {
      case 'consistent':
        return 'AI Consistent';
      case 'inconsistent':
        return 'AI Inconsistent';
      default:
        return 'Uncertain';
    }
  };

  const getConfidenceColor = (confidence: string) => {
    if (confidence === 'high') return 'text-green-600';
    if (confidence === 'medium') return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidencePercent = (confidence: string) => {
    switch (confidence) {
      case 'high': return 85;
      case 'medium': return 65;
      case 'low': return 40;
      default: return 50;
    }
  };

  const ndviChange = verdict.ndvi_analysis ? 
    verdict.ndvi_analysis.current_ndvi - verdict.ndvi_analysis.baseline_ndvi : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={className}
    >
      <Card className="border-l-4 border-l-blue-500">
        <CardHeader>
          <CardTitle className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-xl">
              <Brain className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <span>AI Consistency Verdict</span>
              <div className="text-sm font-normal text-gray-500">
                Processed {new Date(verdict.created_at).toLocaleDateString()}
              </div>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Verdict Summary */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center space-x-3">
              {getVerdictIcon()}
              <div>
                <Badge variant={getVerdictColor() as any} className="mb-1">
                  {getVerdictLabel()}
                </Badge>
                <div className="text-sm text-gray-600">
                  Alignment: <span className={`font-semibold ${getConfidenceColor(verdict.alignment_confidence)}`}>
                    {verdict.alignment_confidence}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  Score: <span className="font-semibold text-primary-600">
                    {(verdict.consistency_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Confidence Meter */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">AI Alignment Confidence</span>
              <span className={`text-sm font-semibold ${getConfidenceColor(verdict.alignment_confidence)}`}>
                {verdict.alignment_confidence}
              </span>
            </div>
            <Progress value={getConfidencePercent(verdict.alignment_confidence)} className="h-3" />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Low</span>
              <span>Medium</span>
              <span>High</span>
            </div>
          </div>

          {/* NDVI Analysis */}
          {verdict.ndvi_analysis && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-xl">
                <div className="text-2xl font-bold text-blue-900">
                  {verdict.ndvi_analysis.baseline_ndvi.toFixed(3)}
                </div>
                <div className="text-sm text-blue-700">Baseline NDVI</div>
              </div>
              
              <div className="text-center p-4 bg-green-50 rounded-xl">
                <div className="text-2xl font-bold text-green-900">
                  {verdict.ndvi_analysis.current_ndvi.toFixed(3)}
                </div>
                <div className="text-sm text-green-700">Current NDVI</div>
              </div>
              
              <div className="text-center p-4 bg-gray-50 rounded-xl">
                <div className={`text-2xl font-bold flex items-center justify-center space-x-1 ${
                  ndviChange > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {ndviChange > 0 ? (
                    <TrendingUp className="h-5 w-5" />
                  ) : (
                    <TrendingDown className="h-5 w-5" />
                  )}
                  <span>{ndviChange > 0 ? '+' : ''}{ndviChange.toFixed(3)}</span>
                </div>
                <div className="text-sm text-gray-700">Change</div>
              </div>
            </div>
          )}

          {/* AI Explanation */}
          <div className="p-4 bg-blue-50 rounded-xl">
            <h4 className="font-medium text-blue-900 mb-2 flex items-center">
              <Brain className="h-4 w-4 mr-2" />
              AI Analysis Explanation
            </h4>
            <p className="text-blue-800 text-sm leading-relaxed">
              {verdict.explanation}
            </p>
            <div className="mt-2 text-xs text-blue-700">
              Consistency Score: {(verdict.consistency_score * 100).toFixed(1)}%
            </div>
          </div>

          {/* Methodology Note */}
          <div className="text-xs text-gray-500 p-3 bg-gray-50 rounded-lg">
            <strong>Methodology:</strong> This analysis uses satellite imagery and NDVI (Normalized Difference Vegetation Index) 
            to assess vegetation health and carbon sequestration potential. The AI model considers historical baselines, 
            seasonal variations, and regional climate patterns to provide accurate carbon impact estimates.
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default AIVerdictCard;