import Head from 'next/head';
import Link from 'next/link';

export default function Custom404() {
  return (
    <>
      <Head>
        <title>404 - Página no encontrada | SuperBincent</title>
        <meta name="robots" content="noindex, nofollow" />
      </Head>
      <main className="min-h-screen bg-white flex items-center justify-center px-6">
        <div className="text-center">
          <h1 className="font-display text-6xl font-bold mb-4" style={{ color: '#6A1B9A' }}>
            404
          </h1>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Página no encontrada
          </h2>
          <p className="text-gray-600 mb-8">
            Lo sentimos, la página que buscas no existe.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/"
              className="px-6 py-3 rounded-lg text-white font-semibold shadow-md"
              style={{ backgroundColor: '#6A1B9A' }}
            >
              Ir al inicio
            </Link>
            <Link
              href="/landing"
              className="px-6 py-3 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50"
            >
              Ver landing
            </Link>
          </div>
        </div>
      </main>
    </>
  );
}


