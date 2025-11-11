import React, { useRef, useState } from 'react';

interface BulkUploadModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: (summary: any) => void;
}

const BulkUploadModal: React.FC<BulkUploadModalProps> = ({ open, onClose, onSuccess }) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any[] | null>(null);

  if (!open) return null;

  const handleFilesSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    await submitFiles(files);
  };

  const submitFiles = async (files: FileList) => {
    try {
      setSubmitting(true);
      setError(null);

      // Subida concurrente (pool) a /process/upload para mejorar velocidad
      const fileArray = Array.from(files);
      const CONCURRENCY = 4;
      const queue = [...fileArray];
      const perFileResults: any[] = [];

      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010';
      const runWorker = async () => {
        while (queue.length > 0) {
          const f = queue.shift();
          if (!f) break;
          try {
            const single = new FormData();
            single.append('file', f);
            const r = await fetch(`${apiBase}/process/upload`, { method: 'POST', body: single });
            let jd: any = null;
            try { jd = await r.json(); } catch { jd = { success: false, error_message: await r.text() }; }
            const row = {
              filename: f.name,
              success: !!jd?.success,
              total_amount: jd?.total_amount ?? null,
              vendor: jd?.vendor ?? null,
              error_message: jd?.error_message ?? (r.ok ? null : 'Error procesando archivo')
            };
            perFileResults.push(row);
            setResults((prev) => (prev ? [...prev, row] : [row]));
          } catch (e: any) {
            const row = { filename: f.name, success: false, error_message: e?.message || String(e) };
            perFileResults.push(row);
            setResults((prev) => (prev ? [...prev, row] : [row]));
          }
        }
      };

      setResults([]);
      await Promise.all(Array.from({ length: Math.min(CONCURRENCY, queue.length) }, runWorker));

      onSuccess?.({ results: perFileResults });
    } catch (err: any) {
      const msg = err?.message ?? (typeof err === 'string' ? err : JSON.stringify(err));
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">Carga masiva de facturas</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Selecciona múltiples archivos (PDF/JPG/PNG). También puedes arrastrar y soltar.
        </p>

        <div
          className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center mb-4"
          onDragOver={(e) => e.preventDefault()}
          onDrop={async (e) => {
            e.preventDefault();
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
              await submitFiles(e.dataTransfer.files);
            }
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            multiple
            className="hidden"
            onChange={handleFilesSelected}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={submitting}
            className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg disabled:opacity-50"
          >
            {submitting ? 'Cargando...' : 'Seleccionar archivos'}
          </button>
        </div>

        {error && (
          <div className="text-red-600 text-sm mb-3">{error}</div>
        )}

        {results && (
          <div className="max-h-64 overflow-auto border border-gray-200 dark:border-gray-700 rounded">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-200">
                <tr>
                  <th className="text-left p-2">Archivo</th>
                  <th className="text-left p-2">Estado</th>
                  <th className="text-right p-2">Total</th>
                  <th className="text-left p-2">Proveedor</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r: any, idx: number) => (
                  <tr key={idx} className="border-t border-gray-200 dark:border-gray-700">
                    <td className="p-2 text-gray-800 dark:text-gray-200">{r.filename || '-'}</td>
                    <td className="p-2">
                      {r.success ? (
                        <span className="text-green-600">Procesada</span>
                      ) : (
                        <span className="text-red-600">Error</span>
                      )}
                    </td>
                    <td className="p-2 text-right text-gray-800 dark:text-gray-200">
                      {r.total_amount != null ? r.total_amount.toLocaleString('es-CO', { style: 'currency', currency: 'COP' }) : '—'}
                    </td>
                    <td className="p-2 text-gray-800 dark:text-gray-200">{r.vendor || (r.error_message ? (typeof r.error_message === 'string' ? r.error_message : JSON.stringify(r.error_message)) : '—')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {results && (
          <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
            <span className="font-medium text-gray-800 dark:text-gray-200">Resumen: </span>
            {(() => {
              const ok = results.filter((r: any) => r.success).length;
              const fail = results.length - ok;
              return `${ok} procesadas, ${fail} con error`;
            })()}
          </div>
        )}

        <div className="mt-4 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg">
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

export default BulkUploadModal;


