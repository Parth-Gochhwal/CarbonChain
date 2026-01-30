import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from '../pages/Home';
import SubmitClaim from '../pages/SubmitClaim';
import ClaimDetail from '../pages/ClaimDetail';
import AuthorityDashboard from '../pages/AuthorityDashboard';
import CommunityReview from '../pages/CommunityReview';
import Transparency from '../pages/Transparency';

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/submit" element={<SubmitClaim />} />
      <Route path="/claim/:id" element={<ClaimDetail />} />
      <Route path="/authority" element={<AuthorityDashboard />} />
      <Route path="/community" element={<CommunityReview />} />
      <Route path="/transparency" element={<Transparency />} />
    </Routes>
  );
};

export default AppRoutes;