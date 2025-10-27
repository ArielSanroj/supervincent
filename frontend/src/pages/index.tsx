import React from 'react';
import Head from 'next/head';
import FinanceDashboard from '../components/FinanceDashboard';

const Home: React.FC = () => {
  return (
    <>
      <Head>
        <title>SuperVincent Finance Dashboard</title>
        <meta name="description" content="Dashboard financiero inteligente con SuperVincent InvoiceBot" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <main>
        <FinanceDashboard />
      </main>
    </>
  );
};

export default Home;
