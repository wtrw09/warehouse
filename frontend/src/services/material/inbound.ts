import api from '../base';
import type {
  InboundOrderCreate,
  InboundOrderDetailResponseType,
  InboundOrderListResponseType,
  InboundOrderPaginationResponseType,
  InboundOrderQueryParams,
  InboundOrderResponseType,
  InboundOrderStatisticsResponseType,
  InboundOrderCreateResponseType,
  InboundOrderUpdateResponseType,
  InboundOrderDateUpdateResponseType,
  InboundOrderItemResponseType,
  OrderNumberUpdate,
  TransferNumberUpdate,
  SupplierUpdate,
  ContractNumberUpdate,
  InboundOrderItemCreate,
  InboundOrderItemUpdate,
  OrderNumberGenerateResponseType,
  SupplierListResponseType,
  InboundOrderUpdate
} from '../types/inbound';

/**
 * 入库单管理API
 */
export const inboundOrderAPI = {
  /**
   * 获取入库单分页列表
   */
  getInboundOrders: async (params: InboundOrderQueryParams): Promise<InboundOrderPaginationResponseType> => {
    const response = await api.get<InboundOrderPaginationResponseType>('/inbound-orders/', { params });
    return response.data;
  },

  /**
   * 获取所有入库单列表（不分页）
   */
  getAllInboundOrders: async (): Promise<InboundOrderListResponseType> => {
    const response = await api.get<InboundOrderListResponseType>('/inbound-orders/all');
    return response.data;
  },

  /**
   * 获取单个入库单详情
   */
  getInboundOrderDetail: async (orderId: number): Promise<InboundOrderDetailResponseType> => {
    const response = await api.get<InboundOrderDetailResponseType>(`/inbound-orders/get/${orderId}`);
    return response.data;
  },

  /**
   * 创建新入库单
   */
  createInboundOrder: async (data: InboundOrderCreate): Promise<InboundOrderCreateResponseType> => {
    const response = await api.post<InboundOrderCreateResponseType>('/inbound-orders/', data);
    return response.data;
  },

  /**
   * 删除入库单
   */
  deleteInboundOrder: async (orderId: number): Promise<void> => {
    await api.delete(`/inbound-orders/delete/${orderId}`);
  },

  /**
   * 获取入库单统计信息
   */
  getInboundOrderStatistics: async (params: {
    start_date?: string;
    end_date?: string;
  }): Promise<InboundOrderStatisticsResponseType> => {
    const response = await api.get<InboundOrderStatisticsResponseType>('/inbound-orders/statistics', { params });
    return response.data;
  },

  /**
   * 修改入库单号
   */
  updateOrderNumber: async (orderId: number, data: OrderNumberUpdate): Promise<InboundOrderUpdateResponseType> => {
    const response = await api.put<InboundOrderUpdateResponseType>(`/inbound-orders/${orderId}/update-order-number`, data);
    return response.data;
  },

  /**
   * 修改调拨单号
   */
  updateTransferNumber: async (orderId: number, data: TransferNumberUpdate): Promise<InboundOrderUpdateResponseType> => {
    const response = await api.put<InboundOrderUpdateResponseType>(`/inbound-orders/${orderId}/update-transfer-number`, data);
    return response.data;
  },

  /**
   * 修改入库单供应商
   */
  updateSupplier: async (orderId: number, data: SupplierUpdate): Promise<InboundOrderUpdateResponseType> => {
    const response = await api.put<InboundOrderUpdateResponseType>(`/inbound-orders/${orderId}/update-supplier`, data);
    return response.data;
  },

  /**
   * 修改入库单合同号
   */
  updateContractNumber: async (orderId: number, data: ContractNumberUpdate): Promise<InboundOrderUpdateResponseType> => {
    const response = await api.put<InboundOrderUpdateResponseType>(`/inbound-orders/${orderId}/update-contract-number`, data);
    return response.data;
  },

  /**
   * 修改入库单信息（包括入库日期等）
   */
  updateInboundOrder: async (orderId: number, data: InboundOrderUpdate): Promise<InboundOrderDateUpdateResponseType> => {
    const response = await api.put<InboundOrderDateUpdateResponseType>(`/inbound-orders/${orderId}/update-inbound-date`, data);
    return response.data;
  },

  /**
   * 新增入库单明细中一条器材信息
   */
  addInboundOrderItem: async (orderId: number, data: InboundOrderItemCreate): Promise<InboundOrderItemResponseType> => {
    const response = await api.post<InboundOrderItemResponseType>(`/inbound-orders/${orderId}/items`, data);
    return response.data;
  },

  /**
   * 修改入库明细中某一条目的器材信息
   */
  updateInboundOrderItem: async (orderId: number, itemId: number, data: InboundOrderItemUpdate): Promise<InboundOrderResponseType> => {
    const response = await api.put<InboundOrderResponseType>(`/inbound-orders/${orderId}/items/update/${itemId}`, data);
    return response.data;
  },

  /**
   * 删除入库明细中某一条目的器材信息
   */
  deleteInboundOrderItem: async (orderId: number, itemId: number): Promise<void> => {
    await api.delete(`/inbound-orders/${orderId}/items/delete/${itemId}`);
  },

  /**
   * 批量删除指定入库单的明细项
   */
  batchDeleteInboundOrderItems: async (orderId: number, itemIds: number[]): Promise<void> => {
    await api.delete(`/inbound-orders/${orderId}/items/batch-delete`, { 
      params: { item_ids: itemIds }
    });
  },

  /**
   * 生成入库单号
   */
  generateInboundOrderNumber: async (dateStr: string): Promise<OrderNumberGenerateResponseType> => {
    const response = await api.get<OrderNumberGenerateResponseType>(`/inbound-orders/generate-order-number/${dateStr}`);
    return response.data;
  },

  /**
   * 获取所有入库单中出现的供应商列表（去重）
   */
  getInboundOrderSuppliers: async (): Promise<SupplierListResponseType> => {
    const response = await api.get<SupplierListResponseType>('/inbound-orders/suppliers');
    return response.data;
  },

  /**
    * 打印入库单
    */
   printInboundOrder: async (orderNumber: string): Promise<Blob> => {
     const response = await api.get(`/inbound-orders/pdf/${orderNumber}`, {
       responseType: 'blob'
     });
     return response.data;
   },

   /**
    * 打印器材分类账页
    */
   printMaterialLedger: async (orderNumber: string): Promise<Blob> => {
     const response = await api.get(`/material-ledger/pdf/${orderNumber}`, {
       responseType: 'blob'
     });
     return response.data;
   }
};