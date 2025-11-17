// Script para ver contactos desde la consola del navegador
// Copia y pega esto en la consola (F12)

(function() {
  console.log('📋 === CONTACTOS GUARDADOS ===\n');
  
  try {
    const contacts = JSON.parse(localStorage.getItem('contacts') || '[]');
    
    if (contacts.length === 0) {
      console.log('❌ No hay contactos guardados en localStorage');
      return;
    }
    
    console.log(`✅ Total de contactos: ${contacts.length}\n`);
    
    contacts.forEach((contact, index) => {
      console.log(`📝 Contacto #${index + 1}:`);
      console.log(`   Nombre: ${contact.nombre}`);
      console.log(`   Teléfono: ${contact.telefono}`);
      console.log(`   Correo: ${contact.correo}`);
      console.log(`   Fecha: ${new Date(contact.timestamp).toLocaleString('es-CO')}`);
      console.log('');
    });
    
    // Opción para copiar como JSON
    console.log('💡 Para copiar como JSON, ejecuta:');
    console.log('   JSON.stringify(JSON.parse(localStorage.getItem("contacts")), null, 2)');
    
  } catch (error) {
    console.error('❌ Error al leer contactos:', error);
  }
})();

