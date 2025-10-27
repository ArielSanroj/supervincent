// Finance Dashboard Types
export interface FinanceDashboard {
  indicators: FinancialIndicators;
  budget: BudgetItem[];
  breakEven: BreakEvenPoint;
}

export interface FinancialIndicators {
  debtRatio: number | null;
  liquidity: number | null;
  lastMonthSales: number | null;
  lastMonthProfit: number | null;
  inventoryTurnoverDays: number | null;
  availableCash: number | null;
}

export interface BudgetItem {
  label: string;
  amount: number | null;
}

export interface BreakEvenPoint {
  percent: number; // 0-100
  tooltipLoss: string;
  tooltipProfit: string;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Component Props Types
export interface IndicatorCardProps {
  title: string;
  value: string | number | null;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  format?: 'currency' | 'percentage' | 'number' | 'days';
}

export interface BudgetListProps {
  items: BudgetItem[];
  total?: number;
}

export interface BreakEvenSliderProps {
  percent: number;
  tooltipLoss: string;
  tooltipProfit: string;
  disabled?: boolean;
}

// Loading States
export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

// Chart Data Types
export interface ChartDataPoint {
  name: string;
  value: number;
  color?: string;
}

// Bookkeeping and Accounting Types
export interface GeneralLedgerEntry {
  id: string;
  date: string;
  account_code: string;
  account_name: string;
  description: string;
  debit: number;
  credit: number;
  balance: number;
}

export interface TrialBalanceAccount {
  account_code: string;
  account_name: string;
  debit_balance: number;
  credit_balance: number;
  total_debit: number;
  total_credit: number;
}

export interface JournalEntry {
  id: string;
  date: string;
  reference: string;
  description: string;
  total_amount: number;
  entries: GeneralLedgerEntry[];
}

export interface AgingBucket {
  current: number;      // 0-30 days
  days_31_60: number;   // 31-60 days
  days_61_90: number;   // 61-90 days
  over_90: number;      // Over 90 days
}

export interface AgingReport {
  receivables: {
    total: number;
    aging: AgingBucket;
  };
  payables: {
    total: number;
    aging: AgingBucket;
  };
  net_position: number;
}

export interface CashFlowReport {
  total_income: number;
  total_expenses: number;
  net_cash_flow: number;
  income_count: number;
  expense_count: number;
}

// Tax Calculation Types
export interface TaxCalculation {
  iva_amount: number;
  iva_rate: number;
  retefuente_renta: number;
  retefuente_iva: number;
  retefuente_ica: number;
  total_withholdings: number;
  net_amount: number;
  compliance_status: string;
  tax_breakdown: TaxBreakdown;
}

export interface TaxBreakdown {
  iva: {
    amount: number;
    rate: number;
    category: string;
  };
  retefuente: {
    renta: { amount: number; rate: number };
    iva: { amount: number; rate: number };
    ica: { amount: number; rate: number };
  };
  totals: {
    base_amount: number;
    iva_amount: number;
    total_amount: number;
    total_withholdings: number;
    net_amount: number;
  };
}

export interface ColombianTaxRules {
  version: string;
  uvt_2025: number;
  currency: string;
  country: string;
  iva_rates: {
    general: number;
    reducida: number;
    exento: number;
  };
  iva_categories: Record<string, {
    rate: number;
    description: string;
    dian_code: string;
  }>;
  retefuente_renta: {
    thresholds: Record<string, {
      uvt_min: number;
      uvt_max?: number;
      rate: number;
      rate_low?: number;
      rate_high?: number;
      description: string;
    }>;
  };
  retefuente_iva: {
    threshold_uvt: number;
    rates: {
      comun: number;
      gran_contribuyente: number;
    };
  };
  retefuente_ica: {
    cities: Record<string, {
      threshold_uvt: number;
      rates: {
        comercio: number;
        industria: number;
        servicios: number;
      };
    }>;
  };
}

export interface TaxCompliance {
  invoice_id: string;
  compliance_status: string;
  validation_results: {
    iva_calculation: string;
    retefuente_calculation: string;
    ica_calculation: string;
    cufe_validation: string;
  };
}

// Extended Finance Dashboard Data
export interface ExtendedFinanceDashboard extends FinanceDashboard {
  // Bookkeeping data
  generalLedger?: GeneralLedgerEntry[];
  trialBalance?: TrialBalanceAccount[];
  journalEntries?: JournalEntry[];
  agingReport?: AgingReport;
  cashFlowReport?: CashFlowReport;
  // Tax data
  taxCalculation?: TaxCalculation;
  taxRules?: ColombianTaxRules;
  taxCompliance?: TaxCompliance;
}
