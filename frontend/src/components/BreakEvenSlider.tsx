import React from 'react';
import { BreakEvenSliderProps } from '../types/finance';

const BreakEvenSlider: React.FC<BreakEvenSliderProps> = ({
  percent,
  tooltipLoss,
  tooltipProfit,
  disabled = false
}) => {
  const getSliderColor = (value: number): string => {
    if (value < 30) return 'bg-danger-500';
    if (value < 70) return 'bg-warning-500';
    return 'bg-success-500';
  };

  const getStatusText = (value: number): string => {
    if (value < 30) return 'Zona de Pérdida';
    if (value < 70) return 'Zona de Transición';
    return 'Zona de Ganancia';
  };

  const getStatusColor = (value: number): string => {
    if (value < 30) return 'text-danger-600';
    if (value < 70) return 'text-warning-600';
    return 'text-success-600';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">
          Punto de Equilibrio
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Indicador de rentabilidad actual
        </p>
      </div>

      <div className="space-y-4">
        {/* Slider */}
        <div className="relative">
          <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-300 ${getSliderColor(percent)}`}
              style={{ width: `${percent}%` }}
            ></div>
          </div>
          
          {/* Slider Handle */}
          <div
            className="absolute top-1/2 transform -translate-y-1/2 w-6 h-6 bg-white dark:bg-gray-300 rounded-full shadow-lg border-2 border-primary-500"
            style={{ left: `calc(${percent}% - 12px)` }}
          >
            <div className="w-full h-full rounded-full bg-primary-500 opacity-20"></div>
          </div>
        </div>

        {/* Percentage Display */}
        <div className="flex items-center justify-between">
          <div className="text-center">
            <div className="text-3xl font-bold text-primary-600 dark:text-primary-400">
              {percent}%
            </div>
            <div className={`text-sm font-medium ${getStatusColor(percent)}`}>
              {getStatusText(percent)}
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-danger-500 rounded-full"></div>
            <span>{tooltipLoss}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-success-500 rounded-full"></div>
            <span>{tooltipProfit}</span>
          </div>
        </div>

        {/* Status Message */}
        <div className={`p-3 rounded-lg ${getStatusColor(percent).replace('text-', 'bg-').replace('-600', '-50')} dark:bg-gray-700`}>
          <p className={`text-sm ${getStatusColor(percent)}`}>
            {percent < 30 && '⚠️ Atención: El negocio está en zona de pérdida. Revisar estrategias.'}
            {percent >= 30 && percent < 70 && '⚖️ El negocio está en transición. Monitorear indicadores.'}
            {percent >= 70 && '✅ Excelente: El negocio está en zona de ganancia.'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default BreakEvenSlider;
