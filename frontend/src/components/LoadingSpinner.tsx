import React from 'react';

const LoadingSpinner: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Cargando datos financieros...</p>
      </div>
    </div>
  );
};

export const SkeletonCard: React.FC = () => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 animate-pulse">
      <div className="flex items-center justify-between mb-4">
        <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-24"></div>
        <div className="h-4 w-4 bg-gray-200 dark:bg-gray-600 rounded"></div>
      </div>
      <div className="h-8 bg-gray-200 dark:bg-gray-600 rounded w-32 mb-2"></div>
      <div className="h-3 bg-gray-200 dark:bg-gray-600 rounded w-20"></div>
    </div>
  );
};

export const ErrorMessage: React.FC<{ message: string; onRetry?: () => void }> = ({ 
  message, 
  onRetry 
}) => {
  return (
    <div className="bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-lg p-6 text-center">
      <div className="text-danger-500 dark:text-danger-400 mb-4">
        <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-danger-800 dark:text-danger-200 mb-2">
        Error al cargar datos
      </h3>
      <p className="text-danger-600 dark:text-danger-300 mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="bg-danger-500 hover:bg-danger-600 text-white px-4 py-2 rounded-lg transition-colors"
        >
          Reintentar
        </button>
      )}
    </div>
  );
};

export default LoadingSpinner;
