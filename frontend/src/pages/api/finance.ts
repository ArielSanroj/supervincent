import { NextApiRequest, NextApiResponse } from 'next';
import { FinanceDashboard } from '../../types/finance';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  // Mock finance dashboard data
  const mockData: FinanceDashboard = {
    indicators: {
      debtRatio: 22,
      liquidity: 1.2,
      lastMonthSales: 123333087333.04,
      lastMonthProfit: 123333087333.04,
      inventoryTurnoverDays: 23,
      availableCash: 123333087333.04
    },
    budget: [
      { label: "Proveedores", amount: 345600678.07 },
      { label: "Personal", amount: 345600678.07 },
      { label: "Mercadeo", amount: 345600678.07 },
      { label: "Transporte", amount: 345600678.07 },
      { label: "Deudas", amount: 345600678.07 },
      { label: "Servicios Públicos", amount: 345600678.07 },
      { label: "Seguros", amount: 345600678.07 },
      { label: "Beti", amount: 345600678.07 }
    ],
    breakEven: {
      percent: 75,
      tooltipLoss: "Pérdida",
      tooltipProfit: "Ganancia"
    }
  };

  // Simulate API delay
  setTimeout(() => {
    res.status(200).json(mockData);
  }, 500);
}
