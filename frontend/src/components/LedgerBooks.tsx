import React, { useMemo, useState } from 'react';

interface LedgerBooksProps {
  entries: any[];
  recentUploads: any[];
}

const LedgerBooks: React.FC<LedgerBooksProps> = ({ entries, recentUploads }) => {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [selected, setSelected] = useState<any | null>(null);

  const groups = useMemo(() => {
    const map: Record<string, { code: string; name: string; items: any[] }> = {};
    for (const e of entries) {
      const code = (e as any).account_code || '—';
      const name = (e as any).account_name || '—';
      const key = `${code}::${name}`;
      if (!map[key]) map[key] = { code, name, items: [] };
      map[key].items.push(e);
    }
    // sort each group by date desc
    Object.values(map).forEach(g => g.items.sort((a: any, b: any) => new Date(b.date).getTime() - new Date(a.date).getTime()));
    return map;
  }, [entries]);

  const openSupport = (entry: any) => {
    const reference = (entry as any).reference;
    const match = reference ? (recentUploads || []).find((u: any) => u.invoice_id === reference) : null;
    setSelected({ entry, support: match || null });
  };

  const formatCurrency = (amount: number) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount || 0);
  const formatDate = (dateString: string) => new Date(dateString).toLocaleDateString('es-CO');

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">📚 Libros mayores y menores</h3>
      <div className="space-y-3">
        {Object.entries(groups).map(([key, group]) => (
          <div key={key} className="border border-gray-200 dark:border-gray-700 rounded-lg">
            <button
              onClick={() => setExpanded(prev => ({ ...prev, [key]: !prev[key] }))}
              className="w-full flex items-center justify-between px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <span className="text-sm font-mono text-gray-600 dark:text-gray-400">{group.code}</span>
                <span className="text-gray-800 dark:text-gray-200 font-medium">{group.name}</span>
                <span className="text-xs text-gray-500">({group.items.length} apuntes)</span>
              </div>
              <span className={`transform transition-transform ${expanded[key] ? 'rotate-90' : ''}`}>▸</span>
            </button>
            {expanded[key] && (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {group.items.map((it: any, idx: number) => {
                  const debit = Number(it.debit) || 0;
                  const credit = Number(it.credit) || 0;
                  return (
                    <div key={idx} className="flex items-center justify-between px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <div className="min-w-0">
                        <div className="text-sm text-gray-800 dark:text-gray-200">{it.description || 'Apunte'}</div>
                        <div className="text-xs text-gray-500">{formatDate(it.date)} • Ref: {(it as any).reference || '—'}</div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-sm text-gray-800 dark:text-gray-200 w-28 text-right">{debit > 0 ? formatCurrency(debit) : '—'}</div>
                        <div className="text-sm text-gray-800 dark:text-gray-200 w-28 text-right">{credit > 0 ? formatCurrency(credit) : '—'}</div>
                        <button onClick={() => openSupport(it)} className="text-sm px-3 py-1 bg-primary-100 text-primary-700 rounded hover:bg-primary-200">Ver soporte</button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-xl bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-200">Soporte contable</h4>
              <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-gray-700">✕</button>
            </div>
            <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
              <div><span className="font-medium">Fecha:</span> {formatDate(selected.entry.date)}</div>
              <div><span className="font-medium">Cuenta:</span> {(selected.entry as any).account_code} — {(selected.entry as any).account_name}</div>
              <div><span className="font-medium">Descripción:</span> {selected.entry.description || '—'}</div>
              <div><span className="font-medium">Referencia:</span> {(selected.entry as any).reference || '—'}</div>
              <div className="mt-3 border-t border-gray-200 dark:border-gray-700 pt-3">
                <div className="font-semibold mb-1">Detalle del soporte</div>
                {selected.support ? (
                  <ul className="space-y-1">
                    <li><span className="font-medium">Proveedor:</span> {selected.support.vendor || '—'}</li>
                    <li><span className="font-medium">Monto:</span> {formatCurrency(selected.support.total_amount || 0)}</li>
                    <li><span className="font-medium">Fecha doc:</span> {(selected.support.date || selected.support.timestamp || '').toString().slice(0,10)}</li>
                    <li><span className="font-medium">Archivo:</span> {selected.support.filename || '—'}</li>
                    <li className="text-xs text-gray-500">El archivo se encuentra en el servidor (uploads). Si quieres, puedo habilitar descarga.</li>
                  </ul>
                ) : (
                  <div className="text-gray-500">No se encontró soporte vinculado para esta referencia.</div>
                )}
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button onClick={() => setSelected(null)} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg">Cerrar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LedgerBooks;


