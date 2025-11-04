import React, { useState } from 'react';

interface FinancialStrategiesModalProps {
  open: boolean;
  onClose: () => void;
}

const FinancialStrategiesModal: React.FC<FinancialStrategiesModalProps> = ({ open, onClose }) => {
  const [prompt, setPrompt] = useState('Quiero estrategias para mejorar liquidez y utilidad.');
  const [answer, setAnswer] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const ask = async () => {
    try {
      setLoading(true);
      setError(null);
      // Placeholder: aquí se integraría la llamada a Ollama vía backend existente
      // Simulamos una respuesta breve mientras no haya endpoint dedicado
      const simulated = 'Sugerencias: 1) Negociar plazos con proveedores. 2) Ofrecer descuentos por pronto pago. 3) Priorizar compras con mayor rotación. 4) Reducir gastos bancarios optimizando comisiones.';
      await new Promise(r => setTimeout(r, 500));
      setAnswer(simulated);
    } catch (e: any) {
      setError(e?.message || 'Error consultando estrategias');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">Estrategias financieras</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <div className="space-y-3">
          <textarea value={prompt} onChange={e => setPrompt(e.target.value)} rows={4} className="w-full border rounded px-3 py-2 bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-200" />
          <div className="flex justify-end">
            <button onClick={ask} disabled={loading} className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded disabled:opacity-50">
              {loading ? 'Pensando...' : 'Preguntar'}
            </button>
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          {answer && (
            <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{answer}</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FinancialStrategiesModal;


