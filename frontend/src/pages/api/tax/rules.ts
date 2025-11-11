import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

const BACKEND_API = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const response = await axios.get(`${BACKEND_API}/tax/rules`);
    return res.status(200).json(response.data);
  } catch (error: any) {
    console.error('Error fetching tax rules:', error?.response?.data || error?.message);
    return res.status(500).json({ 
      status: 'error', 
      error: error?.response?.data || error?.message || 'Failed to load tax rules' 
    });
  }
}

