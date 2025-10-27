import React, { useState, useEffect } from 'react';
import { FinanceDashboard, FinancialIndicators } from '../types/finance';
import { financeService } from '../services/financeService';
import IndicatorCard from './IndicatorCard';
import BudgetList from './BudgetList';
import BreakEvenSlider from './BreakEvenSlider';
import LoadingSpinner, { SkeletonCard, ErrorMessage } from './LoadingSpinner';
import GeneralLedgerTable from './GeneralLedgerTable';
import TrialBalanceTable from './TrialBalanceTable';
import TaxCalculationDisplay from './TaxCalculationDisplay';
import AgingReportDisplay from './AgingReportDisplay';
import { 
  DollarSign, 
  TrendingUp, 
  Package, 
  Wallet, 
  BarChart3, 
  PiggyBank,
  FileText,
  RefreshCw,
  BookOpen,
  Calculator,
  Receipt
} from 'lucide-react';

const FinanceDashboard: React.FC = () => {
  const [dashboard, setDashboard] = useState<FinanceDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'bookkeeping' | 'taxes'>('overview');
  
  // Bookkeeping data state
  const [generalLedger, setGeneralLedger] = useState<any[]>([]);
  const [trialBalance, setTrialBalance] = useState<any[]>([]);
  const [agingReport, setAgingReport] = useState<any>(null);
  const [bookkeepingLoading, setBookkeepingLoading] = useState(false);
  
  // Tax data state
  const [taxCalculation, setTaxCalculation] = useState<any>(null);
  const [taxRules, setTaxRules] = useState<any>(null);
  const [taxLoading, setTaxLoading] = useState(false);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await financeService.getDashboard('demo-user');
      setDashboard(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  const loadBookkeepingData = async () => {
    try {
      setBookkeepingLoading(true);
      
      // Load general ledger
      const ledgerResponse = await fetch('/api/reports/general-ledger?start_date=2025-01-01&end_date=2025-12-31');
      if (ledgerResponse.ok) {
        const ledgerData = await ledgerResponse.json();
        setGeneralLedger(ledgerData.data || []);
      }
      
      // Load trial balance
      const trialResponse = await fetch('/api/reports/trial-balance?start_date=2025-01-01&end_date=2025-12-31');
      if (trialResponse.ok) {
        const trialData = await trialResponse.json();
        setTrialBalance(trialData.data || []);
      }
      
      // Load aging report
      const agingResponse = await fetch('/api/reports/aging?start_date=2025-01-01&end_date=2025-12-31');
      if (agingResponse.ok) {
        const agingData = await agingResponse.json();
        setAgingReport(agingData.data || null);
      }
    } catch (err) {
      console.error('Error loading bookkeeping data:', err);
    } finally {
      setBookkeepingLoading(false);
    }
  };

  const loadTaxData = async () => {
    try {
      setTaxLoading(true);
      
      // Load tax rules
      const rulesResponse = await fetch('/api/tax/rules');
      if (rulesResponse.ok) {
        const rulesData = await rulesResponse.json();
        setTaxRules(rulesData.tax_rules || null);
      }
      
      // Load sample tax calculation
      const calcResponse = await fetch('/api/tax/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          invoice_type: 'purchase',
          date: '2025-01-15',
          vendor: 'Proveedor Ejemplo',
          client: 'Cliente Ejemplo',
          items: [
            {
              description: 'Producto de ejemplo',
              quantity: 1,
              price: 100000
            }
          ],
          subtotal: 100000,
          taxes: 19000,
          total: 119000,
          vendor_nit: '123456789',
          vendor_regime: 'comun',
          vendor_city: 'bogota',
          buyer_nit: '987654321',
          buyer_regime: 'comun',
          buyer_city: 'bogota',
          invoice_number: 'FAC-001'
        })
      });
      if (calcResponse.ok) {
        const calcData = await calcResponse.json();
        setTaxCalculation(calcData.tax_calculation || null);
      }
    } catch (err) {
      console.error('Error loading tax data:', err);
    } finally {
      setTaxLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (activeTab === 'bookkeeping') {
      loadBookkeepingData();
    }
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === 'taxes') {
      loadTaxData();
    }
  }, [activeTab]);

  const renderIndicators = (indicators: FinancialIndicators) => {
    const indicatorCards = [
      {
        title: 'Endeudamiento',
        value: indicators.debtRatio,
        icon: <BarChart3 className="w-5 h-5" />,
        format: 'percentage' as const,
        trend: 'neutral' as const
      },
      {
        title: 'Liquidez',
        value: indicators.liquidity,
        icon: <TrendingUp className="w-5 h-5" />,
        format: 'number' as const,
        trend: 'up' as const
      },
      {
        title: 'Ventas mes pasado',
        value: indicators.lastMonthSales,
        icon: <DollarSign className="w-5 h-5" />,
        format: 'currency' as const,
        trend: 'up' as const
      },
      {
        title: 'Utilidad mes pasado',
        value: indicators.lastMonthProfit,
        icon: <PiggyBank className="w-5 h-5" />,
        format: 'currency' as const,
        trend: 'up' as const
      },
      {
        title: 'Rotación inventario',
        value: indicators.inventoryTurnoverDays,
        icon: <Package className="w-5 h-5" />,
        format: 'days' as const,
        trend: 'down' as const
      },
      {
        title: 'Caja disponible',
        value: indicators.availableCash,
        icon: <Wallet className="w-5 h-5" />,
        format: 'currency' as const,
        trend: 'neutral' as const
      }
    ];

    return indicatorCards.map((card, index) => (
      <IndicatorCard key={index} {...card} />
    ));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="container mx-auto px-4 py-8">
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div className="animate-pulse">
                <div className="h-8 bg-gray-200 dark:bg-gray-600 rounded w-64 mb-2"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-96"></div>
              </div>
              <div className="animate-pulse">
                <div className="h-10 bg-gray-200 dark:bg-gray-600 rounded w-24"></div>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {Array.from({ length: 6 }).map((_, index) => (
              <SkeletonCard key={index} />
            ))}
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="max-w-md w-full">
          <ErrorMessage message={error} onRetry={loadDashboard} />
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-2">
                SuperVincent • Financiero
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Dashboard financiero en tiempo real
              </p>
            </div>
            <button
              onClick={loadDashboard}
              className="flex items-center space-x-2 bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Actualizar</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <TrendingUp className="w-4 h-4 inline mr-2" />
              Resumen General
            </button>
            <button
              onClick={() => setActiveTab('bookkeeping')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'bookkeeping'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <BookOpen className="w-4 h-4 inline mr-2" />
              Contabilidad
            </button>
            <button
              onClick={() => setActiveTab('taxes')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'taxes'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Calculator className="w-4 h-4 inline mr-2" />
              Impuestos
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <>
            {/* Financial Indicators Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {renderIndicators(dashboard.indicators)}
            </div>

            {/* Budget and Break-even Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <BudgetList items={dashboard.budget} />
              <BreakEvenSlider {...dashboard.breakEven} />
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-4">
              <button className="flex items-center space-x-2 bg-success-500 hover:bg-success-600 text-white px-6 py-3 rounded-lg transition-colors">
                <FileText className="w-5 h-5" />
                <span>Ver Extractos</span>
              </button>
              
              <button className="flex items-center space-x-2 bg-primary-500 hover:bg-primary-600 text-white px-6 py-3 rounded-lg transition-colors">
                <DollarSign className="w-5 h-5" />
                <span>Procesar Factura</span>
              </button>
              
              <button className="flex items-center space-x-2 bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-lg transition-colors">
                <BarChart3 className="w-5 h-5" />
                <span>Generar Reporte</span>
              </button>
            </div>
          </>
        )}

        {activeTab === 'bookkeeping' && (
          <div className="space-y-6">
            {/* General Ledger */}
            <GeneralLedgerTable 
              entries={generalLedger} 
              isLoading={bookkeepingLoading}
            />
            
            {/* Trial Balance */}
            <TrialBalanceTable 
              accounts={trialBalance} 
              isLoading={bookkeepingLoading}
            />
            
            {/* Aging Report */}
            <AgingReportDisplay 
              agingReport={agingReport}
              isLoading={bookkeepingLoading}
            />
          </div>
        )}

        {activeTab === 'taxes' && (
          <div className="space-y-6">
            {/* Tax Calculation */}
            <TaxCalculationDisplay 
              taxCalculation={taxCalculation}
              isLoading={taxLoading}
            />
            
            {/* Tax Rules Display */}
            {taxRules && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-6">Reglas Tributarias Colombianas</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-3">Información General</h3>
                    <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                      <li><strong>Versión:</strong> {taxRules.version}</li>
                      <li><strong>UVT 2025:</strong> ${taxRules.uvt_2025?.toLocaleString('es-CO')}</li>
                      <li><strong>Moneda:</strong> {taxRules.currency}</li>
                      <li><strong>País:</strong> {taxRules.country}</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-3">Tarifas de IVA</h3>
                    <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                      <li><strong>General:</strong> {(taxRules.iva_rates?.general * 100)?.toFixed(1)}%</li>
                      <li><strong>Reducida:</strong> {(taxRules.iva_rates?.reducida * 100)?.toFixed(1)}%</li>
                      <li><strong>Exento:</strong> {(taxRules.iva_rates?.exento * 100)?.toFixed(1)}%</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default FinanceDashboard;
