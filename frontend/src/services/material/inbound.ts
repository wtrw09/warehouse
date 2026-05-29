import api, { getServerBaseURL } from '../base';
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
  InboundOrderCreateTimeUpdateResponseType,
  InboundOrderItemResponseType,
  OrderNumberUpdate,
  TransferNumberUpdate,
  SupplierUpdate,
  ContractNumberUpdate,
  InboundCreateTimeUpdate,
  InboundOrderItemCreate,
  InboundOrderItemUpdate,
  OrderNumberGenerateResponseType,
  SupplierListResponseType,
} from '../types/inbound';

/**
 * 入库单管理API
 */
export const inboundOrderAPI = {
  /**
   * 获取入库单分页列表
   */
  getInboundOrders: async (params: InboundOrderQueryParams): Promise<InboundOrderPaginationResponseType> => {
    const response = await api.get<InboundOrderPaginationResponseType>('/inbound-orders', { params });
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
    const response = await api.post<InboundOrderCreateResponseType>('/inbound-orders', data);
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
   * 修改入库单创建时间
   */
  updateCreateTime: async (orderId: number, data: InboundCreateTimeUpdate): Promise<InboundOrderCreateTimeUpdateResponseType> => {
    const response = await api.put<InboundOrderCreateTimeUpdateResponseType>(`/inbound-orders/${orderId}/update-create-time`, data);
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
     const response = await api.get(`/inbound-orders/download/${orderNumber}`, {
       responseType: 'blob'
     });
     return response.data;
   },

   /**
    * 打印器材分类账页
    */
   printMaterialLedger: async (orderNumber: string): Promise<Blob> => {
     const response = await api.get(`/material-ledger/download/${orderNumber}`, {
       responseType: 'blob'
     });
     return response.data;
   },

   /**
    * 批量生成器材分类账页（SSE流式推送进度）
    * 替代串行循环调用 printMaterialLedger，避免 10秒 超时
    */
   batchPrintMaterialLedgerStream: async (
     orderNumbers: string[],
     onProgress: (data: { type: string; order_number: string; current: number; total: number; download_url?: string; error?: string; file_elapsed?: number; elapsed_seconds?: number }) => void,
     onComplete: (result: { total: number; success: number; failed: number; total_elapsed?: number }) => void,
     onError: (error: Error) => void
   ) => {
     // 动态超时：每个账页预留30秒，至少60秒
     const timeoutMs = Math.max(60000, orderNumbers.length * 30000);
     const controller = new AbortController();
     const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

     try {
       const baseURL = getServerBaseURL();
       const token = localStorage.getItem('token');

       const response = await fetch(`${baseURL}/material-ledger/batch-progress`, {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
           'Authorization': `Bearer ${token}`
         },
         body: JSON.stringify({ order_numbers: orderNumbers }),
         signal: controller.signal
       });

       clearTimeout(timeoutId);

       if (!response.ok) {
         const errorData = await response.json().catch(() => ({}));
         throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
       }

       const reader = response.body!.getReader();
       const decoder = new TextDecoder();
       let buffer = '';

       while (true) {
         const { done, value } = await reader.read();
         if (done) break;

         buffer += decoder.decode(value, { stream: true });

         // SSE 事件以双换行符分割
         const parts = buffer.split('\n\n');
         buffer = parts.pop() || '';

         for (const part of parts) {
           const lines = part.split('\n');
           let currentEvent = '';
           let dataStr = '';

           for (const line of lines) {
             if (line.startsWith('event: ')) {
               currentEvent = line.substring(7).trim();
             } else if (line.startsWith('data: ')) {
               dataStr = line.substring(6);
             }
           }

           if (!currentEvent || !dataStr) continue;

           try {
             const data = JSON.parse(dataStr);
             if (currentEvent === 'progress') {
               onProgress(data);
             } else if (currentEvent === 'complete') {
               onComplete(data);
             }
             // heartbeat 事件忽略
           } catch (e) {
             console.warn('解析SSE数据失败:', dataStr);
           }
         }
       }
     } catch (error: any) {
       clearTimeout(timeoutId);
       if (error.name === 'AbortError') {
         onError(new Error('连接超时，请重试'));
       } else {
         onError(error);
       }
     }
   },

   /**
    * 生成入库单Excel文件
    */
   generateInboundOrderExcel: async (orderNumber: string): Promise<Blob> => {
     const response = await api.get(`/inbound-orders/excel/${orderNumber}`, {
       responseType: 'blob'
     });
     return response.data;
   }
};