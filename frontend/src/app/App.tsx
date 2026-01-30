import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';
import AppRoutes from './routes';
import './App.css';

const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-white to-slate-50 w-full">
        <Navbar />
        
        <main className="flex-1 w-full">
          <AnimatePresence mode="wait">
            <AppRoutes />
          </AnimatePresence>
        </main>
        
        <Footer />
      </div>
    </Router>
  );
};

export default App;