import api from '../base';
import type {
  OutboundOrderCreate,
  OutboundOrderDetailResponseType,
  OutboundOrderListResponseType,
  OutboundOrderPaginationResponseType,
  OutboundOrderQueryParams,
  OutboundOrderStatisticsResponseType,
  OutboundOrderCreateResponseType,
  OutboundOrderUpdateResponseType,
  OutboundOrderCreateTimeUpdateResponseType,
  OutboundOrderItemResponseType,
  OrderNumberUpdate,
  TransferNumberUpdate,
  CustomerUpdate,
  CreateTimeUpdate,
  OutboundOrderItemCreate,
  OutboundOrderItemUpdate,
  BatchDeleteResponseType,
  OrderNumberGenerateResponseType,
  CustomerListResponseType
} from '../types/outbound';

/**
 * 出库单管理API
 */
export const outboundOrderAPI = {
  /**
   * 获取出库单分页列表
   */
  getOutboundOrders: async (params: OutboundOrderQueryParams): Promise<OutboundOrderPaginationResponseType> => {
    const response = await api.get<OutboundOrderPaginationResponseType>('/outbound-orders/', { params });
    return response.data;
  },

  /**
   * 获取所有出库单列表（不分页）
   */
  getAllOutboundOrders: async (): Promise<OutboundOrderListResponseType> => {
    const response = await api.get<OutboundOrderListResponseType>('/outbound-orders/all');
    return response.data;
  },

  /**
   * 获取单个出库单详情
   */
  getOutboundOrderDetail: async (orderId: number): Promise<OutboundOrderDetailResponseType> => {
    const response = await api.get<OutboundOrderDetailResponseType>(`/outbound-orders/get/${orderId}`);
    return response.data;
  },

  /**
   * 创建新出库单
   */
  createOutboundOrder: async (data: OutboundOrderCreate): Promise<OutboundOrderCreateResponseType> => {
    const response = await api.post<OutboundOrderCreateResponseType>('/outbound-orders/', data);
    return response.data;
  },

  /**
   * 删除出库单
   */
  deleteOutboundOrder: async (orderId: number): Promise<void> => {
    await api.delete(`/outbound-orders/delete/${orderId}`);
  },

  /**
   * 获取出库单统计信息
   */
  getOutboundOrderStatistics: async (params: {
    start_date?: string;
    end_date?: string;
  }): Promise<OutboundOrderStatisticsResponseType> => {
    const response = await api.get<OutboundOrderStatisticsResponseType>('/outbound-orders/statistics', { params });
    return response.data;
  },

  /**
   * 修改出库单号
   */
  updateOrderNumber: async (orderId: number, data: OrderNumberUpdate): Promise<OutboundOrderUpdateResponseType> => {
    const response = await api.put<OutboundOrderUpdateResponseType>(`/outbound-orders/${orderId}/update-order-number`, data);
    return response.data;
  },

  /**
   * 修改调拨单号
   */
  updateTransferNumber: async (orderId: number, data: TransferNumberUpdate): Promise<OutboundOrderUpdateResponseType> => {
    const response = await api.put<OutboundOrderUpdateResponseType>(`/outbound-orders/${orderId}/update-transfer-number`, data);
    return response.data;
  },

  /**
   * 修改出库单客户
   */
  updateCustomer: async (orderId: number, data: CustomerUpdate): Promise<OutboundOrderUpdateResponseType> => {
    const response = await api.put<OutboundOrderUpdateResponseType>(`/outbound-orders/${orderId}/update-customer`, data);
    return response.data;
  },

  /**
   * 修改出库单创建时间
   */
  updateCreateTime: async (orderId: number, data: CreateTimeUpdate): Promise<OutboundOrderCreateTimeUpdateResponseType> => {
    const response = await api.put<OutboundOrderCreateTimeUpdateResponseType>(`/outbound-orders/update-create-time/${orderId}`, data);
    return response.data;
  },

  /**
   * 新增出库单明细中一条器材信息
   */
  addOutboundOrderItem: async (orderId: number, data: OutboundOrderItemCreate): Promise<OutboundOrderItemResponseType> => {
    const response = await api.post<OutboundOrderItemResponseType>(`/outbound-orders/${orderId}/items`, data);
    return response.data;
  },

  /**
   * 修改出库明细中某一条目的器材信息
   */
  updateOutboundOrderItem: async (orderId: number, itemId: number, data: OutboundOrderItemUpdate): Promise<OutboundOrderItemResponseType> => {
    const response = await api.put<OutboundOrderItemResponseType>(`/outbound-orders/${orderId}/items/update/${itemId}`, data);
    return response.data;
  },

  /**
   * 删除出库明细中某一条目的器材信息
   */
  deleteOutboundOrderItem: async (orderId: number, itemId: number): Promise<void> => {
    await api.delete(`/outbound-orders/${orderId}/items/delete/${itemId}`);
  },

  /**
   * 批量删除指定出库单的明细项
   */
  batchDeleteOutboundOrderItems: async (orderId: number, itemIds: number[]): Promise<BatchDeleteResponseType> => {
    const response = await api.delete<BatchDeleteResponseType>(`/outbound-orders/${orderId}/items/batch-delete`, {
      data: { item_ids: itemIds }
    });
    return response.data;
  },

  /**
   * 生成出库单号
   */
  generateOutboundOrderNumber: async (dateStr: string): Promise<OrderNumberGenerateResponseType> => {
    const response = await api.get<OrderNumberGenerateResponseType>(`/outbound-orders/generate-order-number/${dateStr}`);
    return response.data;
  },

  /**
   * 获取所有出库单中出现的客户列表（去重）
   */
  getOutboundOrderCustomers: async (): Promise<CustomerListResponseType> => {
    const response = await api.get<CustomerListResponseType>('/outbound-orders/customers');
    return response.data;
  },

  /**
   * 生成出库单PDF文件
   */
  generateOutboundOrderPDF: async (orderNumber: string): Promise<Blob> => {
    const response = await api.get(`/outbound-orders/pdf/${orderNumber}`, {
      responseType: 'blob'
    });
    return response.data;
  }
};