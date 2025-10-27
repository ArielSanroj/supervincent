import React from 'react';
import { TaxCalculation, TaxBreakdown } from '../types/finance';

interface TaxCalculationDisplayProps {
  taxCalculation: TaxCalculation | null;
  isLoading?: boolean;
}

const TaxCalculationDisplay: React.FC<TaxCalculationDisplayProps> = ({ 
  taxCalculation, 
  isLoading 
}) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (rate: number) => {
    return `${(rate * 100).toFixed(2)}%`;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!taxCalculation) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          🧾 Cálculo de Impuestos Colombianos
        </h3>
        <p className="text-gray-600">No hay datos de cálculo de impuestos disponibles.</p>
      </div>
    );
  }

  const breakdown = taxCalculation.tax_breakdown;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-800">
          🧾 Cálculo de Impuestos Colombianos
        </h3>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          taxCalculation.compliance_status === 'compliant' 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          {taxCalculation.compliance_status === 'compliant' ? '✅ Cumple' : '❌ No Cumple'}
        </span>
      </div>

      {/* Resumen General Section */}
      <div className="mb-6">
        <h4 className="text-md font-semibold text-gray-700 mb-3 flex items-center">
          <span className="mr-2">📋</span>
          Resumen General
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          {/* Monto Base */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="text-center">
              <span className="text-sm text-gray-600 block mb-1">Monto Base</span>
              <p className="text-lg font-semibold text-gray-800">
                {formatCurrency(breakdown.totals.base_amount)}
              </p>
            </div>
          </div>
          
          {/* IVA */}
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="text-center">
              <span className="text-sm text-gray-600 block mb-1">IVA</span>
              <p className="text-lg font-semibold text-blue-600">
                {formatCurrency(breakdown.iva.amount)}
              </p>
              <p className="text-xs text-blue-500">
                {formatPercentage(breakdown.iva.rate)}
              </p>
            </div>
          </div>
          
          {/* Total */}
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="text-center">
              <span className="text-sm text-gray-600 block mb-1">Total</span>
              <p className="text-lg font-semibold text-green-600">
                {formatCurrency(breakdown.totals.total_amount)}
              </p>
            </div>
          </div>
          
          {/* Neto */}
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <div className="text-center">
              <span className="text-sm text-gray-600 block mb-1">Neto</span>
              <p className="text-lg font-semibold text-purple-600">
                {formatCurrency(breakdown.totals.net_amount)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Retenciones Section */}
      <div className="mb-6">
        <h4 className="text-md font-semibold text-gray-700 mb-3 flex items-center">
          <span className="mr-2">💰</span>
          Retenciones en la Fuente
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* ReteRenta */}
          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <div className="text-center">
              <span className="text-sm text-gray-600 block mb-1">ReteRenta</span>
              <p className="text-lg font-semibold text-red-600">
                {formatCurrency(breakdown.retefuente.renta.amount)}
              </p>
              <p className="text-xs text-red-500">
                {formatPercentage(breakdown.retefuente.renta.rate)}
              </p>
            </div>
          </div>
          
          {/* ReteIVA */}
          <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
            <div className="text-center">
              <span className="text-sm text-gray-600 block mb-1">ReteIVA</span>
              <p className="text-lg font-semibold text-orange-600">
                {formatCurrency(breakdown.retefuente.iva.amount)}
              </p>
              <p className="text-xs text-orange-500">
                {formatPercentage(breakdown.retefuente.iva.rate)}
              </p>
            </div>
          </div>
          
          {/* ReteICA */}
          <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
            <div className="text-center">
              <span className="text-sm text-gray-600 block mb-1">ReteICA</span>
              <p className="text-lg font-semibold text-yellow-600">
                {formatCurrency(breakdown.retefuente.ica.amount)}
              </p>
              <p className="text-xs text-yellow-500">
                {formatPercentage(breakdown.retefuente.ica.rate)}
              </p>
            </div>
          </div>
        </div>
        
        {/* Total Retenciones */}
        <div className="mt-4 bg-gray-100 rounded-lg p-4">
          <div className="text-center">
            <span className="text-sm text-gray-600 block mb-1">Total Retenciones</span>
            <p className="text-xl font-bold text-gray-800">
              {formatCurrency(taxCalculation.total_withholdings)}
            </p>
          </div>
        </div>
      </div>

      {/* Totals Section */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-md font-semibold text-gray-700 mb-3 flex items-center">
          <span className="mr-2">📈</span>
          Resumen Total
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-600">Monto Total:</span>
            <p className="text-xl font-bold text-gray-800">
              {formatCurrency(breakdown.totals.total_amount)}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Monto Neto:</span>
            <p className="text-xl font-bold text-green-600">
              {formatCurrency(breakdown.totals.net_amount)}
            </p>
          </div>
        </div>
      </div>

      {/* Compliance Status */}
      <div className="mt-4 p-3 bg-gray-100 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">
            Estado de Cumplimiento:
          </span>
          <span className={`text-sm font-semibold ${
            taxCalculation.compliance_status === 'compliant' 
              ? 'text-green-600' 
              : 'text-red-600'
          }`}>
            {taxCalculation.compliance_status === 'compliant' 
              ? '✅ Cumple con normativa DIAN' 
              : '❌ Requiere revisión'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default TaxCalculationDisplay;
