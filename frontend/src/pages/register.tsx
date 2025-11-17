import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import ContactModal from '../components/ContactModal';
import Head from 'next/head';

export default function Register() {
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(true);

  // Cuando se cierra el modal, redirigir a la app
  const handleCloseModal = () => {
    setIsModalOpen(false);
    router.push('/app');
  };

  return (
    <>
      <Head>
        <title>Regístrate - SuperBincent</title>
      </Head>
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        {/* El modal se mostrará automáticamente */}
        <ContactModal isOpen={isModalOpen} onClose={handleCloseModal} />
      </div>
    </>
  );
}

