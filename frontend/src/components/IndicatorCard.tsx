import React from 'react';
import { IndicatorCardProps } from '../types/finance';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const IndicatorCard: React.FC<IndicatorCardProps> = ({
  title,
  value,
  icon,
  trend = 'neutral',
  format = 'number'
}) => {
  const formatValue = (val: string | number | null): string => {
    if (val === null || val === undefined) return '—';
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('es-CO', {
          style: 'currency',
          currency: 'COP',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(Number(val));
      
      case 'percentage':
        return `${val}%`;
      
      case 'days':
        return `${val} días`;
      
      case 'number':
      default:
        return new Intl.NumberFormat('es-CO').format(Number(val));
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-success-500" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-danger-500" />;
      default:
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-success-600';
      case 'down':
        return 'text-danger-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 card-hover">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          {icon && <div className="text-primary-500">{icon}</div>}
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-300">
            {title}
          </h3>
        </div>
        {getTrendIcon()}
      </div>
      
      <div className={`text-2xl font-bold ${getTrendColor()}`}>
        {formatValue(value)}
      </div>
      
      {trend !== 'neutral' && (
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {trend === 'up' ? '↗ Aumentó' : '↘ Disminuyó'} este mes
        </div>
      )}
    </div>
  );
};

export default IndicatorCard;
