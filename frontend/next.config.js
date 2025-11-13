/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Variables de entorno públicas (accesibles en el cliente)
  // En Vercel, estas se configuran en el dashboard
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  // Configuración para producción
  poweredByHeader: false,
  // Optimizaciones para Vercel
  compress: true,
  // No usar output: 'standalone' en Vercel (usa su propio sistema)
};

module.exports = nextConfig;
