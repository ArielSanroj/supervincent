# SuperVincent Finance Dashboard - Frontend

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 📁 Project Structure

```
src/
├── components/
│   ├── FinanceDashboard.tsx    # Main dashboard component
│   ├── IndicatorCard.tsx        # Individual metric cards
│   ├── BudgetList.tsx          # Budget breakdown list
│   ├── BreakEvenSlider.tsx     # Break-even point slider
│   └── LoadingSpinner.tsx      # Loading states
├── services/
│   ├── api.ts                  # API client configuration
│   └── financeService.ts       # Finance data service
├── types/
│   └── finance.ts              # TypeScript interfaces
├── styles/
│   ├── globals.css             # Global styles
│   └── components.css          # Component-specific styles
└── pages/
    ├── index.tsx               # Main dashboard page
    └── api/
        └── finance.ts          # API route handler
```

## 🎯 Features

- **📊 Financial Indicators**: Debt ratio, liquidity, sales, profit, inventory turnover, available cash
- **💰 Budget Breakdown**: Visual list of budget categories with amounts
- **⚖️ Break-even Analysis**: Interactive slider showing profit/loss threshold
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **🔄 Real-time Data**: Fetches live data from SuperVincent API
- **🎨 Modern UI**: Clean, professional design with dark mode support

## 🔧 Configuration

Update `src/services/api.ts` with your SuperVincent API endpoint:

```typescript
const API_BASE_URL = 'http://localhost:8000'; // Your SuperVincent API URL
```

## 📱 Usage

1. **Start the development server**: `npm run dev`
2. **Open browser**: Navigate to `http://localhost:3000`
3. **View dashboard**: See real-time financial metrics
4. **Interact**: Click "Extractos" button for detailed reports

## 🎨 Customization

- **Colors**: Modify `styles/globals.css` for brand colors
- **Layout**: Adjust grid columns in `FinanceDashboard.tsx`
- **Metrics**: Add/remove indicators in the dashboard
- **Styling**: Use Tailwind CSS classes for quick styling

## 🔗 Integration

This frontend integrates with your SuperVincent InvoiceBot API running on port 8000. Make sure your backend is running before starting the frontend.
