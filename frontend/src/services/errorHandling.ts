// 错误数据处理与Excel生成的前端服务示例
// 位置：frontend/src/services/errorHandling.ts

import { ElMessage, ElMessageBox } from 'element-plus'
import type { ImportConfig } from './types/import'
import { getServerBaseURL } from './base'

// 临时类型定义，应该添加到 types/import.ts 中
interface ValidationError {
  row_index?: number
  row?: number
  field: string
  error_message?: string
  message?: string
  raw_data?: any
}

interface ImportResult {
  success_count: number
  error_count: number
  total_count?: number
  has_error_file?: boolean
  error_file_name?: string
  message: string
}

/**
 * 处理导入结果，包括错误文件下载
 */
export const handleImportResult = async (
  result: ImportResult,
  config: ImportConfig
): Promise<void> => {
  const { success_count, error_count, has_error_file, error_file_name, message } = result

  if (error_count === 0) {
    // 全部成功
    ElMessage.success(`${message}，所有${config.entityName}数据导入成功！`)
  } else {
    // 部分成功或全部失败
    const title = success_count > 0 ? '部分数据导入成功' : '数据导入失败'
    const content = `
      <div>
        <p>${message}</p>
        ${success_count > 0 ? `<p style="color: #67C23A;">✓ 成功导入 ${success_count} 条数据</p>` : ''}
        <p style="color: #F56C6C;">✗ ${error_count} 条数据需要修改</p>
        ${has_error_file ? '<p>您可以下载错误数据文件进行修改后重新导入。</p>' : ''}
      </div>
    `

    if (has_error_file && error_file_name) {
      // 显示确认对话框，询问是否下载错误文件
      ElMessageBox.confirm(content, title, {
        confirmButtonText: '下载错误文件',
        cancelButtonText: '知道了',
        type: 'warning',
        dangerouslyUseHTMLString: true,
        showClose: true
      })
        .then(() => {
          downloadErrorFile(error_file_name, `${config.entityName}导入错误数据.xls`)
        })
        .catch(() => {
          // 用户点击取消，不做任何操作
        })
    } else {
      ElMessage.warning({
        message: content,
        dangerouslyUseHTMLString: true,
        duration: 8000,
        showClose: true
      })
    }
  }
}

/**
 * 获取当前用户的JWT token
 */
const getAuthToken = (): string | null => {
  // 从localStorage获取token
  return localStorage.getItem('token') || sessionStorage.getItem('token')
}

/**
 * 下载错误文件
 */
