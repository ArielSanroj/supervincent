import React, { useState } from 'react';

interface CreateInvoiceModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (invoice: any) => void;
}

const CreateInvoiceModal: React.FC<CreateInvoiceModalProps> = ({ open, onClose, onCreated }) => {
  const [vendor, setVendor] = useState('');
  const [client, setClient] = useState('Cliente');
  const [date, setDate] = useState<string>(() => new Date().toISOString().slice(0,10));
  const [amount, setAmount] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const parseAmount = (s: string) => {
    const n = Number(String(s).replace(/[^0-9.,]/g, '').replace(/\./g, '').replace(/,/g, '.'));
    return isFinite(n) ? n : 0;
  };

  const handleCreate = async () => {
    try {
      setSubmitting(true);
      setError(null);
      const total = parseAmount(amount);
      if (!vendor || total <= 0) {
        throw new Error('Completa proveedor y monto válido');
      }
      // Crear realmente en backend local para que alimente recientes, contabilidad y presupuesto
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010';
      let created = false;
      try {
        const resp = await fetch(`${apiBase}/process/manual`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ vendor, total_amount: total, date, client })
        });
        const data = await resp.json();
        if (resp.ok && data?.success) {
          const invoice = {
            success: true,
            invoice_id: data.invoice_id,
            invoice_type: data.invoice_type,
            total_amount: data.total_amount,
            vendor: data.vendor,
            client,
            date: data.date,
            processing_time: data.processing_time,
          };
          onCreated(invoice);
          created = true;
        }
      } catch (_) {
        // ignore, fallback below
      }
      if (!created) {
        // Fallback local si el endpoint no existe todavía
        const invoice = {
          success: true,
          invoice_id: `loc_${Date.now()}`,
          invoice_type: 'venta',
          total_amount: total,
          vendor,
          client,
          date,
          processing_time: 0.01,
        };
        onCreated(invoice);
      }
      onClose();
    } catch (e: any) {
      setError(e?.message || 'Error creando factura');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">Crear factura de venta</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">Proveedor</label>
            <input value={vendor} onChange={e => setVendor(e.target.value)} className="w-full border rounded px-3 py-2 bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-200" placeholder="Nombre del proveedor" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">Cliente</label>
            <input value={client} onChange={e => setClient(e.target.value)} className="w-full border rounded px-3 py-2 bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-200" placeholder="Nombre del cliente" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">Fecha</label>
              <input type="date" value={date} onChange={e => setDate(e.target.value)} className="w-full border rounded px-3 py-2 bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-200" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">Monto total</label>
              <input value={amount} onChange={e => setAmount(e.target.value)} className="w-full border rounded px-3 py-2 bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-200" placeholder="$ 0" />
            </div>
          </div>
        </div>

        {error && <div className="mt-3 text-sm text-red-600">{error}</div>}

        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded">Cancelar</button>
          <button onClick={handleCreate} disabled={submitting} className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded disabled:opacity-50">
            {submitting ? 'Creando...' : 'Crear'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateInvoiceModal;


