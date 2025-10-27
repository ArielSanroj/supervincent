import React from 'react';
import { GeneralLedgerEntry } from '../types/finance';

interface GeneralLedgerTableProps {
  entries: GeneralLedgerEntry[];
  isLoading?: boolean;
}

const GeneralLedgerTable: React.FC<GeneralLedgerTableProps> = ({ entries, isLoading }) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-CO');
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        📊 Libro Mayor General
      </h3>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Fecha
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Código
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cuenta
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Descripción
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Débito
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Crédito
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Saldo
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {entries.map((entry) => (
              <tr key={entry.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatDate(entry.date)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600">
                  {entry.account_code}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {entry.account_name}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  {entry.description}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                  {entry.debit > 0 ? formatCurrency(entry.debit) : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                  {entry.credit > 0 ? formatCurrency(entry.credit) : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                  <span className={entry.balance >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatCurrency(Math.abs(entry.balance))}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {entries.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No hay entradas en el libro mayor para el período seleccionado.
        </div>
      )}
    </div>
  );
};

export default GeneralLedgerTable;
