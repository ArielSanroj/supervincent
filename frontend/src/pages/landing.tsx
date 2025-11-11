import Head from 'next/head';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import IndicatorCard from '../components/IndicatorCard';
import BreakEvenSlider from '../components/BreakEvenSlider';
import { DollarSign, TrendingUp, Wallet, BarChart3, PiggyBank, Receipt } from 'lucide-react';

export default function Landing() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [formData, setFormData] = useState({
    nombre: '',
    telefono: '',
    correo: ''
  });

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Aquí iría la lógica de envío del formulario
    console.log('Formulario enviado:', formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <>
      <Head>
        <title>SuperBincent • Optimiza tu flujo de caja</title>
        <meta name="description" content="SuperBincent procesa soportes contables con IA para mostrar caja disponible, impuestos y punto de equilibrio. Compatible con Alegra y DIAN 2025." />
        <meta name="keywords" content="flujo de caja, IA financiera, soportes contables, OCR, DIAN 2025, Alegra, punto de equilibrio, PYMES" />
        <link rel="canonical" href="http://localhost:3001/landing" />
        <meta property="og:title" content="SuperBincent • Optimiza tu flujo de caja con IA" />
        <meta property="og:description" content="Procesa tus soportes contables y ve tus finanzas en segundos: caja, impuestos y PEQ." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="http://localhost:3001/landing" />
        <meta property="og:image" content="/favicon.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="SuperBincent • Optimiza tu flujo de caja con IA" />
        <meta name="twitter:description" content="Analiza facturas y gastos con IA. Caja, impuestos y punto de equilibrio al instante." />
        <link rel="icon" href="/superbincentlogo.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/favicon.ico" />
      </Head>

      {/* Header */}
      <header 
        role="banner" 
        className={`w-full fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled ? 'bg-white shadow-md' : 'bg-white/95 backdrop-blur-sm'
        }`}
      >
        <nav aria-label="Principal" className="container mx-auto px-6 py-4 max-w-[1200px]">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link href="/" aria-label="Ir al inicio" className="flex items-center">
              <img 
                src="/superbincentlogo.svg" 
                alt="SuperBincent" 
                className="h-10 w-auto"
              />
            </Link>

            {/* Menú principal - Desktop */}
            <div className="hidden md:flex items-center gap-8 text-sm">
              <a href="#independientes" className="text-brand-textDark hover:text-primary-500 transition-colors font-medium">
                Independientes
              </a>
              <a href="#empresas" className="text-brand-textDark hover:text-primary-500 transition-colors font-medium">
                Empresas
              </a>
              <a href="#beneficios" className="text-brand-textDark hover:text-primary-500 transition-colors font-medium">
                Beneficios
              </a>
              <a href="#planes" className="text-brand-textDark hover:text-primary-500 transition-colors font-medium">
                Planes
              </a>
              <a href="#sobre-nosotros" className="text-brand-textDark hover:text-primary-500 transition-colors font-medium">
                Sobre nosotros
              </a>
              <a href="#blog" className="text-brand-textDark hover:text-primary-500 transition-colors font-medium">
                Blog
              </a>
            </div>

            {/* Botones - Desktop */}
            <div className="hidden md:flex items-center gap-4">
              <Link 
                href="/register" 
                className="px-5 py-2.5 rounded-lg border-2 border-primary-500 text-primary-500 font-medium hover:bg-brand-lavender transition-all duration-300"
              >
                Regístrate
              </Link>
              <Link 
                href="/" 
                className="px-5 py-2.5 rounded-lg bg-secondary-400 text-white font-medium hover:bg-secondary-500 transition-all duration-300"
              >
                Ingresar
              </Link>
          </div>

            {/* Menú móvil */}
            <button className="md:hidden text-brand-textDark" aria-label="Menú">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </nav>
      </header>

      <main id="contenido" className="min-h-screen bg-white" role="main">
        {/* Hero Principal */}
        <section className="relative overflow-hidden pt-24" style={{ backgroundColor: '#140C20', minHeight: '600px' }}>
          {/* Textura estelar de fondo */}
          <div className="absolute inset-0 opacity-20" style={{
            backgroundImage: `radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)`,
            backgroundSize: '40px 40px'
          }} />
          
          <div className="relative container mx-auto px-6 py-32 max-w-[1200px]">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              {/* Columna izquierda */}
              <div className="text-white space-y-6">
                <h1 className="font-display text-5xl md:text-6xl font-bold leading-tight" style={{ fontSize: '48px', fontWeight: 700 }}>
                  Procesa tus soportes contables y ve tus{' '}
                  <span className="text-secondary-400">finanzas en segundos</span>
                </h1>
                <p className="text-lg text-gray-300 leading-relaxed max-w-xl" style={{ fontSize: '16px', fontWeight: 400 }}>
                  SuperBincent analiza tus facturas y gastos con IA para mostrarte caja disponible, impuestos y punto de equilibrio. 
                  Compatible con Alegra y DIAN 2025.
                </p>
              </div>

              {/* Columna derecha - Formulario */}
              <div className="bg-white rounded-xl p-8 shadow-2xl">
                <h2 className="text-2xl font-bold text-brand-textDark mb-6">Contáctame</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label htmlFor="nombre" className="block text-sm font-medium text-brand-textDark mb-2">
                      Nombre
                    </label>
                    <input
                      type="text"
                      id="nombre"
                      name="nombre"
                      value={formData.nombre}
                      onChange={handleChange}
                      placeholder="Tu nombre completo"
                      className="w-full px-4 py-3 rounded-md border border-brand-borderGray focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-brand-placeholderGray"
                      style={{ fontSize: '16px', padding: '12px', borderRadius: '6px' }}
                      required
                    />
                    </div>
                  <div>
                    <label htmlFor="telefono" className="block text-sm font-medium text-brand-textDark mb-2">
                      Teléfono
                    </label>
                    <input
                      type="tel"
                      id="telefono"
                      name="telefono"
                      value={formData.telefono}
                      onChange={handleChange}
                      placeholder="Tu número de teléfono"
                      className="w-full px-4 py-3 rounded-md border border-brand-borderGray focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-brand-placeholderGray"
                      style={{ fontSize: '16px', padding: '12px', borderRadius: '6px' }}
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="correo" className="block text-sm font-medium text-brand-textDark mb-2">
                      Correo
                    </label>
                    <input
                      type="email"
                      id="correo"
                      name="correo"
                      value={formData.correo}
                      onChange={handleChange}
                      placeholder="tu@correo.com"
                      className="w-full px-4 py-3 rounded-md border border-brand-borderGray focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-brand-placeholderGray"
                      style={{ fontSize: '16px', padding: '12px', borderRadius: '6px' }}
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full py-3 rounded-lg bg-secondary-400 text-white font-medium hover:bg-secondary-500 transition-all duration-300 transform hover:scale-105"
                    style={{ fontSize: '16px', fontWeight: 500, borderRadius: '8px' }}
                  >
                    Contáctame
                  </button>
                </form>
              </div>
            </div>
          </div>
        </section>

        {/* Beneficios - "Con Beti tienes..." */}
        <section id="beneficios" className="py-32" style={{ backgroundColor: '#1A1028' }}>
          <div className="container mx-auto px-6 max-w-[1200px]">
            <h2 className="text-center text-white font-display mb-16" style={{ fontSize: '32px', fontWeight: 600 }}>
              Con SuperBincent tienes...
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
              {[
                { number: '1', title: 'Indicadores en tiempo real', desc: 'Ventas, utilidad y caja disponible siempre actualizados.' },
                { number: '2', title: 'Impuestos automáticos', desc: 'IVA, reteICA y reteRenta calculados automáticamente.' },
                { number: '3', title: 'Punto de equilibrio', desc: 'Análisis visual de ingresos vs egresos.' },
                { number: '4', title: 'Detección inteligente', desc: 'Duplicados, errores y omisiones detectados por IA.' },
              ].map((benefit, idx) => (
                <div key={idx} className="text-center">
                  <div className="w-16 h-16 rounded-full bg-primary-500 text-white flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                    {benefit.number}
            </div>
                  <h3 className="text-white font-semibold mb-3" style={{ fontSize: '20px', fontWeight: 600 }}>
                    {benefit.title}
                  </h3>
                  <p className="text-gray-300" style={{ fontSize: '16px', fontWeight: 400 }}>
                    {benefit.desc}
                  </p>
            </div>
              ))}
            </div>
          </div>
        </section>

        {/* Funcionalidades - "Finanzas / Legal / Back Office" */}
        <section className="py-32 bg-white">
          <div className="container mx-auto px-6 max-w-[1200px]">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              {/* Columna izquierda - Dashboard real */}
              <div className="order-2 lg:order-1">
                <div className="rounded-2xl bg-gray-50 p-6 shadow-xl">
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <IndicatorCard
                      title="Ventas mes"
                      value={12500000}
                      icon={<DollarSign className="w-5 h-5" />}
                      format="currency"
                      trend="up"
                    />
                    <IndicatorCard
                      title="Caja disponible"
                      value={8500000}
                      icon={<Wallet className="w-5 h-5" />}
                      format="currency"
                      trend="neutral"
                    />
                  </div>
                  <BreakEvenSlider
                    percent={75}
                    tooltipLoss="Pérdida"
                    tooltipProfit="Ganancia"
                  />
                </div>
              </div>

              {/* Columna derecha */}
              <div className="order-1 lg:order-2 space-y-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-lg bg-primary-500 flex items-center justify-center">
                    <BarChart3 className="w-6 h-6 text-white" />
                  </div>
                  <h2 className="font-display text-4xl font-bold text-brand-textDark" style={{ fontSize: '32px', fontWeight: 600 }}>
                    Finanzas
                  </h2>
            </div>
                <p className="text-brand-textDark leading-relaxed" style={{ fontSize: '16px', fontWeight: 400 }}>
                  Gestiona tu flujo de caja, visualiza tus ingresos y egresos, y mantén un control total sobre tus finanzas 
                  con nuestro dashboard intuitivo y potente.
                </p>
            </div>
            </div>
          </div>
        </section>

        {/* Servicios - "¿Qué puedes hacer con Beti?" */}
        <section className="py-32 bg-brand-light">
          <div className="container mx-auto px-6 max-w-[1200px]">
            <h2 className="text-center font-display mb-16" style={{ fontSize: '32px', fontWeight: 600, color: '#6C3AA9' }}>
              ¿Qué puedes hacer con SuperBincent?
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              {/* Lista de servicios */}
              <div className="space-y-6">
                {[
                  { icon: '📄', title: 'Facturación', desc: 'Genera y gestiona facturas de manera automática.' },
                  { icon: '📊', title: 'Contabilidad', desc: 'Mantén tus registros contables organizados y actualizados.' },
                  { icon: '🧾', title: 'Impuestos', desc: 'Calcula y gestiona tus obligaciones fiscales automáticamente.' },
                  { icon: '📈', title: 'Reportes', desc: 'Genera reportes financieros detallados en tiempo real.' },
                ].map((service, idx) => (
                  <div key={idx} className="flex items-start gap-4 p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow">
                    <div className="text-3xl">{service.icon}</div>
                    <div>
                      <h3 className="font-semibold text-brand-textDark mb-2" style={{ fontSize: '20px', fontWeight: 600, color: '#6C3AA9' }}>
                        {service.title}
                      </h3>
                      <p className="text-brand-textDark" style={{ fontSize: '16px', fontWeight: 400 }}>
                        {service.desc}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Imagen del calendario */}
              <div className="flex justify-center">
                <div className="rounded-2xl bg-white p-8 shadow-xl w-full max-w-md">
                  <div className="text-center">
                    <div className="text-6xl mb-4">📅</div>
                    <div className="text-gray-600 font-medium">Calendario de vencimientos</div>
                  </div>
            </div>
              </div>
            </div>
          </div>
        </section>

        {/* Testimonio / Propuesta de valor */}
        <section className="py-32 bg-white">
          <div className="container mx-auto px-6 max-w-[1200px]">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              {/* Imagen izquierda */}
              <div className="order-2 lg:order-1">
                <div className="rounded-2xl bg-gradient-to-br from-primary-100 to-secondary-100 p-12 h-96 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-6xl mb-4">👥</div>
                    <div className="text-gray-700 font-medium">Equipo trabajando</div>
                  </div>
                </div>
            </div>

              {/* Texto derecho */}
              <div className="order-1 lg:order-2 space-y-6">
                <h2 className="font-display text-4xl font-bold text-brand-textDark" style={{ fontSize: '32px', fontWeight: 600 }}>
                  ¿Por qué nosotros?
                </h2>
                <p className="text-brand-textDark leading-relaxed" style={{ fontSize: '16px', fontWeight: 400 }}>
                  En SuperBincent entendemos que tu tiempo es valioso. Por eso hemos creado una plataforma que simplifica 
                  la gestión financiera de tu negocio, permitiéndote enfocarte en lo que realmente importa: hacer crecer tu empresa.
                </p>
                <p className="text-brand-textDark leading-relaxed" style={{ fontSize: '16px', fontWeight: 400 }}>
                  Nuestro equipo está comprometido con tu éxito. Trabajamos día a día para ofrecerte las mejores herramientas 
                  financieras, respaldadas por inteligencia artificial de última generación.
                </p>
            </div>
            </div>
          </div>
        </section>

        {/* Call to Action final */}
        <section className="py-32" style={{ backgroundColor: '#1A1028' }}>
          <div className="container mx-auto px-6 max-w-[1200px] text-center">
            <h2 className="font-display text-5xl font-bold text-white mb-8" style={{ fontSize: '48px', fontWeight: 700 }}>
              Con SuperBincent crece tu negocio mientras simplificas tu vida.
            </h2>
            <Link 
              href="/register" 
              className="inline-block px-8 py-4 rounded-lg bg-secondary-400 text-white font-medium hover:bg-secondary-500 transition-all duration-300 transform hover:scale-105"
              style={{ fontSize: '16px', fontWeight: 500 }}
            >
              Regístrate ahora
            </Link>
          </div>
        </section>

        {/* Footer */}
        <footer className="py-16" style={{ backgroundColor: '#1A1028' }}>
          <div className="container mx-auto px-6 max-w-[1200px]">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
              {/* Logo y descripción */}
              <div>
                <Link href="/" className="inline-block mb-4">
                  <img 
                    src="/superbincentlogo.svg" 
                    alt="SuperBincent" 
                    className="h-10 w-auto brightness-0 invert"
                  />
                </Link>
                <p className="text-gray-400 text-sm">
                  Optimiza tu flujo de caja con IA financiera
                </p>
              </div>

              {/* Links útiles */}
              <div>
                <h3 className="text-white font-semibold mb-4">Enlaces</h3>
                <ul className="space-y-2 text-gray-400 text-sm">
                  <li><a href="#" className="hover:text-white transition-colors">Términos y condiciones</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Política de privacidad</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Contacto</a></li>
                </ul>
          </div>

              <div>
                <h3 className="text-white font-semibold mb-4">Producto</h3>
                <ul className="space-y-2 text-gray-400 text-sm">
                  <li><a href="#beneficios" className="hover:text-white transition-colors">Beneficios</a></li>
                  <li><a href="#planes" className="hover:text-white transition-colors">Planes</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Soporte</a></li>
          </ul>
              </div>

              <div>
                <h3 className="text-white font-semibold mb-4">Síguenos</h3>
            <div className="flex gap-4">
                  <a href="#" className="text-white hover:text-secondary-400 transition-colors">
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                    </svg>
                  </a>
                  <a href="#" className="text-white hover:text-secondary-400 transition-colors">
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                    </svg>
                  </a>
                  <a href="#" className="text-white hover:text-secondary-400 transition-colors">
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                  </a>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-700 pt-8 text-center text-gray-400 text-sm">
              <p>© {new Date().getFullYear()} SuperBincent. Todos los derechos reservados.</p>
            </div>
          </div>
        </footer>
      </main>
    </>
  );
}
