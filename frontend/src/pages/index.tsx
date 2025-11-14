import { GetServerSideProps } from 'next';

// Redirección del servidor para Vercel
export const getServerSideProps: GetServerSideProps = async () => {
  return {
    redirect: {
      destination: '/landing',
      permanent: false,
    },
  };
};

// Este componente nunca se renderiza debido a la redirección
const Home = () => null;

export default Home;
