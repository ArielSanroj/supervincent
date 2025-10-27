import { apiClient } from './api';
import { FinanceDashboard, ApiResponse } from '../types/finance';

export class FinanceService {
  /**
   * Fetch finance dashboard data
   * @param userId - User identifier
   * @returns Promise<FinanceDashboard>
   */
  async getDashboard(userId: string): Promise<FinanceDashboard> {
    try {
      // For now, we'll use mock data since the SuperVincent API doesn't have finance endpoints yet
      // In production, this would be: return await apiClient.get(`/api/finance/dashboard?userId=${userId}`);
      
      return this.getMockDashboardData();
    } catch (error) {
      console.error('Error fetching finance dashboard:', error);
      throw new Error('Failed to fetch finance dashboard data');
    }
  }

  /**
   * Process invoice and get financial impact
   * @param filePath - Path to invoice file
   * @returns Promise<any>
   */
  async processInvoice(filePath: string): Promise<any> {
    try {
      return await apiClient.post('/process', { file_path: filePath });
    } catch (error) {
      console.error('Error processing invoice:', error);
      throw new Error('Failed to process invoice');
    }
  }

  /**
   * Get cache statistics
   * @returns Promise<any>
   */
  async getCacheStats(): Promise<any> {
    try {
      return await apiClient.get('/cache/stats');
    } catch (error) {
      console.error('Error fetching cache stats:', error);
      throw new Error('Failed to fetch cache statistics');
    }
  }

  /**
   * Mock data for development/testing
   * This simulates the API response structure
   */
  private getMockDashboardData(): FinanceDashboard {
    return {
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
  }
}

export const financeService = new FinanceService();
