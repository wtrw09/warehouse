import { defineConfig, type UserConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev.config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  build: {
    // 增加chunk大小警告限制
    chunkSizeWarningLimit: 1000,
    // 生产模式优化配置
    minify: 'terser',
    terserOptions: {
      compress: {
        // 移除console、debugger等调试信息
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.warn', 'console.error', 'console.debug']
      }
    },
    // 生成source map用于生产环境调试（可选，建议关闭）
    sourcemap: false
  },
  // 确保静态资源路径正确
  base: './'
}) as UserConfig
