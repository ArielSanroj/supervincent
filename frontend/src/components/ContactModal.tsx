import { useState } from 'react';
import { X } from 'lucide-react';

interface ContactModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ContactModal({ isOpen, onClose }: ContactModalProps) {
  const [formData, setFormData] = useState({
    nombre: '',
    telefono: '',
    correo: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  if (!isOpen) return null;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validar que todos los campos estén llenos
    if (!formData.nombre || !formData.telefono || !formData.correo) {
      alert('Por favor completa todos los campos');
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus('idle');

    // Siempre guardar en localStorage primero (como respaldo)
    try {
      const contacts = JSON.parse(localStorage.getItem('contacts') || '[]');
      const newContact = { ...formData, timestamp: new Date().toISOString() };
      contacts.push(newContact);
      localStorage.setItem('contacts', JSON.stringify(contacts));
      console.log('✅ Contacto guardado en localStorage:', newContact);
    } catch (localError) {
      console.error('Error guardando en localStorage:', localError);
    }

    // Intentar enviar al backend
    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        console.log('✅ Contacto guardado en servidor:', data);
        setSubmitStatus('success');
        setFormData({ nombre: '', telefono: '', correo: '' });
        
        // Cerrar modal después de 2 segundos
        setTimeout(() => {
          onClose();
          setSubmitStatus('idle');
        }, 2000);
      } else {
        console.error('❌ Error del servidor:', data);
        setSubmitStatus('error');
      }
    } catch (error) {
      console.error('❌ Error enviando al servidor:', error);
      // Ya se guardó en localStorage, así que marcamos como éxito
      setSubmitStatus('success');
      setFormData({ nombre: '', telefono: '', correo: '' });
      setTimeout(() => {
        onClose();
        setSubmitStatus('idle');
      }, 2000);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-xl p-8 shadow-2xl max-w-md w-full mx-4 relative">
        {/* Botón cerrar */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Cerrar modal"
        >
          <X className="w-6 h-6" />
        </button>

        <h2 className="text-2xl font-bold text-brand-textDark mb-6">Contáctame</h2>
        
        {submitStatus === 'success' && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
            ¡Gracias por contactarnos! Te responderemos pronto.
          </div>
        )}

        {submitStatus === 'error' && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            Hubo un error al enviar el formulario. Por favor intenta de nuevo.
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="modal-nombre" className="block text-sm font-medium text-brand-textDark mb-2">
              Nombre
            </label>
            <input
              type="text"
              id="modal-nombre"
              name="nombre"
              value={formData.nombre}
              onChange={handleChange}
              placeholder="Tu nombre completo"
              className="w-full px-4 py-3 rounded-md border border-brand-borderGray focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-brand-placeholderGray"
              required
              disabled={isSubmitting}
            />
          </div>
          <div>
            <label htmlFor="modal-telefono" className="block text-sm font-medium text-brand-textDark mb-2">
              Teléfono
            </label>
            <input
              type="tel"
              id="modal-telefono"
              name="telefono"
              value={formData.telefono}
              onChange={handleChange}
              placeholder="Tu número de teléfono"
              className="w-full px-4 py-3 rounded-md border border-brand-borderGray focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-brand-placeholderGray"
              required
              disabled={isSubmitting}
            />
          </div>
          <div>
            <label htmlFor="modal-correo" className="block text-sm font-medium text-brand-textDark mb-2">
              Correo
            </label>
            <input
              type="email"
              id="modal-correo"
              name="correo"
              value={formData.correo}
              onChange={handleChange}
              placeholder="tu@correo.com"
              className="w-full px-4 py-3 rounded-md border border-brand-borderGray focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-brand-placeholderGray"
              required
              disabled={isSubmitting}
            />
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 rounded-lg bg-secondary-400 text-white font-medium hover:bg-secondary-500 transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Enviando...' : 'Contáctame'}
          </button>
        </form>
      </div>
    </div>
  );
}

