import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Eye, 
  Search, 
  Filter, 
  MapPin, 
  Calendar, 
  User, 
  Leaf,
  TrendingUp,
  Globe,
  Shield,
  BarChart3
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import PageContainer from '../components/layout/PageContainer';
import { claimsApi } from '../services/api';
import type { Claim } from '../types';
import { formatDate, formatCO2e, getStatusColor, getStatusLabel } from '../lib/utils';

const Transparency: React.FC = () => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [filteredClaims, setFilteredClaims] = useState<Claim[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClaims();
  }, []);

  useEffect(() => {
    filterClaims();
  }, [claims, searchTerm, statusFilter]);

  const fetchClaims = async () => {
    try {
      setLoading(true);
      const allClaims = await claimsApi.getClaims();
      setClaims(allClaims);
    } catch (error) {
      console.error('Error fetching claims:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterClaims = () => {
    let filtered = claims;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(claim =>
        claim.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        claim.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        claim.submitter_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(claim => claim.status === statusFilter);
    }

    setFilteredClaims(filtered);
  };

  const stats = [
    {
      label: 'Total Claims',
      value: claims.length,
      icon: Leaf,
      color: 'text-emerald-600 bg-emerald-100',
      gradient: 'from-emerald-500 to-green-500'
    },
    {
      label: 'Verified CO₂e',
      value: `${claims.reduce((sum, claim) => sum + claim.carbon_impact_estimate.max_tonnes_co2e, 0).toFixed(1)}t`,
      icon: TrendingUp,
      color: 'text-blue-600 bg-blue-100',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      label: 'Global Projects',
      value: new Set(claims.filter(c => c.location).map(c => `${Math.floor(c.location!.latitude)},${Math.floor(c.location!.longitude)}`)).size,
      icon: Globe,
      color: 'text-purple-600 bg-purple-100',
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      label: 'Trust Score',
      value: '98.5%',
      icon: Shield,
      color: 'text-primary-600 bg-primary-100',
      gradient: 'from-primary-500 to-primary-700'
    }
  ];

  const statusOptions = [
    { value: 'all', label: 'All Claims' },
    { value: 'submitted', label: 'Submitted' },
    { value: 'ai_analyzed', label: 'AI Analyzed' },
    { value: 'authority_reviewed', label: 'Authority Reviewed' },
    { value: 'community_reviewed', label: 'Community Reviewed' },
    { value: 'approved', label: 'Approved' },
    { value: 'minted', label: 'Credits Minted' },
    { value: 'rejected', label: 'Rejected' }
  ];

  const getStatusCounts = () => {
    const counts: Record<string, number> = {};
    claims.forEach(claim => {
      counts[claim.status] = (counts[claim.status] || 0) + 1;
    });
    return counts;
  };

  const statusCounts = getStatusCounts();

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
                Transparency Portal
              </h1>
              <p className="text-xl text-slate-600 mb-8 max-w-3xl mx-auto leading-relaxed">
                Explore all carbon credit claims with complete transparency. 
                Every decision, every verification, and every impact is open for public review.
              </p>
              
              <div className="inline-flex items-center justify-center space-x-3 px-6 py-3 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-2xl border-2 border-blue-200 shadow-lg">
                <Eye className="h-6 w-6 text-blue-600" />
                <span className="text-blue-700 font-semibold text-lg">Fully Transparent Platform</span>
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

          {/* Status Distribution */}
          <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-50 to-slate-100">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center">
                <BarChart3 className="h-6 w-6 mr-2" />
                Status Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
                {statusOptions.filter(opt => opt.value !== 'all').map((option) => {
                  const count = statusCounts[option.value] || 0;
                  const percentage = claims.length > 0 ? (count / claims.length) * 100 : 0;
                  
                  return (
                    <motion.div
                      key={option.value}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="text-center p-4 bg-white rounded-xl border-2 border-slate-200 hover:border-primary-300 transition-all"
                    >
                      <div className="text-2xl font-bold text-slate-900 mb-1">{count}</div>
                      <div className="text-xs font-medium text-slate-600 mb-2">{option.label}</div>
                      <div className="w-full bg-slate-200 rounded-full h-2">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${percentage}%` }}
                          transition={{ duration: 0.8, delay: 0.2 }}
                          className="bg-primary-600 h-2 rounded-full"
                        />
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Filters */}
          <Card className="border-0 shadow-xl">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center">
                <Filter className="h-6 w-6 mr-2 text-slate-600" />
                Explore Claims
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
                    <Input
                      placeholder="Search claims by title, description, or submitter..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-12 h-12 text-base"
                    />
                  </div>
                </div>
                
                <div className="md:w-64">
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-full h-12 px-4 py-2 border-2 border-slate-200 rounded-xl bg-white text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"
                  >
                    {statusOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="mt-4 text-sm font-medium text-slate-600">
                Showing <span className="font-bold text-slate-900">{filteredClaims.length}</span> of <span className="font-bold text-slate-900">{claims.length}</span> claims
              </div>
            </CardContent>
          </Card>

          {/* Claims Grid */}
          {loading ? (
            <div className="text-center py-16">
              <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-slate-600 text-lg">Loading transparency data...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredClaims.map((claim, index) => (
                <motion.div
                  key={claim.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  whileHover={{ y: -4 }}
                >
                  <Link to={`/claim/${claim.id}`}>
                    <Card className="h-full border-0 shadow-xl hover:shadow-2xl transition-all duration-300 cursor-pointer group bg-white">
                      <CardHeader>
                        <div className="flex items-start justify-between mb-3">
                          <CardTitle className="text-xl group-hover:text-primary-700 transition-colors line-clamp-2">
                            {claim.title}
                          </CardTitle>
                          <Badge className={`${getStatusColor(claim.status)} ml-2 flex-shrink-0`}>
                            {getStatusLabel(claim.status)}
                          </Badge>
                        </div>
                        
                        <div className="flex items-center space-x-4 text-sm text-slate-600">
                          <div className="flex items-center space-x-1">
                            <User className="h-4 w-4" />
                            <span className="truncate">{claim.submitter_name}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-4 w-4" />
                            <span>{formatDate(claim.created_at)}</span>
                          </div>
                        </div>
                      </CardHeader>
                      
                      <CardContent>
                        <p className="text-slate-600 text-sm mb-6 line-clamp-3 leading-relaxed">
                          {claim.description}
                        </p>
                        
                        <div className="space-y-3 mb-6">
                          {/* Carbon Impact */}
                          <div className="flex items-center justify-between p-3 bg-gradient-to-r from-primary-50 to-primary-100 rounded-xl">
                            <span className="text-sm font-semibold text-slate-700">Carbon Impact:</span>
                            <span className="font-bold text-primary-900">
                              {formatCO2e(claim.carbon_impact_estimate.min_tonnes_co2e)} - {formatCO2e(claim.carbon_impact_estimate.max_tonnes_co2e)}
                            </span>
                          </div>
                          
                          {/* Location */}
                          {claim.location && (
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-slate-600">Location:</span>
                              <div className="flex items-center space-x-1 text-slate-700 font-medium">
                                <MapPin className="h-4 w-4 text-slate-400" />
                                <span>{claim.location.latitude.toFixed(2)}, {claim.location.longitude.toFixed(2)}</span>
                              </div>
                            </div>
                          )}
                          
                          {/* Project Type */}
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-slate-600">Type:</span>
                            <span className="text-slate-900 font-medium capitalize">
                              {claim.claim_type.replace('_', ' ')}
                            </span>
                          </div>
                        </div>
                        
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="w-full group-hover:bg-primary-50 group-hover:border-primary-300 group-hover:text-primary-700 transition-all"
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Full Details
                        </Button>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}

          {filteredClaims.length === 0 && !loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-16"
            >
              <Search className="h-16 w-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-2xl font-bold text-slate-900 mb-2">No claims found</h3>
              <p className="text-slate-600">Try adjusting your search or filter criteria</p>
            </motion.div>
          )}

          {/* Trust Message */}
          <Card className="border-0 shadow-xl bg-gradient-to-r from-blue-50 via-cyan-50 to-blue-50">
            <CardContent className="p-12 text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", delay: 0.3 }}
                className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-3xl mb-6 shadow-lg"
              >
                <Shield className="h-10 w-10 text-white" />
              </motion.div>
              <h3 className="text-3xl font-bold text-slate-900 mb-4">
                Complete Transparency, Complete Trust
              </h3>
              <p className="text-slate-700 max-w-3xl mx-auto leading-relaxed text-lg">
                Every claim on CarbonChain is fully transparent and verifiable. 
                From AI analysis to authority reviews and community feedback, 
                all data is open for public scrutiny to ensure the highest standards of trust and integrity.
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </PageContainer>
    </div>
  );
};

export default Transparency;