export const downloadErrorFile = async (
  fileName: string,
  filename: string = '导入错误数据.xls',
  entityType: string = 'supplier'
): Promise<void> => {
  try {
    const token = getAuthToken()
    
    console.log('开始下载错误文件:', {
      fileName: fileName,
      filename: filename,
      hasToken: !!token,
      timestamp: new Date().toISOString()
    })
    
    if (!token) {
      throw new Error('用户未登录，请重新登录后重试')
    }
    
    // 改进的文件名提取逻辑
    let pureFileName = fileName
    
    // 情况1：如果是完整的URL（包含查询参数file_name=）
    if (fileName.includes('file_name=')) {
      const match = fileName.match(/file_name=([^&]+)/)
      if (match && match[1]) {
        pureFileName = decodeURIComponent(match[1])
      }
    }
    // 情况2：如果是相对路径URL（如 "/suppliers/download-error-file?file_path=xxx"）
    else if (fileName.includes('file_path=')) {
      const match = fileName.match(/file_path=([^&]+)/)
      if (match && match[1]) {
        const filePath = decodeURIComponent(match[1])
        pureFileName = filePath.split('/').pop() || filePath
      }
    }
    // 情况3：如果只是路径（包含/符号）
    else if (fileName.includes('/')) {
      pureFileName = fileName.split('/').pop() || fileName
    }
    // 情况4：已经是纯文件名，直接使用
    
    console.log('文件名提取结果:', {
      originalFileName: fileName,
      extractedFileName: pureFileName
    })
    
    // 构造完整的下载 URL - 使用 file_name 参数
    const baseURL = getServerBaseURL()
    const downloadUrl = `${baseURL}/${entityType}s/download-error-file?file_name=${encodeURIComponent(pureFileName)}`
    
    console.log('使用简化的 GET 请求下载文件:', {
      originalFileName: fileName,
      extractedFileName: pureFileName,
      downloadUrl: downloadUrl
    })
    
    // 使用简单的 fetch GET 请求
    const response = await fetch(downloadUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    console.log('服务器响应状态:', {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok,
      contentType: response.headers.get('content-type'),
      contentLength: response.headers.get('content-length')
    })
    
    if (!response.ok) {
      // 记录详细的错误信息
      let errorDetail = ''
      try {
        const errorText = await response.text()
        errorDetail = errorText ? ` - 详细信息: ${errorText}` : ''
      } catch (e) {
        // 忽略解析错误响应的错误
      }
      
      if (response.status === 401) {
        throw new Error('认证失败，请重新登录')
      } else if (response.status === 403) {
        throw new Error('权限不足，无法下载错误文件。请联系管理员获取相应权限。')
      } else if (response.status === 404) {
        throw new Error(`错误文件不存在或已过期${errorDetail}`)
      } else if (response.status === 500) {
        throw new Error(`服务器内部错误，无法读取错误文件${errorDetail}`)
      }
      throw new Error(`下载失败: ${response.status} ${response.statusText}${errorDetail}`)
    }

    // 获取文件数据流
    const blobData = await response.blob()
    
    // 强制设置正确的blob类型为Excel文件
    const blob = new Blob([blobData], { type: 'application/vnd.ms-excel' })
    
    console.log('文件数据流信息:', {
      blobSize: blob.size,
      blobType: blob.type,
      hasData: blob.size > 0
    })
    
    if (blob.size === 0) {
      throw new Error('下载的文件为空，可能是服务器错误')
    }
    
    // 创建下载链接并触发下载
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.style.display = 'none'
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 清理内存
    window.URL.revokeObjectURL(url)
    
    console.log('文件下载完成:', {
      success: true,
      filename: filename,
      fileSize: blob.size
    })
    
    ElMessage.success(`错误文件下载成功 (${(blob.size / 1024).toFixed(1)}KB)`)
    
  } catch (error: any) {
    console.error('下载错误文件失败:', {
      error: error,
      message: error.message,
      fileName: fileName,
      filename: filename,
      timestamp: new Date().toISOString()
    })
    
    // 直接显示错误信息给用户
    ElMessage.error(`下载失败: ${error.message || '网络错误'}`)
  }
}

/**
 * 批量导入数据并处理错误
 */
export const batchImportWithErrorHandling = async (
  data: any[],
  config: ImportConfig
): Promise<ImportResult> => {
  try {
    const apiResult = await config.batchImportAPI(data)
    
    // 转换为BatchImportResult的结果为ImportResult格式
    const result: ImportResult = {
      success_count: apiResult.success_count || 0,
      error_count: apiResult.error_count || 0,
      total_count: data.length,
      has_error_file: apiResult.has_error_file || false,
      error_file_name: apiResult.error_file_name,
      message: `处理完成，成功${apiResult.success_count || 0}条，失败${apiResult.error_count || 0}条`
    }
    
    // 处理导入结果
    await handleImportResult(result, config)
    
    return result
    
  } catch (error: any) {
    console.error('批量导入失败:', error)
    
    const errorMessage = error.response?.data?.detail || error.message || '导入失败'
    ElMessage.error(`${config.entityName}导入失败: ${errorMessage}`)
    
    throw error
  }
}

/**
 * 验证数据并提供编辑选择
 */
export const validateAndOfferEditOptions = async (
  data: any[],
  validationErrors: ValidationError[],
  _config: ImportConfig
): Promise<'inline' | 'download' | 'force' | 'cancel'> => {
  if (validationErrors.length === 0) {
    return 'inline' // 无错误，直接导入
  }

  const errorCount = validationErrors.length
  const forceDownload = data.length > 20 || errorCount > 5

  let message = `发现 ${errorCount} 条数据需要修改`
  
  if (forceDownload) {
    message += '，数据量较大，建议下载Excel文件进行批量编辑'
    
    return ElMessageBox.confirm(
      `${message}，请选择处理方式：`,
      '数据验证结果',
      {
        confirmButtonText: '下载错误文件',
        cancelButtonText: '仍然导入数据',
        type: 'warning'
      }
    ).then((): 'download' => 'download').catch((): 'force' => 'force')
  } else {
    return ElMessageBox.confirm(
      `${message}，请选择处理方式：`,
      '数据验证结果',
      {
        confirmButtonText: '在线编辑',
        cancelButtonText: '下载文件编辑',
        type: 'warning'
      }
    ).then((): 'inline' => 'inline').catch((): 'download' => 'download')
  }
}