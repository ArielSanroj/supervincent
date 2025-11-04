import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

const BACKEND_API = process.env.BACKEND_API_URL || 'http://localhost:8010';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }
  try {
    const resp = await axios.get(`${BACKEND_API}/processed/recent`);
    return res.status(200).json(resp.data);
  } catch (e: any) {
    const msg = e?.response?.data || e?.message || 'Failed to load recent';
    return res.status(500).json({ status: 'error', error: msg });
  }
}


