/**
 * 性能监控工具
 * 用于监控登录页背景图片的加载性能
 */

export class PerformanceMonitor {
  constructor() {
    this.metrics = {
      imageLoadTimes: {},
      totalLoadTime: 0,
      firstContentfulPaint: 0,
      largestContentfulPaint: 0
    };
    this.startTime = performance.now();
  }

  /**
   * 开始监控图片加载
   * @param {string} imageSrc - 图片路径
   */
  startImageLoad(imageSrc) {
    const loadStart = performance.now();
    this.metrics.imageLoadTimes[imageSrc] = {
      start: loadStart,
      end: null,
      duration: null
    };
    
    return loadStart;
  }

  /**
   * 结束图片加载监控
   * @param {string} imageSrc - 图片路径
   * @param {number} startTime - 开始时间
   */
  endImageLoad(imageSrc, startTime) {
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    if (this.metrics.imageLoadTimes[imageSrc]) {
      this.metrics.imageLoadTimes[imageSrc].end = endTime;
      this.metrics.imageLoadTimes[imageSrc].duration = duration;
    }
    
    console.log(`📊 图片加载性能: ${imageSrc} - ${duration.toFixed(2)}ms`);
    return duration;
  }

  /**
   * 记录关键性能指标
   */
  recordCoreWebVitals() {
    if ('PerformanceObserver' in window) {
      // 监控首次内容绘制 (FCP)
      new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        entries.forEach(entry => {
          if (entry.name === 'first-contentful-paint') {
            this.metrics.firstContentfulPaint = entry.startTime;
            console.log(`🎨 首次内容绘制: ${entry.startTime.toFixed(2)}ms`);
          }
        });
      }).observe({ type: 'paint', buffered: true });

      // 监控最大内容绘制 (LCP)
      new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.metrics.largestContentfulPaint = lastEntry.renderTime || lastEntry.loadTime;
        console.log(`🖼️ 最大内容绘制: ${this.metrics.largestContentfulPaint.toFixed(2)}ms`);
      }).observe({ type: 'largest-contentful-paint', buffered: true });
    }
  }

  /**
   * 计算总体加载时间
   */
  calculateTotalLoadTime() {
    this.metrics.totalLoadTime = performance.now() - this.startTime;
    console.log(`⏱️ 总加载时间: ${this.metrics.totalLoadTime.toFixed(2)}ms`);
    return this.metrics.totalLoadTime;
  }

  /**
   * 生成性能报告
   */
  generateReport() {
    const report = {
      ...this.metrics,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      connection: navigator.connection ? {
        effectiveType: navigator.connection.effectiveType,
        downlink: navigator.connection.downlink,
        rtt: navigator.connection.rtt
      } : null
    };

    console.group('📈 登录页性能报告');
    console.table(report.imageLoadTimes);
    console.log('总加载时间:', report.totalLoadTime.toFixed(2) + 'ms');
    console.log('首次内容绘制:', report.firstContentfulPaint.toFixed(2) + 'ms');
    console.log('最大内容绘制:', report.largestContentfulPaint.toFixed(2) + 'ms');
    console.groupEnd();

    return report;
  }

  /**
   * 比较优化前后的性能
   * @param {Object} beforeMetrics - 优化前的指标
   * @param {Object} afterMetrics - 优化后的指标
   */
  static comparePerformance(beforeMetrics, afterMetrics) {
    const improvements = {
      totalLoadTime: ((beforeMetrics.totalLoadTime - afterMetrics.totalLoadTime) / beforeMetrics.totalLoadTime * 100).toFixed(1),
      imageLoadTime: {}
    };

    // 计算每个图片的改进百分比
    Object.keys(afterMetrics.imageLoadTimes).forEach(imageSrc => {
      if (beforeMetrics.imageLoadTimes[imageSrc]) {
        const before = beforeMetrics.imageLoadTimes[imageSrc].duration;
        const after = afterMetrics.imageLoadTimes[imageSrc].duration;
        improvements.imageLoadTime[imageSrc] = ((before - after) / before * 100).toFixed(1);
      }
    });

    console.group('📊 性能改进报告');
    console.log('总加载时间改进:', improvements.totalLoadTime + '%');
    console.table(improvements.imageLoadTime);
    console.groupEnd();

    return improvements;
  }
}

/**
 * 图片加载优化工具
 */
export class ImageLoadOptimizer {
  /**
   * 创建图片加载策略
   * @param {string} src - 图片路径
   * @param {Object} options - 配置选项
   */
  static createLoadStrategy(src, options = {}) {
    const {
      priority = 'high',
      lazy = true,
      placeholder = null,
      onLoad = null,
      onError = null
    } = options;

    return {
      src,
      priority,
      lazy,
      placeholder,
      onLoad,
      onError,
      load: function() {
        return new Promise((resolve, reject) => {
          const img = new Image();
          
          if (priority === 'high') {
            img.fetchPriority = 'high';
          }
          
          img.onload = () => {
            if (onLoad) onLoad(img);
            resolve(img);
          };
          
          img.onerror = (error) => {
            if (onError) onError(error);
            reject(error);
          };
          
          img.src = src;
        });
      }
    };
  }

  /**
   * 批量优化图片加载
   * @param {Array} images - 图片配置数组
   */
  static optimizeBatchLoad(images) {
    const highPriority = images.filter(img => img.priority === 'high');
    const lowPriority = images.filter(img => img.priority === 'low');

    // 先加载高优先级图片
    const highPriorityPromises = highPriority.map(img => img.load());
    
    // 高优先级图片加载完成后，再加载低优先级图片
    return Promise.all(highPriorityPromises)
      .then(() => {
        console.log('✅ 高优先级图片加载完成');
        return Promise.all(lowPriority.map(img => img.load()));
      })
      .then(() => {
        console.log('✅ 所有图片加载完成');
      });
  }
}

export default PerformanceMonitor;