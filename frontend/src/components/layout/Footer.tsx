import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Leaf, Github, Twitter, Globe, Shield, Mail } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white relative overflow-hidden">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAzNGMwIDMuMzE0LTIuNjg2IDYtNiA2cy02LTIuNjg2LTYtNiAyLjY4Ni02IDYtNiA2IDIuNjg2IDYgNnoiIGZpbGw9IndoaXRlIiBvcGFjaXR5PSIuMDMiLz48L2c+PC9zdmc+')] opacity-30" />
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="flex items-center space-x-3 mb-6"
            >
              <div className="p-3 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl shadow-lg">
                <Leaf className="h-7 w-7 text-white" />
              </div>
              <div>
                <span className="text-2xl font-bold bg-gradient-to-r from-white to-slate-200 bg-clip-text text-transparent">
                  CarbonChain
                </span>
                <div className="text-sm text-slate-400 -mt-1 font-medium">Climate Verification Platform</div>
              </div>
            </motion.div>
            <p className="text-slate-300 mb-6 max-w-md leading-relaxed">
              Transparent, AI-powered carbon credit verification with community governance. 
              Building trust in climate action through technology and transparency.
            </p>
            <div className="flex space-x-3">
              {[
                { icon: Github, href: '#', label: 'GitHub' },
                { icon: Twitter, href: '#', label: 'Twitter' },
                { icon: Globe, href: '#', label: 'Website' },
                { icon: Mail, href: '#', label: 'Email' },
              ].map((social) => {
                const Icon = social.icon;
                return (
                  <motion.a
                    key={social.label}
                    href={social.href}
                    whileHover={{ scale: 1.1, y: -2 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-3 bg-white/10 backdrop-blur-sm rounded-xl hover:bg-white/20 transition-all duration-300 border border-white/10"
                    aria-label={social.label}
                  >
                    <Icon className="h-5 w-5" />
                  </motion.a>
                );
              })}
            </div>
          </div>

          {/* Platform */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
          >
            <h3 className="font-bold text-lg mb-6 text-white">Platform</h3>
            <ul className="space-y-3 text-slate-300">
              <li>
                <Link to="/submit" className="hover:text-white transition-colors flex items-center group">
                  <span className="group-hover:translate-x-1 transition-transform">Submit Claims</span>
                </Link>
              </li>
              <li>
                <Link to="/transparency" className="hover:text-white transition-colors flex items-center group">
                  <span className="group-hover:translate-x-1 transition-transform">Transparency Portal</span>
                </Link>
              </li>
              <li>
                <Link to="/authority" className="hover:text-white transition-colors flex items-center group">
                  <span className="group-hover:translate-x-1 transition-transform">Authority Review</span>
                </Link>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors flex items-center group">
                  <span className="group-hover:translate-x-1 transition-transform">Community Portal</span>
                </a>
              </li>
            </ul>
          </motion.div>

          {/* Resources */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
          >
            <h3 className="font-bold text-lg mb-6 text-white">Resources</h3>
            <ul className="space-y-3 text-slate-300">
              <li>
                <a href="#" className="hover:text-white transition-colors flex items-center group">
                  <span className="group-hover:translate-x-1 transition-transform">Documentation</span>
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors flex items-center group">
                  <span className="group-hover:translate-x-1 transition-transform">API Reference</span>
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors flex items-center group">
                  <span className="group-hover:translate-x-1 transition-transform">Methodology</span>
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors flex items-center group">
                  <span className="group-hover:translate-x-1 transition-transform">Support</span>
                </a>
              </li>
            </ul>
          </motion.div>
        </div>

        <div className="border-t border-slate-700/50 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
          <div className="text-slate-400 text-sm mb-4 md:mb-0">
            © 2024 CarbonChain. All rights reserved.
          </div>
          
          <div className="flex flex-wrap items-center gap-6 text-sm text-slate-400">
            <div className="flex items-center space-x-2">
              <Shield className="h-4 w-4 text-primary-400" />
              <span>Simulated ERC-20 Credits</span>
            </div>
            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
