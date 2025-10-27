import React from 'react';
import { BudgetListProps } from '../types/finance';

const BudgetList: React.FC<BudgetListProps> = ({ items, total }) => {
  const formatCurrency = (amount: number | null): string => {
    if (amount === null || amount === undefined) return '—';
    
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const calculateTotal = (): number => {
    if (total !== undefined) return total;
    return items.reduce((sum, item) => sum + (item.amount || 0), 0);
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
          <div className="space-y-3 mb-6">
            {items.map((item, index) => (
              <div
                key={index}
                className="flex items-center justify-between py-3 px-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-primary-500 rounded-full"></div>
                  <span className="text-gray-700 dark:text-gray-300 font-medium">
                    {item.label}
                  </span>
                </div>
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
              </div>
            ))}
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
