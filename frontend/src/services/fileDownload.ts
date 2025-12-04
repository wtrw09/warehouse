/**
 * 通用文件下载服务
 * 提供统一的文件下载接口，支持不同实体类型的错误文件下载
 */

import { downloadErrorFile } from './errorHandling';

/**
 * 下载错误文件
 * @param fileName 文件名或文件路径
 * @param downloadFileName 下载时显示的文件名
 * @param entityType 实体类型（如：supplier、customer、bin等）
 * @returns Promise<void>
 */
export const downloadEntityErrorFile = async (
  fileName: string,
  downloadFileName: string,
  entityType: string
): Promise<void> => {
  return downloadErrorFile(fileName, downloadFileName, entityType);
};

/**
 * 供应商错误文件下载
 * @param fileName 文件名
 * @param downloadFileName 下载时显示的文件名
 * @returns Promise<void>
 */
export const downloadSupplierErrorFile = async (
  fileName: string,
  downloadFileName: string = '供应商导入错误数据.xls'
): Promise<void> => {
  return downloadErrorFile(fileName, downloadFileName, 'supplier');
};

/**
 * 客户错误文件下载
 * @param fileName 文件名
 * @param downloadFileName 下载时显示的文件名
 * @returns Promise<void>
 */
export const downloadCustomerErrorFile = async (
  fileName: string,
  downloadFileName: string = '客户导入错误数据.xls'
): Promise<void> => {
  return downloadErrorFile(fileName, downloadFileName, 'customer');
};

/**
 * 货位错误文件下载
 * @param fileName 文件名
 * @param downloadFileName 下载时显示的文件名
 * @returns Promise<void>
 */
export const downloadBinErrorFile = async (
  fileName: string,
  downloadFileName: string = '货位导入错误数据.xls'
): Promise<void> => {
  return downloadErrorFile(fileName, downloadFileName, 'bin');
};

/**
 * 通用文件下载工具
 * @param url 完整的下载URL
 * @param downloadFileName 下载时显示的文件名
 * @returns Promise<void>
 */
export const downloadFileByUrl = async (
  url: string,
  downloadFileName: string
): Promise<void> => {
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      }
    });

    if (!response.ok) {
      throw new Error(`下载失败: ${response.status} ${response.statusText}`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = downloadFileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error('文件下载失败:', error);
    throw error;
  }
};

export default {
  downloadEntityErrorFile,
  downloadSupplierErrorFile,
  downloadCustomerErrorFile,
  downloadBinErrorFile,
  downloadFileByUrl
};