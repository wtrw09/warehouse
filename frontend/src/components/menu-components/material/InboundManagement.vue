<template>
  <div class="base-management-container">
    <!-- 入库单列表组件 -->
    <InboundOrders 
      v-if="currentView === 'list'" 
      ref="inboundOrdersRef"
      @add="handleAdd"
      @view="handleView"
      @edit="handleEdit"
    />
    
    <!-- 入库单编辑组件 -->
    <InboundOrderEdit 
      v-else-if="currentView === 'edit' || currentView === 'view'" 
      :edit-id="editId"
      :readonly="currentView === 'view'"
      @back="handleBack"
      @saved="handleSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import InboundOrders from './InboundOrders.vue'
import InboundOrderEdit from './InboundOrderEdit.vue'

// 当前视图状态
const currentView = ref<'list' | 'edit' | 'view'>('list')
const editId = ref<number | null>(null)

// 获取InboundOrders组件的引用
const inboundOrdersRef = ref<InstanceType<typeof InboundOrders> | null>(null)

// 处理新增入库单
const handleAdd = () => {
  editId.value = null
  currentView.value = 'edit'
}

// 处理查看入库单
const handleView = (id: number) => {
  editId.value = id
  currentView.value = 'view'
}

// 处理编辑入库单
const handleEdit = (id: number) => {
  editId.value = id
  currentView.value = 'edit'
}

// 处理返回操作
const handleBack = async () => {
  currentView.value = 'list'
  editId.value = null
  
  // 等待DOM更新后刷新列表
  await nextTick()
  if (inboundOrdersRef.value) {
    inboundOrdersRef.value.getInboundOrders()
  }
}

// 处理保存成功
const handleSaved = async () => {
  currentView.value = 'list'
  editId.value = null
  
  // 等待DOM更新后刷新列表
  await nextTick()
  if (inboundOrdersRef.value) {
    inboundOrdersRef.value.getInboundOrders()
  }
}

onMounted(() => {
  // 初始化显示列表
  currentView.value = 'list'
})
</script>

<style scoped lang="scss">
@use '../../../css/base-styles-mixin.scss' as mixins;
@import '../../../css/base-styles.css';
</style>