import React from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Brain, 
  Users, 
  Eye, 
  CheckCircle, 
  Coins,
  Clock
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import type { Claim } from '../../types';
import { formatDate, getStatusColor, getStatusLabel } from '../../lib/utils';

interface ClaimTimelineProps {
  claim: Claim;
  className?: string;
}

const ClaimTimeline: React.FC<ClaimTimelineProps> = ({ claim, className = '' }) => {
  const timelineEvents = [
    {
      id: 'submitted',
      title: 'Claim Submitted',
      description: `Submitted by ${claim.submitter_name}`,
      timestamp: claim.created_at,
      icon: FileText,
      status: 'completed',
      color: 'blue'
    },
    {
      id: 'ai_analyzed',
      title: 'AI Analysis',
      description: claim.status === 'ai_analyzed' || claim.status === 'ai_verified' || claim.status === 'verified'
        ? 'AI analysis completed'
        : 'Processing satellite data and NDVI analysis',
      timestamp: claim.updated_at,
      icon: Brain,
      status: ['ai_analyzed', 'ai_verified', 'verified', 'authority_reviewed', 'community_reviewed', 'approved', 'minted'].includes(claim.status)
        ? 'completed' 
        : claim.status === 'submitted' 
        ? 'active' 
        : 'pending',
      color: 'purple'
    },
    {
      id: 'authority_review',
      title: 'Authority Review',
      description: 'Awaiting expert authority validation',
      timestamp: null,
      icon: Users,
      status: ['authority_reviewed', 'community_reviewed', 'approved', 'minted'].includes(claim.status)
        ? 'completed' 
        : ['ai_analyzed', 'ai_verified', 'verified'].includes(claim.status)
        ? 'active' 
        : 'pending',
      color: 'green'
    },
    {
      id: 'community_review',
      title: 'Community Transparency',
      description: 'Open for public review and feedback',
      timestamp: null,
      icon: Eye,
      status: ['community_reviewed', 'approved', 'minted'].includes(claim.status)
        ? 'completed' 
        : claim.status === 'authority_reviewed'
        ? 'active' 
        : 'pending',
      color: 'indigo'
    }
  ];

  // Add minting event if credits are minted
  if (claim.status === 'minted') {
    timelineEvents.push({
      id: 'minted',
      title: 'Credits Minted',
      description: 'Carbon credits issued',
      timestamp: claim.updated_at,
      icon: Coins,
      status: 'completed',
      color: 'emerald'
    });
  }

  const getEventIcon = (event: typeof timelineEvents[0]) => {
    const Icon = event.icon;
    
    switch (event.status) {
      case 'completed':
        return (
          <div className={`p-2 bg-${event.color}-100 rounded-full`}>
            <CheckCircle className={`h-5 w-5 text-${event.color}-600`} />
          </div>
        );
      case 'active':
        return (
          <div className={`p-2 bg-${event.color}-100 rounded-full animate-pulse`}>
            <Icon className={`h-5 w-5 text-${event.color}-600`} />
          </div>
        );
      default:
        return (
          <div className="p-2 bg-gray-100 rounded-full">
            <Icon className="h-5 w-5 text-gray-400" />
          </div>
        );
    }
  };

  const getConnectorColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'active':
        return 'bg-blue-500';
      default:
        return 'bg-gray-300';
    }
  };

  const getNextStep = () => {
    if (claim.status === 'submitted') {
      return 'Your claim is being processed by our AI verification system.';
    }
    if (['ai_analyzed', 'ai_verified', 'verified'].includes(claim.status)) {
      return 'AI analysis complete. Awaiting authority review.';
    }
    if (claim.status === 'authority_reviewed') {
      return 'Approved by authorities. Open for community review.';
    }
    if (claim.status === 'community_reviewed') {
      return 'Community review complete. Ready for credit minting.';
    }
    if (claim.status === 'approved') {
      return 'Claim fully approved. Carbon credits will be minted.';
    }
    if (claim.status === 'minted') {
      return 'Carbon credits have been successfully minted and are active.';
    }
    if (claim.status === 'rejected') {
      return 'Claim has been rejected. Please review feedback and resubmit if needed.';
    }
    return 'Processing...';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={className}
    >
      <Card className="border-0 shadow-xl">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="text-xl">Claim Timeline</span>
            <Badge className={getStatusColor(claim.status)}>
              {getStatusLabel(claim.status)}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            {timelineEvents.map((event, index) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative flex items-start space-x-4 pb-8 last:pb-0"
              >
                {/* Connector Line */}
                {index < timelineEvents.length - 1 && (
                  <div 
                    className={`absolute left-6 top-12 w-0.5 h-16 ${getConnectorColor(event.status)}`}
                  />
                )}
                
                {/* Event Icon */}
                <div className="relative z-10">
                  {getEventIcon(event)}
                </div>
                
                {/* Event Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-semibold text-slate-900">
                      {event.title}
                    </h4>
                    {event.timestamp && (
                      <span className="text-xs text-slate-500">
                        {formatDate(event.timestamp)}
                      </span>
                    )}
                  </div>
                  
                  <p className="text-sm text-slate-600 mb-2">
                    {event.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
          
          {/* Next Steps */}
          <div className="mt-6 p-5 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl border border-blue-200">
            <div className="flex items-center space-x-2 mb-2">
              <Clock className="h-5 w-5 text-blue-600" />
              <h4 className="font-semibold text-blue-900">Next Steps</h4>
            </div>
            <p className="text-sm text-blue-800 leading-relaxed">
              {getNextStep()}
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default ClaimTimeline;
