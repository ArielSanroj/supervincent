import React from 'react';
import { AgingReport } from '../types/finance';

interface AgingReportDisplayProps {
  agingReport: AgingReport | null;
  isLoading?: boolean;
}

const AgingReportDisplay: React.FC<AgingReportDisplayProps> = ({ 
  agingReport, 
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

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!agingReport) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          📅 Reporte de Antigüedad de Saldos
        </h3>
        <p className="text-gray-600">No hay datos del reporte de antigüedad de saldos disponibles.</p>
      </div>
    );
  }

  const { receivables, payables, net_position } = agingReport;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-6">
        📅 Reporte de Antigüedad de Saldos
      </h3>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-green-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-green-800 mb-2">
            Cuentas por Cobrar
          </h4>
          <p className="text-2xl font-bold text-green-600">
            {formatCurrency(receivables.total)}
          </p>
        </div>
        
        <div className="bg-red-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-red-800 mb-2">
            Cuentas por Pagar
          </h4>
          <p className="text-2xl font-bold text-red-600">
            {formatCurrency(payables.total)}
          </p>
        </div>
        
        <div className={`rounded-lg p-4 ${
          net_position >= 0 ? 'bg-blue-50' : 'bg-orange-50'
        }`}>
          <h4 className={`text-sm font-medium mb-2 ${
            net_position >= 0 ? 'text-blue-800' : 'text-orange-800'
          }`}>
            Posición Neta
          </h4>
          <p className={`text-2xl font-bold ${
            net_position >= 0 ? 'text-blue-600' : 'text-orange-600'
          }`}>
            {formatCurrency(net_position)}
          </p>
        </div>
      </div>

      {/* Aging Buckets */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Receivables Aging */}
        <div className="bg-green-50 rounded-lg p-4">
          <h4 className="text-md font-semibold text-green-800 mb-4">
            📈 Cuentas por Cobrar - Antigüedad
          </h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">0-30 días:</span>
              <span className="font-semibold text-green-600">
                {formatCurrency(receivables.aging.current)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">31-60 días:</span>
              <span className="font-semibold text-yellow-600">
                {formatCurrency(receivables.aging.days_31_60)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">61-90 días:</span>
              <span className="font-semibold text-orange-600">
                {formatCurrency(receivables.aging.days_61_90)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Más de 90 días:</span>
              <span className="font-semibold text-red-600">
                {formatCurrency(receivables.aging.over_90)}
              </span>
            </div>
          </div>
        </div>

        {/* Payables Aging */}
        <div className="bg-red-50 rounded-lg p-4">
          <h4 className="text-md font-semibold text-red-800 mb-4">
            📉 Cuentas por Pagar - Antigüedad
          </h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">0-30 días:</span>
              <span className="font-semibold text-green-600">
                {formatCurrency(payables.aging.current)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">31-60 días:</span>
              <span className="font-semibold text-yellow-600">
                {formatCurrency(payables.aging.days_31_60)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">61-90 días:</span>
              <span className="font-semibold text-orange-600">
                {formatCurrency(payables.aging.days_61_90)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Más de 90 días:</span>
              <span className="font-semibold text-red-600">
                {formatCurrency(payables.aging.over_90)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="mt-6 bg-blue-50 rounded-lg p-4">
        <h4 className="text-md font-semibold text-blue-800 mb-2">
          💡 Recomendaciones
        </h4>
        <ul className="text-sm text-blue-700 space-y-1">
          {receivables.aging.over_90 > 0 && (
            <li>• Revisar cuentas por cobrar vencidas por más de 90 días</li>
          )}
          {payables.aging.over_90 > 0 && (
            <li>• Priorizar pagos de cuentas por pagar vencidas</li>
          )}
          {net_position < 0 && (
            <li>• Considerar estrategias para mejorar el flujo de caja</li>
          )}
          {receivables.total > payables.total * 2 && (
            <li>• Implementar políticas de cobro más agresivas</li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default AgingReportDisplay;
