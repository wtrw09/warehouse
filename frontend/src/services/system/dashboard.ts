/**
 * 主页仪表板API服务
 */
import api from '../base';

/**
 * 核心统计数据类型
 */
export interface DashboardStatistics {
  today_inbound: {
    order_count: number;
    material_count: number;
    change_percent: number;
  };
  today_outbound: {
    order_count: number;
    material_count: number;
    change_percent: number;
  };
  total_inventory: {
    quantity: number;
    material_types: number;
    total_value: number;
  };
  warning_count: {
    total: number;
    out_of_stock: number;
    low_stock: number;
  };
}

/**
 * 月度趋势数据类型
 */
export interface MonthlyTrendData {
  daily_data: Array<{
    date: string;
    inbound: number;
    outbound: number;
  }>;
  total_inbound: number;
  total_outbound: number;
  query_year: number;
  query_month: number;
  is_current_month: boolean;
}

/**
 * 最近交易记录类型
 */
export interface RecentTransaction {
  transaction_id: number;
  transaction_time: string;
  change_type: string;
  material_code: string;
  material_name: string;
  material_specification: string;
  quantity_change: number;
  reference_number: string;
  creator: string;
}

/**
 * 库存预警数据类型
 */
export interface InventoryWarningItem {
  material_id: number;
  material_code: string;
  material_name: string;
  material_specification: string;
  current_stock: number;
  safety_stock: number;
  shortage: number;
  major_name: string;
  equipment_name: string;
}

export interface InventoryWarnings {
  out_of_stock: InventoryWarningItem[];
  low_stock: InventoryWarningItem[];
  summary: {
    out_of_stock_count: number;
    low_stock_count: number;
    total_warning_count: number;
  };
}

/**
 * 仪表板API服务
 */
export const dashboardAPI = {
  /**
   * 获取核心统计数据
   */
  getStatistics: async (): Promise<DashboardStatistics> => {
    const response = await api.get('/api/dashboard/statistics');
    return response.data;
  },

  /**
   * 获取指定月份的出入库趋势
   * @param year 年份，不传则为当前年份
   * @param month 月份（1-12），不传则为当前月份
   */
  getMonthlyTrend: async (year?: number, month?: number): Promise<MonthlyTrendData> => {
    const response = await api.get('/api/dashboard/monthly-trend', {
      params: { year, month }
    });
    return response.data;
  },

  /**
   * 获取最近的出入库记录
   * @param limit 返回记录数量，默认10条
   */
  getRecentTransactions: async (limit: number = 10): Promise<{ transactions: RecentTransaction[] }> => {
    const response = await api.get('/api/dashboard/recent-transactions', {
      params: { limit }
    });
    return response.data;
  },

  /**
   * 获取库存预警信息
   */
  getInventoryWarnings: async (): Promise<InventoryWarnings> => {
    const response = await api.get('/api/dashboard/inventory-warnings');
    return response.data;
  }
};
