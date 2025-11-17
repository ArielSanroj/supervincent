import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Redirigir automáticamente a la app
    router.push('/app');
  }, [router]);

  return null;
}
