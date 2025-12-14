<template>
  <div class="dashboard-container">

    <!-- 核心数据概览区 -->
    <div class="statistics-cards">
      <!-- 今日入库统计 -->
      <el-card class="stat-card inbound-card">
        <div class="card-icon green">
          <el-icon><Download /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-label">今日入库</div>
          <div class="card-main">
            <span class="main-number">{{ statistics.today_inbound.order_count }}</span>
            <span class="unit">单</span>
            <span class="change-badge" :class="getChangeClass(statistics.today_inbound.change_percent)">
              <el-icon v-if="statistics.today_inbound.change_percent > 0"><ArrowUp /></el-icon>
              <el-icon v-else-if="statistics.today_inbound.change_percent < 0"><ArrowDown /></el-icon>
              <el-icon v-else><Minus /></el-icon>
              {{ Math.abs(statistics.today_inbound.change_percent) }}%
            </span>
          </div>
          <div class="card-sub">共计 {{ formatNumber(statistics.today_inbound.material_count) }} 件器材</div>
        </div>
      </el-card>

      <!-- 今日出库统计 -->
      <el-card class="stat-card outbound-card">
        <div class="card-icon blue">
          <el-icon><Upload /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-label">今日出库</div>
          <div class="card-main">
            <span class="main-number">{{ statistics.today_outbound.order_count }}</span>
            <span class="unit">单</span>
            <span class="change-badge" :class="getChangeClass(statistics.today_outbound.change_percent)">
              <el-icon v-if="statistics.today_outbound.change_percent > 0"><ArrowUp /></el-icon>
              <el-icon v-else-if="statistics.today_outbound.change_percent < 0"><ArrowDown /></el-icon>
              <el-icon v-else><Minus /></el-icon>
              {{ Math.abs(statistics.today_outbound.change_percent) }}%
            </span>
          </div>
          <div class="card-sub">共计 {{ formatNumber(statistics.today_outbound.material_count) }} 件器材</div>
        </div>
      </el-card>

      <!-- 当前库存总量 -->
      <el-card class="stat-card inventory-card">
        <div class="card-icon orange">
          <el-icon><Box /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-label">库存总量</div>
          <div class="card-main">
            <span class="main-number">{{ formatNumber(statistics.total_inventory.quantity) }}</span>
            <span class="unit">件</span>
          </div>
          <div class="card-sub">涵盖 {{ statistics.total_inventory.material_types }} 个品类</div>
          <div class="card-sub">总价值：¥{{ formatNumber(statistics.total_inventory.total_value) }}元</div>
        </div>
      </el-card>

      <!-- 库存预警数量 -->
      <el-card class="stat-card warning-card" @click="scrollToWarnings">
        <div class="card-icon red">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-label">库存预警</div>
          <div class="card-main">
            <span class="main-number">{{ statistics.warning_count.total }}</span>
            <span class="unit">项需关注</span>
          </div>
          <div class="card-sub danger">缺货：{{ statistics.warning_count.out_of_stock }} 项</div>
          <div class="card-sub warning">库存紧张：{{ statistics.warning_count.low_stock }} 项</div>
        </div>
      </el-card>
    </div>

    <!-- 数据统计区域 -->
    <el-row :gutter="20">
      <!-- 出入库趋势 -->
      <el-col :xs="24" :sm="24" :md="24" :lg="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <span class="card-title">出入库趋势</span>
                <el-date-picker
                  v-model="selectedMonth"
                  type="month"
                  placeholder="选择月份"
                  format="YYYY年MM月"
                  value-format="YYYY-MM"
                  size="default"
                  @change="handleMonthChange"
                  style="width: 150px; margin-left: 15px;"
                />
              </div>
              <div class="trend-summary">
                <span class="summary-item inbound">入库总计：{{ formatNumber(monthlyTrend.total_inbound) }} 件</span>
                <span class="summary-item outbound">出库总计：{{ formatNumber(monthlyTrend.total_outbound) }} 件</span>
              </div>
            </div>
          </template>
          <div ref="trendChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 最近出入库记录 -->
      <el-col :xs="24" :sm="24" :md="24" :lg="8">
        <el-card class="recent-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">最近10条出入库记录</span>
              <el-button type="primary" link @click="refreshData">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          <div class="recent-list" v-loading="loading">
            <div v-if="recentTransactions.length === 0" class="empty-state">
              <el-empty description="暂无出入库记录" />
            </div>
            <div v-else class="transaction-item" v-for="item in recentTransactions" :key="item.transaction_id">
              <div class="transaction-header">
                <el-tag :type="getTransactionTagType(item.change_type)" size="small">
                  {{ getTransactionTypeName(item.change_type) }}
                </el-tag>
                <span class="transaction-time">{{ formatTime(item.transaction_time) }}</span>
              </div>
              <div class="transaction-content">
                <div class="material-info">
                  <span class="material-code">{{ item.material_code }}</span>
                  <span class="material-name">{{ item.material_name }}</span>
                </div>
                <div class="quantity-change" :class="item.change_type === 'IN' ? 'positive' : 'negative'">
                  {{ item.change_type === 'IN' ? '+' : '-' }}{{ Math.abs(item.quantity_change) }}
                </div>
              </div>
              <div class="transaction-footer">
                <span class="reference-number">{{ item.reference_number }}</span>
                <span class="creator">{{ item.creator }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 库存预警区 -->
    <div ref="warningsSection" class="warnings-section">
      <el-row :gutter="20">
        <!-- 缺货预警 -->
        <el-col :xs="24" :sm="24" :md="12">
          <el-card class="warning-card-container out-of-stock">
            <template #header>
              <div class="warning-header">
                <div class="warning-title">
                  <el-icon class="warning-icon"><CircleClose /></el-icon>
                  <span>缺货预警</span>
                </div>
                <el-tag type="danger" size="large">{{ warnings.summary.out_of_stock_count }} 项</el-tag>
              </div>
            </template>
            <div class="warning-detail">
              <el-table :data="warnings.out_of_stock" height="250" stripe>
                <el-table-column type="index" label="序号" width="60" />
                <el-table-column prop="material_code" label="器材编码" width="120" />
                <el-table-column prop="material_name" label="器材名称" width="150" show-overflow-tooltip />
                <el-table-column prop="material_specification" label="规格型号" width="120" show-overflow-tooltip />
                <el-table-column prop="current_stock" label="当前库存" width="100" align="center">
                  <template #default="scope">
                    <span class="stock-zero">{{ scope.row.current_stock }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="safety_stock" label="安全库存" width="100" align="center" />
                <el-table-column prop="shortage" label="缺口数量" width="100" align="center">
                  <template #default="scope">
                    <span class="shortage-text">{{ scope.row.shortage }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="major_name" label="所属专业" width="120" show-overflow-tooltip />
                <el-table-column prop="equipment_name" label="所属装备" width="120" show-overflow-tooltip />
              </el-table>
            </div>
          </el-card>
        </el-col>

        <!-- 库存紧张 -->
        <el-col :xs="24" :sm="24" :md="12">
          <el-card class="warning-card-container low-stock">
            <template #header>
              <div class="warning-header">
                <div class="warning-title">
                  <el-icon class="warning-icon"><WarningFilled /></el-icon>
                  <span>库存紧张</span>
                </div>
                <el-tag type="warning" size="large">{{ warnings.summary.low_stock_count }} 项</el-tag>
              </div>
            </template>
            <div class="warning-detail">
              <el-table :data="warnings.low_stock" height="250" stripe>
                <el-table-column type="index" label="序号" width="60" />
                <el-table-column prop="material_code" label="器材编码" width="120" />
                <el-table-column prop="material_name" label="器材名称" width="150" show-overflow-tooltip />
                <el-table-column prop="material_specification" label="规格型号" width="120" show-overflow-tooltip />
                <el-table-column prop="current_stock" label="当前库存" width="100" align="center">
                  <template #default="scope">
                    <span class="stock-low">{{ scope.row.current_stock }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="safety_stock" label="安全库存" width="100" align="center" />
                <el-table-column prop="shortage" label="缺口数量" width="100" align="center">
                  <template #default="scope">
                    <span class="shortage-text">{{ scope.row.shortage }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="major_name" label="所属专业" width="120" show-overflow-tooltip />
                <el-table-column prop="equipment_name" label="所属装备" width="120" show-overflow-tooltip />
              </el-table>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick, inject } from 'vue';
import { dashboardAPI } from '../../services';
import type { 
  DashboardStatistics, 
  MonthlyTrendData, 
  RecentTransaction,
  InventoryWarnings 
} from '../../services/system/dashboard';
import * as echarts from 'echarts';
import {
  Calendar, Sunny, Moon, Download, Upload, Box, Warning,
  ArrowUp, ArrowDown, Minus, Refresh, CircleClose, WarningFilled
} from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

// 从父组件注入用户信息
const currentUserFromParent: any = inject('currentUser', ref(null));

// 格式化当前月份（YYYY-MM格式）
const formatCurrentMonth = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
};

// 响应式数据
const loading = ref(false);
const statistics = ref<DashboardStatistics>({
  today_inbound: { order_count: 0, material_count: 0, change_percent: 0 },
  today_outbound: { order_count: 0, material_count: 0, change_percent: 0 },
  total_inventory: { quantity: 0, material_types: 0, total_value: 0 },
  warning_count: { total: 0, out_of_stock: 0, low_stock: 0 }
});

const monthlyTrend = ref<MonthlyTrendData>({
  daily_data: [],
  total_inbound: 0,
  total_outbound: 0,
  query_year: new Date().getFullYear(),
  query_month: new Date().getMonth() + 1,
  is_current_month: true
});

const recentTransactions = ref<RecentTransaction[]>([]);
const warnings = ref<InventoryWarnings>({
  out_of_stock: [],
  low_stock: [],
  summary: { out_of_stock_count: 0, low_stock_count: 0, total_warning_count: 0 }
});

// 选中的月份，默认为当前月
const selectedMonth = ref<string>(formatCurrentMonth());



// 图表引用
const trendChart = ref<HTMLElement | null>(null);
const warningsSection = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;



// 格式化数字（千分位）
const formatNumber = (num: number): string => {
  return num.toLocaleString('zh-CN');
};

// 格式化时间
const formatTime = (timeStr: string): string => {
  return timeStr.replace(/^\d{4}-\d{2}-\d{2}\s/, '');
};

// 获取环比变化样式类
const getChangeClass = (percent: number): string => {
  if (percent > 0) return 'increase';
  if (percent < 0) return 'decrease';
  return 'stable';
};

// 获取交易类型标签类型
const getTransactionTagType = (type: string): string => {
  const typeMap: Record<string, string> = {
    'IN': 'success',
    'OUT': 'primary',
    'ADJUST': 'warning'
  };
  return typeMap[type] || 'info';
};

// 获取交易类型名称
const getTransactionTypeName = (type: string): string => {
  const nameMap: Record<string, string> = {
    'IN': '入库',
    'OUT': '出库',
    'ADJUST': '调整'
  };
  return nameMap[type] || type;
};

// 滚动到预警区域
const scrollToWarnings = () => {
  warningsSection.value?.scrollIntoView({ behavior: 'smooth' });
};

// 处理月份选择变化
const handleMonthChange = async (value: string) => {
  if (!value) return;
  
  const [year, month] = value.split('-').map(Number);
  await loadTrendData(year, month);
};

// 加载趋势数据
const loadTrendData = async (year?: number, month?: number) => {
  try {
    const trendData = await dashboardAPI.getMonthlyTrend(year, month);
    monthlyTrend.value = trendData;
    
    // 更新图表
    await nextTick();
    initTrendChart();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载趋势数据失败');
  }
};

// 初始化趋势图表
const initTrendChart = () => {
  if (!trendChart.value) return;
  
  chartInstance = echarts.init(trendChart.value);
  
  // 只显示日期（如 "1", "2", "3"），去掉前导0
  const dates = monthlyTrend.value.daily_data.map(d => String(parseInt(d.date.substring(8))));
  const inboundData = monthlyTrend.value.daily_data.map(d => d.inbound);
  const outboundData = monthlyTrend.value.daily_data.map(d => d.outbound);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['入库', '出库'],
      top: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      name: '数量（件）'
    },
    series: [
      {
        name: '入库',
        type: 'bar',
        itemStyle: { 
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#85CE61' },
            { offset: 1, color: '#67C23A' }
          ])
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#95D475' },
              { offset: 1, color: '#7BCF4E' }
            ])
          }
        },
        data: inboundData
      },
      {
        name: '出库',
        type: 'bar',
        itemStyle: { 
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#66B1FF' },
            { offset: 1, color: '#409EFF' }
          ])
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#79BBFF' },
              { offset: 1, color: '#5DAAFF' }
            ])
          }
        },
        data: outboundData
      }
    ]
  };
  
  chartInstance.setOption(option as any);
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    chartInstance?.resize();
  });
};

