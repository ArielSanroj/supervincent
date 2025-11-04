import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

// Backend API base (FastAPI)
const BACKEND_API = process.env.BACKEND_API_URL || 'http://localhost:8010';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
	if (req.method !== 'GET') {
		return res.status(405).json({ message: 'Method not allowed' });
	}

  try {
    // Only reflect what has been uploaded/processed recently
    const recent = await axios.get(`${BACKEND_API}/processed/recent`);
    const list = (recent.data?.data || []) as Array<any>;

    let reteIcaTotal = 0;
    let reteIvaTotal = 0;
    let reteRentaTotal = 0;

    for (const it of list) {
      if (it?.success && it?.taxes) {
        reteIcaTotal += Number(it.taxes.retefuente_ica || 0);
        reteIvaTotal += Number(it.taxes.retefuente_iva || 0);
        reteRentaTotal += Number(it.taxes.retefuente_renta || 0);
      }
    }

    return res.status(200).json({
      success: true,
      data: {
        reteIcaTotal,
        reteIvaTotal,
        reteRentaTotal,
        invoiceCount: list.length
      }
    });
  } catch (error: any) {
    console.error('Error computing withholdings:', error?.response?.data || error?.message || error);
    return res.status(200).json({ success: true, data: { reteIcaTotal: 0, reteIvaTotal: 0, reteRentaTotal: 0, invoiceCount: 0 } });
  }
}
