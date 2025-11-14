import { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';

const Home: React.FC = () => {
  const router = useRouter();

  useEffect(() => {
    // Redirigir a la landing page
    router.replace('/landing');
  }, [router]);

  return (
    <>
      <Head>
        <title>SuperBincent • Optimiza tu flujo de caja</title>
        <meta name="description" content="SuperBincent procesa soportes contables con IA para mostrar caja disponible, impuestos y punto de equilibrio." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/superbincentlogo.svg" type="image/svg+xml" />
      </Head>
      
      <main style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #1A1F3B 0%, #6C5DD3 100%)'
      }}>
        <div style={{ color: 'white', textAlign: 'center' }}>
          <p>Cargando...</p>
        </div>
      </main>
    </>
  );
};

export default Home;
