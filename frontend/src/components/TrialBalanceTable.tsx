import React from 'react';
import { TrialBalanceAccount } from '../types/finance';

interface TrialBalanceTableProps {
  accounts: TrialBalanceAccount[];
  isLoading?: boolean;
}

const TrialBalanceTable: React.FC<TrialBalanceTableProps> = ({ accounts, isLoading }) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const totalDebit = accounts.reduce((sum, account: any) => sum + (Number(account.total_debit) || 0), 0);
  const totalCredit = accounts.reduce((sum, account: any) => sum + (Number(account.total_credit) || 0), 0);

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
        ⚖️ Balance de Prueba
      </h3>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Código
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Nombre de Cuenta
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Saldo Débito
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Saldo Crédito
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total Débito
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total Crédito
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {accounts.map((account: any, index) => {
              const debitBalance = Number(account.debit_balance) || 0;
              const creditBalance = Number(account.credit_balance) || 0;
              const totalDebitAcc = Number(account.total_debit) || 0;
              const totalCreditAcc = Number(account.total_credit) || 0;
              const accountCode = account.account_code || '-';
              const accountName = account.account_name || '-';
              return (
              <tr key={account.account_code} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600">
                  {accountCode}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  {accountName}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                  {debitBalance > 0 ? formatCurrency(debitBalance) : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                  {creditBalance > 0 ? formatCurrency(creditBalance) : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                  {totalDebitAcc > 0 ? formatCurrency(totalDebitAcc) : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                  {totalCreditAcc > 0 ? formatCurrency(totalCreditAcc) : '-'}
                </td>
              </tr>
            );})}
          </tbody>
          <tfoot className="bg-gray-100">
            <tr className="font-semibold">
              <td colSpan={2} className="px-6 py-3 text-sm text-gray-800">
                TOTALES
              </td>
              <td className="px-6 py-3 text-sm text-right text-gray-800">
                {formatCurrency(accounts.reduce((sum, acc: any) => sum + (Number(acc.debit_balance) || 0), 0))}
              </td>
              <td className="px-6 py-3 text-sm text-right text-gray-800">
                {formatCurrency(accounts.reduce((sum, acc: any) => sum + (Number(acc.credit_balance) || 0), 0))}
              </td>
              <td className="px-6 py-3 text-sm text-right text-gray-800">
                {formatCurrency(totalDebit)}
              </td>
              <td className="px-6 py-3 text-sm text-right text-gray-800">
                {formatCurrency(totalCredit)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
      
      {/* Balance verification */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-blue-800">
            Verificación del Balance:
          </span>
          <span className={`text-sm font-semibold ${
            Math.abs(totalDebit - totalCredit) < 0.01 
              ? 'text-green-600' 
              : 'text-red-600'
          }`}>
            {Math.abs(totalDebit - totalCredit) < 0.01 
              ? '✅ Balanceado' 
              : '❌ Desbalanceado'}
          </span>
        </div>
        <div className="text-xs text-blue-600 mt-1">
          Diferencia: {formatCurrency(Math.abs(totalDebit - totalCredit))}
        </div>
      </div>
      
      {accounts.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No hay cuentas en el balance de prueba para el período seleccionado.
        </div>
      )}
    </div>
  );
};

export default TrialBalanceTable;
