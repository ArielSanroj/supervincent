import React, { useState, useEffect } from 'react';
import { FinanceDashboard, FinancialIndicators } from '../types/finance';
// import { financeService } from '../services/financeService';
import IndicatorCard from './IndicatorCard';
import BudgetList from './BudgetList';
import BreakEvenSlider from './BreakEvenSlider';
import LoadingSpinner, { SkeletonCard, ErrorMessage } from './LoadingSpinner';
import GeneralLedgerTable from './GeneralLedgerTable';
import TrialBalanceTable from './TrialBalanceTable';
import TaxCalculationDisplay from './TaxCalculationDisplay';
import AgingReportDisplay from './AgingReportDisplay';
import InvoiceUploadModal from './InvoiceUploadModal';
import BulkUploadModal from './BulkUploadModal';
import LedgerBooks from './LedgerBooks';
import CreateInvoiceModal from './CreateInvoiceModal';
import FinancialStrategiesModal from './FinancialStrategiesModal';
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

// Función para categorizar facturas en rubros presupuestarios
const categorizeInvoice = (vendor: string | null | undefined): string => {
  if (!vendor) return 'Proveedores';
  
  const vendorLower = vendor.toLowerCase();
  
  // Servicios públicos
  if (
    vendorLower.includes('acueducto') ||
    vendorLower.includes('alcantarillado') ||
    vendorLower.includes('energia') ||
    vendorLower.includes('energía') ||
    vendorLower.includes('gas') ||
    vendorLower.includes('electricidad') ||
    vendorLower.includes('agua') ||
    vendorLower.includes('empresas publicas') ||
    vendorLower.includes('empresas públicas') ||
    vendorLower.includes('codensa') ||
    vendorLower.includes('enel') ||
    vendorLower.includes('epm') ||
    vendorLower.includes('fidarta') ||
    vendorLower.includes('rural')
  ) {
    return 'Servicios Públicos';
  }
  
  // Impuestos
  if (
    vendorLower.includes('dian') ||
    vendorLower.includes('impuestos') ||
    vendorLower.includes('renta') ||
    vendorLower.includes('iva') ||
    vendorLower.includes('ica') ||
    vendorLower.includes('retencion') ||
    vendorLower.includes('retención')
  ) {
    return 'Impuestos';
  }
  
  // Personal
  if (
    vendorLower.includes('nómina') ||
    vendorLower.includes('nomina') ||
    vendorLower.includes('salario') ||
    vendorLower.includes('pension') ||
    vendorLower.includes('pensión') ||
    vendorLower.includes('cesantias') ||
    vendorLower.includes('cesantías') ||
    vendorLower.includes('seguridad social') ||
    vendorLower.includes('arl') ||
    vendorLower.includes('eps') ||
    vendorLower.includes('caja de compensación')
  ) {
    return 'Personal';
  }
  
  // Gastos bancarios
  if (
    vendorLower.includes('banco') ||
    vendorLower.includes('bancolombia') ||
    vendorLower.includes('davivienda') ||
    vendorLower.includes('bogota') ||
    vendorLower.includes('bogotá') ||
    vendorLower.includes('bbva') ||
    vendorLower.includes('comisión') ||
    vendorLower.includes('comision') ||
    vendorLower.includes('interés') ||
    vendorLower.includes('interes') ||
    vendorLower.includes('tarjeta') ||
    vendorLower.includes('caja')
  ) {
    return 'Gastos Bancarios';
  }
  
  // Proveedores (por defecto)
  return 'Proveedores';
};

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

  const [withholdings, setWithholdings] = useState<{ reteIcaTotal: number; reteIvaTotal: number; reteRentaTotal: number } | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [bulkOpen, setBulkOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [strategiesOpen, setStrategiesOpen] = useState(false);
  const [recentUploads, setRecentUploads] = useState<Array<{ success: boolean; invoice_id?: string | null; invoice_type?: string | null; total_amount?: number | null; vendor?: string | null; error_message?: string | null; processing_time?: number | null }>>([]);
  const [manualInvoices, setManualInvoices] = useState<Array<{ success: boolean; invoice_id?: string | null; invoice_type?: string | null; total_amount?: number | null; vendor?: string | null; error_message?: string | null; processing_time?: number | null; date?: string | null; timestamp?: string | null }>>([]);
  const [showRecent, setShowRecent] = useState(true);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      // Initialize dashboard with zeros so UI stays consistent
      setDashboard({
        indicators: {
          debtRatio: 0,
          liquidity: 0,
          lastMonthSales: 0,
          lastMonthProfit: 0,
          inventoryTurnoverDays: 0,
          availableCash: 0
        },
        budget: [],
        breakEven: { percent: 0, tooltipLoss: '', tooltipProfit: '' }
      });
      // Fetch withholdings from real processed data
      const w = await fetch('/api/finance/withholdings');
      if (w.ok) {
        const wd = await w.json();
        setWithholdings(wd.data);
      }
      // Fetch recent processed to populate budget
      const r = await fetch('/api/finance/recent');
      if (r.ok) {
        const rd = await r.json();
        const list = rd?.data || [];
        // Merge backend list with manually created invoices (session-only)
        const combined = [...list, ...manualInvoices];
        setRecentUploads(combined);
        // Indicadores del mes: ventas mes y costos mes (por categorías de gasto)
        const now = new Date();
        const ym = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
        const isCurrentMonth = (d?: string) => d ? d.slice(0,7) === ym : false;
        const expenseCategories = new Set(['Servicios Públicos','Impuestos','Personal','Gastos Bancarios','Proveedores']);
        let monthSales = 0;
        let monthCosts = 0;
        for (const it of combined) {
          if (!(it?.success && typeof it?.total_amount === 'number')) continue;
          if (!(isCurrentMonth(it?.date) || isCurrentMonth(it?.timestamp))) continue;
          const category = categorizeInvoice(it.vendor);
          if (expenseCategories.has(category)) {
            monthCosts += Number(it.total_amount) || 0;
          } else {
            monthSales += Number(it.total_amount) || 0;
          }
        }
        const profit = monthSales - monthCosts;
        const availableCash = monthSales - monthCosts;
        setDashboard(prev => prev ? {
          ...prev,
          indicators: {
            debtRatio: prev.indicators.debtRatio ?? 0,
            liquidity: prev.indicators.liquidity ?? 0,
            lastMonthSales: monthSales,
            lastMonthProfit: profit,
            inventoryTurnoverDays: prev.indicators.inventoryTurnoverDays ?? 0,
            availableCash: availableCash,
          },
          breakEven: { ...prev.breakEven, percent: profit > 0 ? 100 : 0 }
        } : prev);
        // Aggregate by budget category with individual invoices
        const byCategory: Record<string, { amount: number; invoices: Array<{ vendor: string; amount: number; date?: string; invoice_id?: string }> }> = {
          'Servicios Públicos': { amount: 0, invoices: [] },
          'Impuestos': { amount: 0, invoices: [] },
          'Personal': { amount: 0, invoices: [] },
          'Gastos Bancarios': { amount: 0, invoices: [] },
          'Proveedores': { amount: 0, invoices: [] }
        };
        for (const it of combined) {
          if (it?.success && typeof it?.total_amount === 'number') {
            const category = categorizeInvoice(it.vendor);
            const catData = byCategory[category];
            catData.amount += it.total_amount || 0;
            catData.invoices.push({
              vendor: it.vendor || 'Proveedor desconocido',
              amount: it.total_amount || 0,
              date: it.date || it.timestamp,
              invoice_id: it.invoice_id
            });
          }
        }
        const budgetItems = Object.entries(byCategory)
          .filter(([_, data]) => data.amount > 0) // Solo mostrar categorías con monto
          .sort((a, b) => b[1].amount - a[1].amount)
          .map(([label, data]) => ({ 
            label, 
            amount: data.amount,
            invoices: data.invoices
          }));
        setDashboard(prev => prev ? { ...prev, budget: budgetItems } : prev);
      }
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
      
      // No automatic calc
      setTaxCalculation(null);
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
        value: indicators.debtRatio ?? 0,
        icon: <BarChart3 className="w-5 h-5" />,
        format: 'percentage' as const,
        trend: 'neutral' as const
      },
      {
        title: 'Liquidez',
        value: indicators.liquidity ?? 0,
        icon: <TrendingUp className="w-5 h-5" />,
        format: 'number' as const,
        trend: 'neutral' as const
      },
      {
        title: 'Ventas mes',
        value: indicators.lastMonthSales ?? 0,
        icon: <DollarSign className="w-5 h-5" />,
        format: 'currency' as const,
        trend: 'neutral' as const
      },
      {
        title: 'Utilidad mes',
        value: indicators.lastMonthProfit ?? 0,
        icon: <PiggyBank className="w-5 h-5" />,
        format: 'currency' as const,
        trend: 'neutral' as const
      },
      {
        title: 'Rotación inventario',
        value: indicators.inventoryTurnoverDays ?? 0,
        icon: <Package className="w-5 h-5" />,
        format: 'days' as const,
        trend: 'neutral' as const
      },
      {
        title: 'Caja disponible',
        value: indicators.availableCash ?? 0,
        icon: <Wallet className="w-5 h-5" />,
        format: 'currency' as const,
        trend: 'neutral' as const
      },
      // Withholding cards
      {
        title: 'ReteICA',
        value: withholdings?.reteIcaTotal ?? 0,
        icon: <Receipt className="w-5 h-5" />,
        format: 'currency' as const,
        trend: 'neutral' as const
      },
      {
        title: 'ReteIVA',
        value: withholdings?.reteIvaTotal ?? 0,
        icon: <Receipt className="w-5 h-5" />,
        format: 'currency' as const,
        trend: 'neutral' as const
      },
      {
        title: 'ReteRenta',
        value: withholdings?.reteRentaTotal ?? 0,
        icon: <Receipt className="w-5 h-5" />,
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
              <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-2 font-display">SuperVincent • Financiero</h1>
              <p className="text-gray-600 dark:text-gray-400">Dashboard financiero en tiempo real</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={loadDashboard}
                className="flex items-center space-x-2 bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Actualizar</span>
              </button>
              <button onClick={() => setUploadOpen(true)} className="flex items-center space-x-2 bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg transition-colors">
                <DollarSign className="w-5 h-5" />
                <span>Subir Soporte Contable</span>
              </button>
              <button onClick={() => setBulkOpen(true)} className="flex items-center space-x-2 bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg transition-colors">
                <FileText className="w-5 h-5" />
                <span>Carga Masiva</span>
              </button>
              <button onClick={() => setCreateOpen(true)} className="flex items-center space-x-2 bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-lg transition-colors">
                <Receipt className="w-5 h-5" />
                <span>Crear Factura</span>
              </button>
              <button onClick={() => setStrategiesOpen(true)} className="flex items-center space-x-2 bg-primary-100 hover:bg-primary-200 text-primary-700 px-4 py-2 rounded-lg transition-colors">
                <BarChart3 className="w-5 h-5" />
                <span>Busquemos estrategias financieras</span>
              </button>
            </div>
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
              Indicadores financieros
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

            {/* Presupuesto y Punto de equilibrio */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <BudgetList items={dashboard.budget} total={0} />
              <BreakEvenSlider percent={dashboard.breakEven.percent} tooltipLoss={dashboard.breakEven.tooltipLoss} tooltipProfit={dashboard.breakEven.tooltipProfit} />
            </div>
            {/* Últimas cargas se movió a Contabilidad */}
          </>
        )}

        {activeTab === 'bookkeeping' && (
          <div className="space-y-6">
            {/* Últimas cargas (colapsable) */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <button
                onClick={() => setShowRecent(!showRecent)}
                className="w-full flex items-center justify-between px-6 py-4"
              >
                <div className="text-left">
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">Últimas cargas</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{recentUploads.length} recientes</p>
                </div>
                <span className={`transform transition-transform ${showRecent ? 'rotate-180' : ''}`}>⌄</span>
              </button>
              {showRecent && (
                <div className="px-6 pb-4">
                  {recentUploads.length === 0 ? (
                    <p className="text-gray-500 dark:text-gray-400">Sin registros.</p>
                  ) : (
                    <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                      {recentUploads.slice().reverse().map((it, idx) => (
                        <li key={idx} className="py-3 flex items-center justify-between">
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                              {it.success ? 'Procesada' : 'Error'} • {it.invoice_type || '-'}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                              {it.vendor || '—'}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                              {typeof it.total_amount === 'number' ? it.total_amount.toLocaleString('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }) : '—'}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {(it as any).date?.slice(0,10) || (it as any).timestamp?.slice(0,10) || ''}
                            </p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>

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
            
            {/* Ledger Books (mayores y menores) */}
            <LedgerBooks
              entries={generalLedger}
              recentUploads={recentUploads}
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
      <InvoiceUploadModal 
        open={uploadOpen} 
        onClose={() => setUploadOpen(false)} 
        onSuccess={(res: any) => {
          // Refresh withholdings after processing a new file
          fetch('/api/finance/withholdings').then(r => r.json()).then(d => setWithholdings(d.data)).catch(() => {});
          // Track recent upload result
          setRecentUploads(prev => [...prev, {
            success: !!res?.success,
            invoice_id: res?.invoice_id ?? null,
            invoice_type: res?.invoice_type ?? null,
            total_amount: res?.total_amount ?? null,
            vendor: res?.vendor ?? null,
            error_message: res?.error_message ?? null,
            processing_time: res?.processing_time ?? null,
          }]);
          // Refresh recent list and recompute presupuesto e indicadores
          fetch('/api/finance/recent')
            .then(r => r.json())
            .then(rd => {
              const list = rd?.data || [];
              setRecentUploads(list);
              // Recalcular indicadores del mes (ventas, costos, utilidad, caja)
              const now = new Date();
              const ym = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
              const isCurrentMonth = (d?: string) => d ? d.slice(0,7) === ym : false;
              const expenseCategories = new Set(['Servicios Públicos','Impuestos','Personal','Gastos Bancarios','Proveedores']);
              let monthSales = 0;
              let monthCosts = 0;
              for (const it of list) {
                if (!(it?.success && typeof it?.total_amount === 'number')) continue;
                if (!(isCurrentMonth(it?.date) || isCurrentMonth(it?.timestamp))) continue;
                const category = categorizeInvoice(it.vendor);
                if (expenseCategories.has(category)) {
                  monthCosts += Number(it.total_amount) || 0;
                } else {
                  monthSales += Number(it.total_amount) || 0;
                }
              }
              const profit = monthSales - monthCosts;
              const availableCash = monthSales - monthCosts;
              // Aggregate by budget category with individual invoices
              const byCategory: Record<string, { amount: number; invoices: Array<{ vendor: string; amount: number; date?: string; invoice_id?: string }> }> = {
                'Servicios Públicos': { amount: 0, invoices: [] },
                'Impuestos': { amount: 0, invoices: [] },
                'Personal': { amount: 0, invoices: [] },
                'Gastos Bancarios': { amount: 0, invoices: [] },
                'Proveedores': { amount: 0, invoices: [] }
              };
              for (const it of list) {
                if (it?.success && typeof it?.total_amount === 'number') {
                  const category = categorizeInvoice(it.vendor);
                  const catData = byCategory[category];
                  catData.amount += it.total_amount || 0;
                  catData.invoices.push({
                    vendor: it.vendor || 'Proveedor desconocido',
                    amount: it.total_amount || 0,
                    date: it.date || it.timestamp,
                    invoice_id: it.invoice_id
                  });
                }
              }
              const budgetItems = Object.entries(byCategory)
                .filter(([_, data]) => data.amount > 0) // Solo mostrar categorías con monto
                .sort((a, b) => b[1].amount - a[1].amount)
                .map(([label, data]) => ({ 
                  label, 
                  amount: data.amount,
                  invoices: data.invoices
                }));
              setDashboard(prev => prev ? { 
                ...prev, 
                budget: budgetItems,
                indicators: {
                  debtRatio: prev.indicators.debtRatio ?? 0,
                  liquidity: prev.indicators.liquidity ?? 0,
                  lastMonthSales: monthSales,
                  lastMonthProfit: profit,
                  inventoryTurnoverDays: prev.indicators.inventoryTurnoverDays ?? 0,
                  availableCash: availableCash,
                },
                breakEven: { ...prev.breakEven, percent: profit > 0 ? 100 : 0 }
              } : prev);
            })
            .catch(() => {});
        }}
      />
      <BulkUploadModal
        open={bulkOpen}
        onClose={() => setBulkOpen(false)}
        onSuccess={() => {
          // Refresh withholdings and budget after bulk upload
          fetch('/api/finance/withholdings').then(r => r.json()).then(d => setWithholdings(d.data)).catch(() => {});
          loadDashboard();
        }}
      />
      <CreateInvoiceModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(inv: any) => {
          const stamped = { ...inv, success: true, invoice_type: 'venta', timestamp: new Date().toISOString() };
          setManualInvoices(prev => [...prev, stamped]);
          setRecentUploads(prev => [...prev, stamped]);
          // Inyectar en libro mayor (UI) y balance de prueba (UI) sin tocar backend
          const amount = Number(stamped.total_amount) || 0;
          const dateStr = (stamped.date || stamped.timestamp || new Date().toISOString()).slice(0,10);
          const vendorName = stamped.vendor || 'Cliente';
          if (amount > 0) {
            setGeneralLedger(prev => [
              ...prev,
              {
                id: `ml-${Date.now()}-d`,
                date: dateStr,
                account_code: '1305',
                account_name: 'Cuentas por cobrar - Clientes',
                description: `Factura venta - ${vendorName}`,
                debit: amount,
                credit: 0,
                balance: amount,
              },
              {
                id: `ml-${Date.now()}-c`,
                date: dateStr,
                account_code: '4135',
                account_name: 'Ingresos por ventas',
                description: `Factura venta - ${vendorName}`,
                debit: 0,
                credit: amount,
                balance: -amount,
              }
            ]);
            setTrialBalance(prev => {
              const next = [...prev];
              const upsert = (code: string, name: string, deltaDebit: number, deltaCredit: number) => {
                const idx = next.findIndex((a: any) => a.account_code === code);
                if (idx === -1) {
                  next.push({
                    account_code: code,
                    account_name: name,
                    debit_balance: Math.max(0, deltaDebit - deltaCredit),
                    credit_balance: Math.max(0, deltaCredit - deltaDebit),
                    total_debit: Math.max(0, deltaDebit),
                    total_credit: Math.max(0, deltaCredit),
                  } as any);
                } else {
                  const a: any = next[idx];
                  a.total_debit = (Number(a.total_debit) || 0) + Math.max(0, deltaDebit);
                  a.total_credit = (Number(a.total_credit) || 0) + Math.max(0, deltaCredit);
                  const debBal = (Number(a.debit_balance) || 0) + Math.max(0, deltaDebit - deltaCredit);
                  const credBal = (Number(a.credit_balance) || 0) + Math.max(0, deltaCredit - deltaDebit);
                  a.debit_balance = debBal;
                  a.credit_balance = credBal;
                }
              };
              upsert('1305', 'Cuentas por cobrar - Clientes', amount, 0);
              upsert('4135', 'Ingresos por ventas', 0, amount);
              return next;
            });
          }
          loadDashboard();
        }}
      />
      <FinancialStrategiesModal open={strategiesOpen} onClose={() => setStrategiesOpen(false)} />
    </div>
  );
};

export default FinanceDashboard;
