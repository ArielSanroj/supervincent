/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Variables de entorno públicas (accesibles en el cliente)
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010',
  },
  // Deshabilitar rewrites en producción ya que usamos API routes
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/:path*',
  //       destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010'}/:path*`,
  //     },
  //   ];
  // },
  // Configuración para producción
  output: 'standalone',
  poweredByHeader: false,
};

module.exports = nextConfig;
