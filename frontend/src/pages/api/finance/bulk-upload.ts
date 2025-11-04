import type { NextApiRequest, NextApiResponse } from 'next'
import axios from 'axios'

const BACKEND_API = process.env.BACKEND_API_URL || 'http://localhost:8010'

export const config = {
  api: {
    bodyParser: false,
  },
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    // Proxy the multipart form-data stream to backend
    const backendUrl = `${BACKEND_API}/process/upload-multiple`

    const response = await axios.post(backendUrl, req, {
      headers: {
        ...req.headers,
      },
      maxBodyLength: Infinity,
      maxContentLength: Infinity,
    })

    return res.status(response.status).json(response.data)
  } catch (e: any) {
    const msg = e?.response?.data || e?.message || 'Bulk upload failed'
    return res.status(500).json({ status: 'error', error: msg })
  }
}


