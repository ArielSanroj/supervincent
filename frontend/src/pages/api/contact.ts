import type { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

interface ContactData {
  nombre: string;
  apellido: string;
  telefono: string;
  correo: string;
  queHaceEmpresa: string;
  comoPodemosAyudar: string;
}

// Archivo donde se guardan los contactos (temporal)
// NOTA: En Vercel, el sistema de archivos es read-only excepto /tmp
// /tmp se limpia entre invocaciones, así que esto es solo temporal
// En producción real, usar una base de datos (PostgreSQL, MongoDB, etc.)
const getContactsFile = () => {
  const isVercel = process.env.VERCEL === '1';
  
  if (isVercel) {
    // En Vercel, usar /tmp (se limpia entre invocaciones)
    // Para producción, considerar usar Vercel KV, Upstash, o una DB
    return '/tmp/contacts.json';
  }
  
  // En desarrollo local
  const dataDir = path.join(process.cwd(), 'data');
  return path.join(dataDir, 'contacts.json');
};

const CONTACTS_FILE = getContactsFile();

// Asegurar que el directorio existe
const ensureDataDir = () => {
  const dataDir = path.dirname(CONTACTS_FILE);
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  if (!fs.existsSync(CONTACTS_FILE)) {
    fs.writeFileSync(CONTACTS_FILE, JSON.stringify([], null, 2));
  }
};

// Leer contactos del archivo
const readContacts = (): ContactData[] => {
  try {
    ensureDataDir();
    const data = fs.readFileSync(CONTACTS_FILE, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    return [];
  }
};

// Guardar contacto en archivo
const saveContact = (contact: ContactData & { timestamp: string }) => {
  try {
    ensureDataDir();
    const contacts = readContacts();
    contacts.push(contact);
    fs.writeFileSync(CONTACTS_FILE, JSON.stringify(contacts, null, 2), 'utf-8');
    console.log('✅ Contacto guardado en:', CONTACTS_FILE);
    console.log('📋 Total de contactos:', contacts.length);
    return true;
  } catch (error) {
    console.error('❌ Error guardando contacto:', error);
    console.error('📁 Ruta intentada:', CONTACTS_FILE);
    return false;
  }
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // GET: Obtener lista de contactos
  if (req.method === 'GET') {
    try {
      const contacts = readContacts();
      return res.status(200).json({ 
        success: true, 
        count: contacts.length,
        data: contacts 
      });
    } catch (error: any) {
      return res.status(500).json({ 
        success: false,
        message: 'Error al leer contactos' 
      });
    }
  }

  // POST: Guardar nuevo contacto
  if (req.method === 'POST') {
    try {
      const { nombre, apellido, telefono, correo, queHaceEmpresa, comoPodemosAyudar }: ContactData = req.body;

      // Validar datos
      if (!nombre || !apellido || !telefono || !correo || !queHaceEmpresa || !comoPodemosAyudar) {
        return res.status(400).json({ message: 'Todos los campos son requeridos' });
      }

      const contact = {
        nombre,
        apellido,
        telefono,
        correo,
        queHaceEmpresa,
        comoPodemosAyudar,
        timestamp: new Date().toISOString()
      };

      // Guardar en archivo
      const saved = saveContact(contact);
      
      if (saved) {
        // También loguear en consola
        console.log('✅ Nuevo contacto guardado:', contact);
        
        return res.status(200).json({ 
          success: true, 
          message: 'Contacto recibido correctamente',
          data: contact
        });
      } else {
        throw new Error('Error al guardar contacto');
      }
    } catch (error: any) {
      console.error('Error procesando contacto:', error);
      return res.status(500).json({ 
        success: false,
        message: 'Error al procesar el contacto' 
      });
    }
  }

  return res.status(405).json({ message: 'Method not allowed' });
}

