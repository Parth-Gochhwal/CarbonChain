# CarbonChain Frontend

A production-grade React frontend for the CarbonChain climate verification platform.

## 🚀 Features

- **Modern Tech Stack**: React 18 + TypeScript + Vite
- **Premium UI**: Tailwind CSS + shadcn/ui components
- **Interactive Maps**: Leaflet integration for location selection
- **Smooth Animations**: Framer Motion for professional transitions
- **Responsive Design**: Mobile-first approach with excellent UX
- **Trust-Focused Design**: Visual trust signals throughout the interface

## 🎨 Design System

### Color Palette
- **Primary**: Deep forest green (#14532d) - represents environmental focus
- **Secondary**: Emerald/mint accents - fresh, natural feel
- **Trust**: Blue-green gradients - builds confidence
- **Background**: Soft off-white/light gray - clean, professional

### Visual Style
- Minimalist design with high whitespace
- Rounded corners (2xl) for modern feel
- Soft shadows for depth
- Card-based layouts for organization
- Subtle, professional animations

## 🧭 Core User Flows

### 1. Submit Claim Flow
Multi-step form with progress indicator:
- Claim details input
- Interactive map location selection
- Evidence upload with preview
- Carbon impact estimation
- Review and submit

### 2. AI Verification View
- NDVI baseline vs monitoring display
- AI confidence meter
- Clear verdict explanation
- Evidence analysis results

### 3. Authority Review Dashboard
- Claims pending review list
- Detailed claim inspection
- Approve/reject with notes
- Real-time status updates

### 4. Community Transparency Portal
- Public claim browser
- Community review system
- Trust indicators
- Full transparency of decisions

### 5. Credit Lifecycle View
- Credit status tracking
- Health monitoring
- Minting/burning history
- ERC-20 simulation labels

## 🛠️ Tech Stack

- **Framework**: React 18 + Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **Maps**: Leaflet + React Leaflet
- **Charts**: Recharts
- **State**: React hooks (no Redux)
- **API**: Centralized axios service

## 📁 Project Structure

```
src/
├── app/
│   ├── App.tsx
│   └── routes.tsx
├── pages/
│   ├── Home.tsx
│   ├── SubmitClaim.tsx
│   ├── ClaimDetail.tsx
│   ├── AuthorityDashboard.tsx
│   ├── CommunityReview.tsx
│   └── Transparency.tsx
├── components/
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   ├── Footer.tsx
│   │   └── PageContainer.tsx
│   ├── claim/
│   │   ├── ClaimForm.tsx
│   │   ├── EvidenceUploader.tsx
│   │   ├── MapSelector.tsx
│   │   └── ClaimTimeline.tsx
│   ├── verification/
│   │   └── AIVerdictCard.tsx
│   └── ui/ (shadcn components)
├── services/
│   └── api.ts
├── types/
│   └── index.ts
└── lib/
    └── utils.ts
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Configure environment variables:
```env
VITE_API_URL=http://localhost:8000
VITE_NODE_ENV=development
VITE_ENABLE_MOCK_DATA=true
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

Create a production build:
```bash
npm run build
```

### Preview

Preview the production build:
```bash
npm run preview
```

## 🎯 UX Principles

### Trust-First Design
Every page answers: "Why should I trust this?"
- Clear verification status indicators
- Transparent decision processes
- Expert authority validation
- Community oversight

### AI Transparency
Every AI decision includes:
- Clear explanation of methodology
- Confidence score with visual meter
- Supporting evidence display
- Human-readable summaries

### No Dead Ends
- Clear next steps on every page
- Helpful error messages
- Guided user flows
- Progressive disclosure

## 🔧 Key Components

### ClaimForm
Multi-step form with validation:
- Progress indicator
- Real-time validation
- File upload with preview
- Map integration

### MapSelector
Interactive location selection:
- Click to select point
- Auto-buffer generation
- Custom polygon drawing
- Area calculation

### AIVerdictCard
AI verification display:
- Verdict badge with confidence
- NDVI analysis visualization
- Explanation text
- Methodology notes

### ClaimTimeline
Status progression:
- Visual timeline
- Status indicators
- Next steps guidance
- Historical tracking

## 🎨 Animation Guidelines

### Subtle & Professional
- Page transitions: fade + slide
- Step transitions in forms
- Hover states on interactive elements
- Progress indicators with smooth animation
- NO flashy or game-like effects

### Performance
- Use CSS transforms for animations
- Leverage Framer Motion's optimization
- Minimize layout thrashing
- Respect user motion preferences

## 📱 Responsive Design

### Breakpoints
- Mobile: 320px - 768px
- Tablet: 768px - 1024px  
- Desktop: 1024px+

### Mobile-First
- Touch-friendly interactions
- Optimized navigation
- Readable typography
- Accessible form controls

## 🔒 Security Considerations

- Input validation on all forms
- XSS prevention in user content
- Secure file upload handling
- API endpoint protection
- Environment variable security

## 🧪 Testing Strategy

### Component Testing
- Unit tests for utilities
- Component integration tests
- Form validation testing
- API service mocking

### E2E Testing
- Critical user flows
- Cross-browser compatibility
- Mobile responsiveness
- Performance benchmarks

## 🚀 Deployment

### Build Optimization
- Code splitting by route
- Asset optimization
- Bundle size monitoring
- Performance budgets

### Environment Configuration
- Production API endpoints
- Feature flag management
- Analytics integration
- Error monitoring

## 📈 Performance

### Optimization Techniques
- Lazy loading of routes
- Image optimization
- Bundle splitting
- Caching strategies

### Monitoring
- Core Web Vitals tracking
- User experience metrics
- Error rate monitoring
- Performance budgets

## 🤝 Contributing

### Code Style
- TypeScript strict mode
- ESLint + Prettier
- Conventional commits
- Component documentation

### Development Workflow
1. Feature branch from main
2. Implement with tests
3. Code review process
4. Merge to main
5. Deploy to staging

## 📄 License

This project is part of the CarbonChain platform for climate verification.