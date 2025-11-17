import Head from 'next/head';
import FinanceDashboard from '../components/FinanceDashboard';

export default function App() {
  return (
    <>
      <Head>
        <title>SuperBincent • Dashboard</title>
        <meta name="description" content="Dashboard financiero de SuperBincent" />
      </Head>
      <FinanceDashboard />
    </>
  );
}

