import type { NextApiRequest, NextApiResponse } from 'next';

// Esta es una implementación temporal para ver los contactos
// En producción, esto debería venir de una base de datos
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    // TODO: Reemplazar con consulta a base de datos
    // Por ahora, retornamos un mensaje indicando dónde se almacenan
    
    const storageInfo = {
      message: 'Los datos del formulario "Contáctame" se almacenan en:',
      locations: [
        {
          type: 'Backend API',
          endpoint: '/api/contact',
          description: 'Los datos se envían al endpoint /api/contact que actualmente solo los registra en los logs del servidor',
          status: 'Implementado (solo logging)'
        },
        {
          type: 'LocalStorage (Fallback)',
          description: 'Si el backend falla, los datos se guardan en localStorage del navegador',
          key: 'contacts',
          status: 'Implementado como fallback',
          note: 'Para ver los datos en localStorage, abre la consola del navegador y ejecuta: JSON.parse(localStorage.getItem("contacts"))'
        }
      ],
      nextSteps: [
        'Implementar guardado en base de datos (PostgreSQL, MongoDB, etc.)',
        'Configurar envío de emails de notificación',
        'Integrar con CRM (HubSpot, Salesforce, etc.)',
        'Añadir validación y sanitización de datos'
      ]
    };

    return res.status(200).json(storageInfo);
  } catch (error: any) {
    console.error('Error:', error);
    return res.status(500).json({ 
      success: false,
      message: 'Error al obtener información' 
    });
  }
}

