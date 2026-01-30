import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, useScroll, useTransform } from 'framer-motion';
import { 
  Shield, 
  Brain, 
  Users, 
  Eye, 
  ArrowRight, 
  CheckCircle, 
  Leaf,
  Globe,
  TrendingUp,
  Sparkles,
  Zap,
  Lock
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardTitle } from '../components/ui/card';
import PageContainer from '../components/layout/PageContainer';
import { claimsApi } from '../services/api';

const Home: React.FC = () => {
  const { scrollY } = useScroll();
  const opacity = useTransform(scrollY, [0, 300], [1, 0]);
  const scale = useTransform(scrollY, [0, 300], [1, 0.95]);
  const [claimCount, setClaimCount] = useState(0);

  useEffect(() => {
    claimsApi.getClaims().then(claims => setClaimCount(claims.length)).catch(() => {});
  }, []);

  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Verification',
      description: 'Advanced satellite analysis and NDVI monitoring for accurate carbon impact assessment',
      color: 'from-blue-500 to-cyan-500',
      gradient: 'bg-gradient-to-br from-blue-50 to-cyan-50',
      delay: 0.1
    },
    {
      icon: Users,
      title: 'Authority Governance',
      description: 'Expert review by certified environmental authorities for final validation',
      color: 'from-purple-500 to-pink-500',
      gradient: 'bg-gradient-to-br from-purple-50 to-pink-50',
      delay: 0.2
    },
    {
      icon: Eye,
      title: 'Full Transparency',
      description: 'Open community review and public verification of all claims and decisions',
      color: 'from-emerald-500 to-teal-500',
      gradient: 'bg-gradient-to-br from-emerald-50 to-teal-50',
      delay: 0.3
    },
    {
      icon: Lock,
      title: 'Immutable Records',
      description: 'Blockchain-ready evidence system with cryptographic integrity verification',
      color: 'from-indigo-500 to-violet-500',
      gradient: 'bg-gradient-to-br from-indigo-50 to-violet-50',
      delay: 0.4
    }
  ];

  const stats = [
    { label: 'Claims Verified', value: claimCount.toLocaleString(), icon: CheckCircle, color: 'text-blue-600' },
    { label: 'CO₂e Tracked', value: '45.2k', icon: Leaf, color: 'text-emerald-600' },
    { label: 'Global Coverage', value: '23', icon: Globe, color: 'text-purple-600' },
    { label: 'Trust Score', value: '98.5%', icon: TrendingUp, color: 'text-indigo-600' },
  ];

  const processSteps = [
    {
      step: '01',
      title: 'Submit Claim',
      description: 'Upload your climate action project with location and evidence',
      icon: Zap,
    },
    {
      step: '02',
      title: 'AI Analysis',
      description: 'Automated satellite verification using Sentinel-2 and NDVI analysis',
      icon: Brain,
    },
    {
      step: '03',
      title: 'Authority Review',
      description: 'Certified environmental authorities validate your claim',
      icon: Shield,
    },
    {
      step: '04',
      title: 'Community Review',
      description: 'Public transparency check by NGOs and community observers',
      icon: Users,
    },
    {
      step: '05',
      title: 'Mint Credits',
      description: 'Receive verified carbon credits with ongoing monitoring',
      icon: Sparkles,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-500/10 via-transparent to-secondary-500/10" />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAzNGMwIDMuMzE0LTIuNjg2IDYtNiA2cy02LTIuNjg2LTYtNiAyLjY4Ni02IDYtNiA2IDIuNjg2IDYgNnoiIGZpbGw9IiNmMWY1ZjkiIG9wYWNpdHk9Ii4wNSIvPjwvZz48L3N2Zz4=')] opacity-40" />
        
        <PageContainer className="relative pt-24 pb-32">
          <motion.div
            style={{ opacity, scale }}
            className="text-center max-w-5xl mx-auto"
          >
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="mb-8"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100/80 backdrop-blur-sm rounded-full border border-primary-200 mb-6"
              >
                <Sparkles className="h-4 w-4 text-primary-600" />
                <span className="text-sm font-medium text-primary-700">
                  Trusted Carbon Verification Platform
                </span>
              </motion.div>
              
              <h1 className="text-6xl md:text-8xl font-extrabold mb-6 leading-tight">
                <span className="block text-slate-900">Verify Climate</span>
                <span className="block text-transparent bg-clip-text bg-gradient-to-r from-primary-600 via-secondary-500 to-primary-600 whitespace-normal">
                  Impact With Confidence
                </span>
              </h1>
              
              <p className="text-xl md:text-2xl text-slate-600 mb-10 max-w-3xl mx-auto leading-relaxed">
                CarbonChain combines AI-powered satellite analysis with human expertise 
                to create the most trusted carbon credit verification platform.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
                <Link to="/submit">
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Button size="lg" className="group text-lg px-8 py-6 shadow-xl">
                      Submit Your Claim
                      <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </motion.div>
                </Link>
                
                <Link to="/transparency">
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Button variant="outline" size="lg" className="text-lg px-8 py-6 border-2">
                      Explore Transparency Portal
                    </Button>
                  </motion.div>
                </Link>
              </div>
            </motion.div>

            {/* Stats */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.6 }}
              className="grid grid-cols-2 md:grid-cols-4 gap-6"
            >
              {stats.map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.5 + index * 0.1, type: "spring" }}
                    whileHover={{ scale: 1.05, y: -5 }}
                    className="relative"
                  >
                    <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-white/80 backdrop-blur-sm">
                      <CardContent className="p-6 text-center">
                        <div className={`inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4 ${stat.color.replace('text-', 'bg-')} bg-opacity-10`}>
                          <Icon className={`h-7 w-7 ${stat.color}`} />
                        </div>
                        <div className="text-3xl font-bold text-slate-900 mb-1 break-words">{stat.value}</div>
                        <div className="text-sm font-medium text-slate-600 break-words">{stat.label}</div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </motion.div>
          </motion.div>
        </PageContainer>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <PageContainer>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-5xl font-bold text-slate-900 mb-4">
              Why CarbonChain?
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              A comprehensive verification platform that ensures accuracy, transparency, and trust
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: feature.delay }}
                  whileHover={{ y: -8 }}
                >
                  <Card className="h-full border-0 shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden group">
                    <div className={`${feature.gradient} p-8`}>
                      <div className={`inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r ${feature.color} rounded-3xl mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                        <Icon className="h-10 w-10 text-white" />
                      </div>
                      <CardTitle className="text-2xl mb-3 text-slate-900">{feature.title}</CardTitle>
                      <CardDescription className="text-slate-600 leading-relaxed text-base">
                        {feature.description}
                      </CardDescription>
                    </div>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </PageContainer>
      </section>

      {/* Process Section */}
      <section className="py-24 bg-gradient-to-br from-slate-50 to-slate-100">
        <PageContainer>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-5xl font-bold text-slate-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              A streamlined five-step process from submission to credit minting
            </p>
          </motion.div>

          <div className="relative">
            {/* Connection Line */}
            <div className="hidden lg:block absolute top-24 left-0 right-0 h-1 bg-gradient-to-r from-primary-200 via-secondary-200 to-primary-200" />
            
            <div className="grid grid-cols-1 md:grid-cols-5 gap-8 relative">
              {processSteps.map((step, idx) => {
                const Icon = step.icon;
                return (
                  <motion.div
                    key={step.step}
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: idx * 0.1 }}
                    className="relative"
                  >
                    <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-white text-center group">
                      <CardContent className="p-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-secondary-500 text-white text-2xl font-bold mb-4 group-hover:scale-110 transition-transform">
                          {step.step}
                        </div>
                        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary-100 text-primary-600 mb-4 group-hover:bg-primary-200 transition-colors">
                          <Icon className="h-6 w-6" />
                        </div>
                        <CardTitle className="text-xl mb-2 text-slate-900">{step.title}</CardTitle>
                        <CardDescription className="text-slate-600 text-sm leading-relaxed">
                          {step.description}
                        </CardDescription>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </PageContainer>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-primary-900 via-primary-800 to-secondary-800 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAzNGMwIDMuMzE0LTIuNjg2IDYtNiA2cy02LTIuNjg2LTYtNiAyLjY4Ni02IDYtNiA2IDIuNjg2IDYgNnoiIGZpbGw9IndoaXRlIiBvcGFjaXR5PSIuMDUiLz48L2c+PC9zdmc+')] opacity-20" />
        
        <PageContainer className="relative">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center max-w-4xl mx-auto"
          >
            <h2 className="text-5xl font-bold mb-6">
              Ready to Verify Your Climate Impact?
            </h2>
            <p className="text-xl text-primary-100 mb-10 leading-relaxed">
              Join the transparent future of carbon credit verification. 
              Submit your claim today and be part of the solution.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/submit">
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button variant="secondary" size="lg" className="text-lg px-8 py-6 shadow-xl">
                    Get Started Now
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </motion.div>
              </Link>
              
              <Link to="/authority">
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button variant="outline" size="lg" className="text-lg px-8 py-6 border-2 border-white text-white hover:bg-white hover:text-primary-900">
                    Authority Dashboard
                  </Button>
                </motion.div>
              </Link>
            </div>
          </motion.div>
        </PageContainer>
      </section>
    </div>
  );
};

export default Home;