// 加载所有数据
const loadAllData = async () => {
  loading.value = true;
  try {
    // 并行加载所有数据
    const [statsData, trendData, transData, warningData] = await Promise.all([
      dashboardAPI.getStatistics(),
      dashboardAPI.getMonthlyTrend(), // 默认加载当前月
      dashboardAPI.getRecentTransactions(10),
      dashboardAPI.getInventoryWarnings()
    ]);
    
    statistics.value = statsData;
    monthlyTrend.value = trendData;
    recentTransactions.value = transData.transactions;
    warnings.value = warningData;
    
    // 同步选中的月份
    selectedMonth.value = `${trendData.query_year}-${String(trendData.query_month).padStart(2, '0')}`;
    
    // 等待DOM更新后初始化图表
    await nextTick();
    initTrendChart();
    
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载数据失败');
  } finally {
    loading.value = false;
  }
};

// 刷新数据
const refreshData = async () => {
  await loadAllData();
  ElMessage.success('数据已刷新');
};

// 组件挂载时加载数据
onMounted(() => {
  loadAllData();
});
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}



/* 核心统计卡片 */
.statistics-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .statistics-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .statistics-cards {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
  flex-shrink: 0;
}

.card-icon.green {
  background: linear-gradient(135deg, #67C23A 0%, #85CE61 100%);
}

.card-icon.blue {
  background: linear-gradient(135deg, #409EFF 0%, #66B1FF 100%);
}

.card-icon.orange {
  background: linear-gradient(135deg, #E6A23C 0%, #F56C6C 100%);
}

.card-icon.red {
  background: linear-gradient(135deg, #F56C6C 0%, #F78989 100%);
}

.card-content {
  flex: 1;
}

.card-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.card-main {
  display: flex;
  align-items: baseline;
  gap: 5px;
  margin-bottom: 8px;
}

.main-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.unit {
  font-size: 16px;
  color: #606266;
}

.change-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  margin-left: 10px;
}

.change-badge.increase {
  background-color: #f0f9ff;
  color: #67C23A;
}

.change-badge.decrease {
  background-color: #fef0f0;
  color: #F56C6C;
}

.change-badge.stable {
  background-color: #f4f4f5;
  color: #909399;
}

.card-sub {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.card-sub.danger {
  color: #F56C6C;
  font-weight: 500;
}

.card-sub.warning {
  color: #E6A23C;
  font-weight: 500;
}

/* 图表卡片 */
.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.trend-summary {
  display: flex;
  gap: 20px;
}

.summary-item {
  font-size: 14px;
  font-weight: 500;
}

.summary-item.inbound {
  color: #67C23A;
}

.summary-item.outbound {
  color: #409EFF;
}

.chart-container {
  width: 100%;
  height: 400px;
}

/* 最近记录卡片 */
.recent-card {
  margin-bottom: 20px;
}

.recent-list {
  height: 400px;
  overflow-y: auto;
}

.empty-state {
  padding: 40px 0;
}

.transaction-item {
  padding: 12px;
  border-bottom: 1px solid #EBEEF5;
  transition: background-color 0.2s;
}

.transaction-item:last-child {
  border-bottom: none;
}

.transaction-item:hover {
  background-color: #f5f7fa;
}

.transaction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.transaction-time {
  font-size: 12px;
  color: #909399;
}

.transaction-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.material-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.material-code {
  font-size: 12px;
  color: #909399;
}

.material-name {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.quantity-change {
  font-size: 18px;
  font-weight: bold;
  min-width: 60px;
  text-align: right;
}

.quantity-change.positive {
  color: #67C23A;
}

.quantity-change.negative {
  color: #F56C6C;
}

.transaction-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

/* 库存预警区 */
.warnings-section {
  margin-top: 20px;
}

.warning-card-container {
  border-width: 2px;
}

.warning-card-container.out-of-stock {
  border-color: #F56C6C;
  background-color: #FEF0F0;
}

.warning-card-container.low-stock {
  border-color: #E6A23C;
  background-color: #FDF6EC;
}

.warning-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.warning-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.warning-card-container.out-of-stock .warning-title {
  color: #F56C6C;
}

.warning-card-container.low-stock .warning-title {
  color: #E6A23C;
}

.warning-icon {
  font-size: 20px;
}



.stock-zero {
  color: #F56C6C;
  font-weight: bold;
}

.stock-low {
  color: #E6A23C;
  font-weight: bold;
}

.shortage-text {
  color: #F56C6C;
  font-weight: 600;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .statistics-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .greeting-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .statistics-cards {
    grid-template-columns: 1fr;
  }
  
  .trend-summary {
    flex-direction: column;
    gap: 5px;
  }
}
</style>
