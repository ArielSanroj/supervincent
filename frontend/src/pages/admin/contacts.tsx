import { useState, useEffect } from 'react';
import Head from 'next/head';

interface Contact {
  nombre: string;
  telefono: string;
  correo: string;
  timestamp: string;
}

export default function ContactsAdmin() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [localStorageContacts, setLocalStorageContacts] = useState<Contact[]>([]);

  useEffect(() => {
    // Cargar contactos del servidor
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

    // Cargar contactos de localStorage
    try {
      const stored = localStorage.getItem('contacts');
      if (stored) {
        setLocalStorageContacts(JSON.parse(stored));
      }
    } catch (e) {
      console.error('Error leyendo localStorage:', e);
    }
  }, []);

  const totalContacts = contacts.length;
  const totalLocalStorage = localStorageContacts.length;

  return (
    <>
      <Head>
        <title>Contactos - SuperBincent Admin</title>
      </Head>
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">📋 Contactos Recibidos</h1>

          {/* Resumen */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-700 mb-2">Servidor (API)</h2>
              <p className="text-3xl font-bold text-blue-600">{totalContacts}</p>
              <p className="text-sm text-gray-500 mt-2">Contactos guardados en el servidor</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-700 mb-2">LocalStorage (Navegador)</h2>
              <p className="text-3xl font-bold text-green-600">{totalLocalStorage}</p>
              <p className="text-sm text-gray-500 mt-2">Contactos guardados en el navegador</p>
            </div>
          </div>

          {loading && (
            <div className="text-center py-8">
              <p className="text-gray-600">Cargando contactos...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Contactos del servidor */}
          <div className="bg-white rounded-lg shadow mb-8">
            <div className="p-6 border-b">
              <h2 className="text-xl font-semibold">Contactos del Servidor ({totalContacts})</h2>
            </div>
            {totalContacts === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No hay contactos guardados en el servidor aún.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Teléfono</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Correo</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {contacts.map((contact, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {contact.nombre}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {contact.telefono}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {contact.correo}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(contact.timestamp).toLocaleString('es-CO')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Contactos de localStorage */}
          {totalLocalStorage > 0 && (
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h2 className="text-xl font-semibold">Contactos en LocalStorage ({totalLocalStorage})</h2>
                <p className="text-sm text-gray-500 mt-1">Estos son contactos guardados localmente en tu navegador</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Teléfono</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Correo</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {localStorageContacts.map((contact, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {contact.nombre}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {contact.telefono}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {contact.correo}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(contact.timestamp).toLocaleString('es-CO')}
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

