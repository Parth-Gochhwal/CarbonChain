import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Leaf, Shield, Users, Eye, Menu, X, MessageSquare } from 'lucide-react';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';
import { claimsApi } from '../../services/api';

const Navbar: React.FC = () => {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [hasAuthorityReviewedClaims, setHasAuthorityReviewedClaims] = useState(false);

  // Check if there are any AUTHORITY_REVIEWED claims to show Community tab
  useEffect(() => {
    const checkAuthorityReviewedClaims = async () => {
      try {
        const allClaims = await claimsApi.getClaims();
        const hasAuthorityReviewed = allClaims.some(claim => claim.status === 'authority_reviewed');
        setHasAuthorityReviewedClaims(hasAuthorityReviewed);
      } catch (error) {
        console.error('Error checking claims:', error);
        // Show Community tab even on error (user can navigate directly)
        setHasAuthorityReviewedClaims(true);
      }
    };
    
    checkAuthorityReviewedClaims();
    // Refresh every 30 seconds to update visibility
    const interval = setInterval(checkAuthorityReviewedClaims, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { path: '/', label: 'Home', icon: Leaf },
    { path: '/submit', label: 'Submit Claim', icon: Shield },
    { path: '/authority', label: 'Authority', icon: Users },
    // Community tab - show if there are AUTHORITY_REVIEWED claims OR if user is on community page
    ...(hasAuthorityReviewedClaims || location.pathname === '/community' 
      ? [{ path: '/community', label: 'Community', icon: MessageSquare }] 
      : []),
    { path: '/transparency', label: 'Transparency', icon: Eye },
  ];

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200/50 shadow-sm"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3 group">
            <motion.div
              whileHover={{ rotate: [0, -10, 10, -10, 0] }}
              transition={{ duration: 0.5 }}
              className="p-2.5 bg-gradient-to-br from-primary-600 to-primary-800 rounded-2xl group-hover:shadow-lg transition-all duration-300"
            >
              <Leaf className="h-7 w-7 text-white" />
            </motion.div>
            <div>
              <span className="text-2xl font-bold bg-gradient-to-r from-primary-700 to-secondary-600 bg-clip-text text-transparent">
                CarbonChain
              </span>
              <div className="text-xs text-slate-500 -mt-1 font-medium">Climate Verification</div>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link key={item.path} to={item.path}>
                  <motion.div
                    whileHover={{ y: -2 }}
                    whileTap={{ y: 0 }}
                  >
                    <Button
                      variant={isActive ? "default" : "ghost"}
                      size="sm"
                      className={cn(
                        "relative flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-200",
                        isActive && "bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg"
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      <span className="font-medium">{item.label}</span>
                      {isActive && (
                        <motion.div
                          layoutId="activeTab"
                          className="absolute inset-0 bg-gradient-to-r from-primary-600 to-primary-700 rounded-xl -z-10"
                          transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                        />
                      )}
                    </Button>
                  </motion.div>
                </Link>
              );
            })}
          </div>

          {/* Trust Indicator & CTA */}
          <div className="hidden md:flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-4 py-2 bg-emerald-50 rounded-full border border-emerald-200">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span className="text-xs font-semibold text-emerald-700">Verified Platform</span>
            </div>
            
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button variant="default" size="sm" className="bg-gradient-to-r from-primary-600 to-primary-700 shadow-lg">
                Connect Wallet
              </Button>
            </motion.div>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-slate-100 transition-colors"
          >
            {mobileMenuOpen ? (
              <X className="h-6 w-6 text-slate-700" />
            ) : (
              <Menu className="h-6 w-6 text-slate-700" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Navigation */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-slate-200 bg-white/95 backdrop-blur-xl"
          >
            <div className="px-4 py-4 space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <motion.div
                      whileHover={{ x: 4 }}
                      className={cn(
                        "flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors",
                        isActive
                          ? "bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg"
                          : "text-slate-700 hover:bg-slate-100"
                      )}
                    >
                      <Icon className="h-5 w-5" />
                      <span className="font-medium">{item.label}</span>
                    </motion.div>
                  </Link>
                );
              })}
              <div className="pt-4 border-t border-slate-200">
                <Button variant="default" className="w-full bg-gradient-to-r from-primary-600 to-primary-700">
                  Connect Wallet
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
};

export default Navbar;
