import React, { useState } from 'react';
import { BudgetListProps } from '../types/finance';

const BudgetList: React.FC<BudgetListProps> = ({ items, total }) => {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const formatCurrency = (amount: number | null): string => {
    if (amount === null || amount === undefined) return '—';
    
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (date?: string): string => {
    if (!date) return '';
    try {
      const d = new Date(date);
      return d.toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return date;
    }
  };

  const calculateTotal = (): number => {
    if (total !== undefined) return total;
    return items.reduce((sum, item) => sum + (item.amount || 0), 0);
  };

  const toggleExpanded = (label: string) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  };

  const budgetTotal = calculateTotal();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
          Presupuesto
        </h2>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {items.length} categorías
        </div>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-gray-400 dark:text-gray-500 mb-2">
            📊
          </div>
          <p className="text-gray-500 dark:text-gray-400">
            Sin datos de presupuesto
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-2 mb-6">
            {items.map((item, index) => {
              const isExpanded = expandedItems.has(item.label);
              const hasInvoices = item.invoices && item.invoices.length > 0;
              
              return (
                <div
                  key={index}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
                >
                  {/* Header - Clickable para expandir/contraer */}
                  <button
                    onClick={() => toggleExpanded(item.label)}
                    className="w-full flex items-center justify-between py-3 px-4 bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-3 h-3 bg-primary-500 rounded-full"></div>
                      <span className="text-gray-700 dark:text-gray-300 font-medium text-left">
                        {item.label}
                      </span>
                      {hasInvoices && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          ({item.invoices!.length} {item.invoices!.length === 1 ? 'factura' : 'facturas'})
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="text-right">
                        <div className="font-semibold text-gray-800 dark:text-gray-200">
                          {formatCurrency(item.amount)}
                        </div>
                        {item.amount && budgetTotal > 0 && (
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {((item.amount / budgetTotal) * 100).toFixed(1)}%
                          </div>
                        )}
                      </div>
                      {hasInvoices && (
                        <svg
                          className={`w-5 h-5 text-gray-500 dark:text-gray-400 transition-transform ${
                            isExpanded ? 'rotate-180' : ''
                          }`}
                          fill="none"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path d="M19 9l-7 7-7-7"></path>
                        </svg>
                      )}
                    </div>
                  </button>
                  
                  {/* Contenido expandible - Lista de facturas */}
                  {isExpanded && hasInvoices && (
                    <div className="border-t border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800">
                      <div className="p-3 space-y-2">
                        {item.invoices!.map((invoice, invIndex) => (
                          <div
                            key={invIndex}
                            className="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-700/50 rounded-md"
                          >
                            <div className="flex-1">
                              <div className="text-sm font-medium text-gray-800 dark:text-gray-200">
                                {invoice.vendor || 'Proveedor desconocido'}
                              </div>
                              {invoice.date && (
                                <div className="text-xs text-gray-500 dark:text-gray-400">
                                  {formatDate(invoice.date)}
                                </div>
                              )}
                            </div>
                            <div className="text-right">
                              <div className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                                {formatCurrency(invoice.amount)}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="border-t border-gray-200 dark:border-gray-600 pt-4">
            <div className="flex items-center justify-between">
              <span className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                Total Presupuesto
              </span>
              <span className="text-xl font-bold text-primary-600 dark:text-primary-400">
                {formatCurrency(budgetTotal)}
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default BudgetList;
