import React, { useRef, useState } from 'react';

interface InvoiceUploadModalProps {
	open: boolean;
	onClose: () => void;
	onSuccess?: (result: any) => void;
}

type Mode = 'upload' | 'path';

const InvoiceUploadModal: React.FC<InvoiceUploadModalProps> = ({ open, onClose, onSuccess }) => {
	const [file, setFile] = useState<File | null>(null);
	const [mode, setMode] = useState<Mode>('upload');
	const [localPath, setLocalPath] = useState('');
	const [submitting, setSubmitting] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [duplicateCheck, setDuplicateCheck] = useState<{isDuplicate: boolean; duplicates: any[]; invoiceData: any} | null>(null);
	const [pendingResult, setPendingResult] = useState<any>(null);
	const fileInputRef = useRef<HTMLInputElement | null>(null);

	if (!open) return null;

	const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010';

	const handlePickFile = () => {
		fileInputRef.current?.click();
	};

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setSubmitting(true);
		setError(null);
		setDuplicateCheck(null);
		setPendingResult(null);
		try {
			let data: any = null;
			if (mode === 'upload') {
				if (!file) {
					setError('Selecciona un archivo');
					setSubmitting(false);
					return;
				}
				const formData = new FormData();
				formData.append('file', file);
				const resp = await fetch(`${apiBase}/process/upload`, {
					method: 'POST',
					body: formData
				});
				if (!resp.ok) throw new Error('Error procesando la factura');
				data = await resp.json();
			} else {
				if (!localPath) {
					setError('Ingresa la ruta del archivo');
					setSubmitting(false);
					return;
				}
				const normalizedPath = localPath.startsWith('/') ? localPath : `/${localPath}`;
				const resp = await fetch(`${apiBase}/process`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ file_path: normalizedPath })
				});
				if (!resp.ok) throw new Error('No se pudo acceder a la ruta local. Verifica mayúsculas/minúsculas.');
				data = await resp.json();
			}
			
			// Debug: log response
			console.log('📋 Invoice processing response:', data);
			console.log('🔍 Duplicate check:', {
				success: data.success,
				is_duplicate: data.is_duplicate,
				duplicate_count: data.duplicate_count,
				duplicates: data.duplicates
			});
			
			// Check for duplicates if processing was successful
			if (data.success && data.is_duplicate && data.duplicate_count > 0) {
				console.log('⚠️ Duplicate detected, showing modal');
				setPendingResult(data);
				setDuplicateCheck({
					isDuplicate: true,
					duplicates: data.duplicates || [],
					invoiceData: data
				});
				setSubmitting(false);
				return;
			}
			
			// No duplicate, proceed normally
			onSuccess?.(data);
			onClose();
		} catch (err: any) {
			setError(err.message || 'Error desconocido');
		} finally {
			setSubmitting(false);
		}
	};

	const handleConfirmDuplicate = async () => {
		if (pendingResult && pendingResult.invoice_id) {
			try {
				// Confirm duplicate with backend
				const resp = await fetch(`${apiBase}/process/confirm-duplicate`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ invoice_id: pendingResult.invoice_id })
				});
				if (!resp.ok) throw new Error('Error al confirmar duplicado');
				
				// Success - proceed
				onSuccess?.(pendingResult);
				onClose();
			} catch (err: any) {
				setError(err.message || 'Error al confirmar duplicado');
			}
		}
	};

	const handleCancelDuplicate = () => {
		setDuplicateCheck(null);
		setPendingResult(null);
		setSubmitting(false);
	};

	// Show duplicate confirmation modal if duplicate detected
	if (duplicateCheck?.isDuplicate) {
		return (
			<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
				<div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-lg">
					<div className="p-4 border-b border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20">
						<div className="flex items-center gap-2">
							<span className="text-2xl">⚠️</span>
							<h2 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200">Factura Duplicada Detectada</h2>
						</div>
					</div>
					<div className="p-4 space-y-4">
						<p className="text-sm text-gray-700 dark:text-gray-300">
							Se detectó que esta factura puede ser un duplicado. Se encontraron <strong>{duplicateCheck.duplicates.length}</strong> factura(s) similar(es) procesada(s) anteriormente.
						</p>
						
						<div className="bg-gray-50 dark:bg-gray-700/50 rounded p-3 space-y-2">
							<p className="text-xs font-semibold text-gray-600 dark:text-gray-400">Factura actual:</p>
							<div className="text-sm">
								<p><strong>Proveedor:</strong> {duplicateCheck.invoiceData.vendor || 'N/A'}</p>
								<p><strong>Total:</strong> {(duplicateCheck.invoiceData.total_amount || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP' })}</p>
								<p><strong>Tipo:</strong> {duplicateCheck.invoiceData.invoice_type || 'N/A'}</p>
							</div>
						</div>

						{duplicateCheck.duplicates.length > 0 && (
							<div className="bg-red-50 dark:bg-red-900/20 rounded p-3">
								<p className="text-xs font-semibold text-red-800 dark:text-red-200 mb-2">Factura(s) similar(es) encontrada(s):</p>
								<ul className="space-y-1 text-xs">
									{duplicateCheck.duplicates.map((dup: any, idx: number) => (
										<li key={idx} className="text-red-700 dark:text-red-300">
											• {dup.vendor || 'Proveedor'} - {(dup.total_amount || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP' })} ({dup.date || 'Sin fecha'})
										</li>
									))}
								</ul>
							</div>
						)}

						<p className="text-xs text-gray-600 dark:text-gray-400">
							¿Estás seguro de que deseas procesar esta factura de todas formas?
						</p>
					</div>
					<div className="p-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-2">
						<button 
							onClick={handleCancelDuplicate}
							className="px-4 py-2 rounded-md bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600"
						>
							Cancelar
						</button>
						<button 
							onClick={handleConfirmDuplicate}
							className="px-4 py-2 rounded-md bg-yellow-500 hover:bg-yellow-600 text-white font-semibold"
						>
							Sí, procesar de todas formas
						</button>
					</div>
				</div>
			</div>
		);
	}

	return (
		<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
			<div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md">
				<div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
					<h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200">Procesar Factura</h2>
					<button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
				</div>
				<form onSubmit={handleSubmit} className="p-4 space-y-4">
					<div className="flex gap-2 text-sm">
						<button type="button" onClick={() => setMode('upload')} className={`px-3 py-1 rounded ${mode==='upload' ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200'}`}>Subir archivo</button>
						<button type="button" onClick={() => setMode('path')} className={`px-3 py-1 rounded ${mode==='path' ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200'}`}>Ruta local</button>
					</div>

					{mode === 'upload' ? (
						<div className="space-y-2">
							<input
								ref={fileInputRef}
								type="file"
								accept=".pdf,.jpg,.jpeg,.png"
								onChange={(e) => setFile(e.target.files?.[0] || null)}
								className="hidden"
							/>
							<button type="button" onClick={handlePickFile} className="px-3 py-2 rounded-md bg-primary-500 hover:bg-primary-600 text-white">
								Seleccionar archivo (PDF/JPG/PNG)
							</button>
							{file && <div className="text-sm text-gray-700 dark:text-gray-200 truncate">Seleccionado: {file.name}</div>}
						</div>
					) : (
						<div>
							<label className="block text-sm text-gray-600 dark:text-gray-300 mb-2">Ruta absoluta del archivo</label>
							<input
								type="text"
								placeholder="/Users/arielsanroj/Downloads/testfactura2.jpg"
								value={localPath}
								onChange={(e) => setLocalPath(e.target.value)}
								className="w-full text-sm px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100"
							/>
							<p className="text-xs text-gray-500 mt-1">Nota: Respetar mayúsculas/minúsculas (ej. "/Users" con U mayúscula)</p>
						</div>
					)}

					{error && <div className="text-red-600 text-sm">{error}</div>}
					<div className="flex items-center justify-end gap-2">
						<button type="button" onClick={onClose} className="px-4 py-2 rounded-md bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200">Cancelar</button>
						<button disabled={submitting || (mode==='upload' ? !file : !localPath)} type="submit" className="px-4 py-2 rounded-md bg-primary-500 hover:bg-primary-600 text-white disabled:opacity-50">
							{submitting ? 'Procesando…' : 'Procesar'}
						</button>
					</div>
				</form>
			</div>
		</div>
	);
};

export default InvoiceUploadModal;

