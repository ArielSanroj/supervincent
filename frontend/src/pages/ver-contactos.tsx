import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';

interface Contact {
  nombre: string;
  apellido?: string;
  telefono: string;
  correo: string;
  queHaceEmpresa?: string;
  comoPodemosAyudar?: string;
  timestamp: string;
}

export default function VerContactos() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [localStorageContacts, setLocalStorageContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadContacts = () => {
    setLoading(true);
    
    // Cargar del servidor
    fetch('/api/contact')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setContacts(data.data || []);
        } else {
          setError(data.message || 'Error al cargar contactos');
        }
        setLoading(false);
      })
      .catch(err => {
        setError('Error al conectar con el servidor');
        setLoading(false);
      });

    // Cargar de localStorage
    try {
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem('contacts');
        if (stored) {
          setLocalStorageContacts(JSON.parse(stored));
        } else {
          setLocalStorageContacts([]);
        }
      }
    } catch (e) {
      console.error('Error leyendo localStorage:', e);
      setLocalStorageContacts([]);
    }
  };

  useEffect(() => {
    loadContacts();
  }, []);

  const totalServer = contacts.length;
  const totalLocal = localStorageContacts.length;
  const total = totalServer + totalLocal;

  return (
    <>
      <Head>
        <title>Ver Contactos - SuperBincent</title>
      </Head>
      <div className="min-h-screen bg-gray-50 p-4 md:p-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">📋 Contactos Recibidos</h1>
            <Link 
              href="/app" 
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Volver al Dashboard
            </Link>
          </div>

          {/* Botón de actualizar */}
          <div className="mb-6">
            <button
              onClick={loadContacts}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              🔄 Actualizar Lista
            </button>
          </div>

          {/* Resumen */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-700 mb-2">Total</h2>
              <p className="text-4xl font-bold text-purple-600">{total}</p>
              <p className="text-sm text-gray-500 mt-2">Contactos recibidos</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-700 mb-2">Servidor</h2>
              <p className="text-4xl font-bold text-blue-600">{totalServer}</p>
              <p className="text-sm text-gray-500 mt-2">Guardados en servidor</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-700 mb-2">Navegador</h2>
              <p className="text-4xl font-bold text-green-600">{totalLocal}</p>
              <p className="text-sm text-gray-500 mt-2">En localStorage</p>
            </div>
          </div>

          {loading && (
            <div className="text-center py-8">
              <p className="text-gray-600">Cargando contactos...</p>
            </div>
          )}

          {error && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <p className="text-yellow-800">⚠️ {error}</p>
            </div>
          )}

          {/* Si no hay contactos */}
          {!loading && total === 0 && (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-xl text-gray-600 mb-4">📭 No hay contactos registrados aún</p>
              <p className="text-gray-500">
                Cuando alguien complete el formulario "Contáctame", aparecerá aquí.
              </p>
            </div>
          )}

          {/* Contactos del servidor */}
          {totalServer > 0 && (
            <div className="bg-white rounded-lg shadow mb-8">
              <div className="p-6 border-b bg-blue-50">
                <h2 className="text-xl font-semibold text-blue-900">
                  💾 Contactos del Servidor ({totalServer})
                </h2>
                <p className="text-sm text-blue-700 mt-1">
                  Estos contactos están guardados permanentemente en el servidor
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre Completo</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Teléfono</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Correo</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Empresa</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {contacts.map((contact, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{idx + 1}</td>
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">
                          <div>{contact.nombre} {contact.apellido || ''}</div>
                          {contact.comoPodemosAyudar && (
                            <div className="text-xs text-gray-500 mt-1 max-w-xs truncate" title={contact.comoPodemosAyudar}>
                              {contact.comoPodemosAyudar}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {contact.telefono}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <a href={`mailto:${contact.correo}`} className="text-blue-600 hover:underline">
                            {contact.correo}
                          </a>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500 max-w-xs">
                          {contact.queHaceEmpresa || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(contact.timestamp).toLocaleString('es-CO', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Contactos de localStorage */}
          {totalLocal > 0 && (
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b bg-green-50">
                <h2 className="text-xl font-semibold text-green-900">
                  🌐 Contactos en tu Navegador ({totalLocal})
                </h2>
                <p className="text-sm text-green-700 mt-1">
                  Estos contactos están guardados localmente en tu navegador (localStorage)
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre Completo</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Teléfono</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Correo</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Empresa</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {localStorageContacts.map((contact, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{idx + 1}</td>
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">
                          <div>{contact.nombre} {contact.apellido || ''}</div>
                          {contact.comoPodemosAyudar && (
                            <div className="text-xs text-gray-500 mt-1 max-w-xs truncate" title={contact.comoPodemosAyudar}>
                              {contact.comoPodemosAyudar}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {contact.telefono}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <a href={`mailto:${contact.correo}`} className="text-blue-600 hover:underline">
                            {contact.correo}
                          </a>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500 max-w-xs">
                          {contact.queHaceEmpresa || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(contact.timestamp).toLocaleString('es-CO', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

