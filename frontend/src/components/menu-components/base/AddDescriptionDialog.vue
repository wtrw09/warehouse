<template>
  <!-- 添加专业描述对话框 -->
  <el-dialog
    v-model="dialogVisible"
    title="添加专业描述"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form :model="form" label-width="120px">
      <el-form-item label="描述名称：">
        <el-input
          v-model="form.descriptionNames"
          placeholder="请输入描述名称，多个用逗号隔开，例如：油漆,稀释剂,喷漆"
          type="textarea"
          :rows="3"
          :autosize="{ minRows: 3, maxRows: 6 }"
        />
        <div style="color: #909399; font-size: 12px; margin-top: 8px;">
          提示：可以输入多个描述名称，用逗号隔开，系统会自动转换为JSON数组格式
        </div>
      </el-form-item>
      
      <el-form-item label="选择一级专业：">
        <el-select
          v-model="form.selectedPrimaryMajor"
          placeholder="请选择一级专业"
          style="width: 100%"
          @change="handlePrimaryMajorChange"
          filterable
        >
          <el-option
            v-for="major in allPrimaryMajors"
            :key="major.major_code"
            :label="major.major_name"
            :value="major.major_code"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="选择二级专业：">
        <el-select
          v-model="form.selectedSecondaryMajor"
          placeholder="请选择二级专业"
          style="width: 100%"
          filterable
          :disabled="!form.selectedPrimaryMajor"
        >
          <el-option
            v-for="major in filteredSecondaryMajors"
            :key="major.sub_major_code"
            :label="major.sub_major_name"
            :value="major.sub_major_code"
          />
        </el-select>
        <div v-if="!form.selectedPrimaryMajor" style="color: #909399; font-size: 12px; margin-top: 8px;">
          提示：请先选择一级专业
        </div>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          确定添加
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import { subMajorAPI } from '@/services/base/sub_major';
import { majorAPI } from '@/services/base/major';
import type { SubMajorResponse } from '@/services/types/sub_major';
import type { MajorResponse } from '@/services/types/major';

interface Props {
  materialName?: string;
  searchText?: string;
}

interface Emits {
  (e: 'success'): void;
  (e: 'close'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const dialogVisible = ref(false);
const loading = ref(false);
const allPrimaryMajors = ref<MajorResponse[]>([]);
const allSecondaryMajors = ref<SubMajorResponse[]>([]);
const filteredSecondaryMajors = ref<SubMajorResponse[]>([]);

const form = reactive({
  descriptionNames: '',
  selectedPrimaryMajor: '',
  selectedSecondaryMajor: ''
});

// 打开对话框
const open = async () => {
  try {
    // 优先使用搜索文本，如果没有搜索文本则使用器材名称
    form.descriptionNames = props.searchText || props.materialName || '';
    
    // 分别加载一级专业和二级专业数据
    const [primaryResponse, secondaryResponse] = await Promise.all([
      majorAPI.getMajors(),
      subMajorAPI.getSubMajors()
    ]);
    
    console.log('一级专业API响应:', primaryResponse);
    console.log('二级专业API响应:', secondaryResponse);
    
    // 设置一级专业数据
    allPrimaryMajors.value = primaryResponse.data;
    
    // 设置二级专业数据
    allSecondaryMajors.value = secondaryResponse.data;
    
    console.log('一级专业数据:', allPrimaryMajors.value);
    console.log('二级专业数据:', allSecondaryMajors.value);
    
    // 重置选择
    form.selectedPrimaryMajor = '';
    form.selectedSecondaryMajor = '';
    filteredSecondaryMajors.value = [];
    
    dialogVisible.value = true;
  } catch (error) {
    console.error('加载专业数据失败:', error);
    ElMessage.error('加载专业数据失败');
  }
};

// 处理一级专业选择变化
const handlePrimaryMajorChange = (primaryMajorCode: string) => {
  console.log('一级专业选择变化:', primaryMajorCode);
  
  if (primaryMajorCode) {
    // 根据一级专业代码筛选对应的二级专业
    const primaryMajor = allPrimaryMajors.value.find(major => major.major_code === primaryMajorCode);
    console.log('找到的一级专业:', primaryMajor);
    
    if (primaryMajor && primaryMajor.id) {
      console.log('一级专业ID:', primaryMajor.id);
      console.log('所有二级专业数据:', allSecondaryMajors.value);
      
      // 调试：打印所有二级专业的major_id
      allSecondaryMajors.value.forEach((secondaryMajor, index) => {
        console.log(`二级专业${index}:`, secondaryMajor.sub_major_code, 'major_id:', secondaryMajor.major_id, '是否匹配:', secondaryMajor.major_id === primaryMajor.id);
      });
      
      // 根据major_id筛选对应的二级专业
      filteredSecondaryMajors.value = allSecondaryMajors.value.filter(secondaryMajor => 
        secondaryMajor.major_id === primaryMajor.id
      );
      
      console.log('筛选后的二级专业:', filteredSecondaryMajors.value);
    }
  } else {
    // 清空一级专业选择时，清空二级专业列表
    filteredSecondaryMajors.value = [];
  }
  
  // 重置二级专业选择
  form.selectedSecondaryMajor = '';
};

// 处理对话框关闭
const handleClose = () => {
  dialogVisible.value = false;
  // 重置表单
  form.descriptionNames = '';
  form.selectedPrimaryMajor = '';
  form.selectedSecondaryMajor = '';
  filteredSecondaryMajors.value = [];
  loading.value = false;
  emit('close');
};

// 处理添加专业描述
const handleSubmit = async () => {
  if (!form.selectedPrimaryMajor) {
    ElMessage.warning('请先选择一级专业');
    return;
  }
  
  if (!form.selectedSecondaryMajor) {
    ElMessage.warning('请选择二级专业');
    return;
  }
  
  if (!form.descriptionNames.trim()) {
    ElMessage.warning('请输入描述名称');
    return;
  }
  
  try {
    loading.value = true;
    
    // 获取选中的二级专业
    const selectedMajor = filteredSecondaryMajors.value.find(
      major => major.sub_major_code === form.selectedSecondaryMajor
    );
    
    if (!selectedMajor) {
      ElMessage.error('选择的二级专业不存在');
      return;
    }
    
    // 解析描述名称，使用逗号分隔，去除重复值
    const descriptionArray = form.descriptionNames
      .split(',')
      .filter(name => name.trim())
      .map(name => name.trim());
    
    const uniqueDescriptions = [...new Set(descriptionArray)];
    
    // 使用addDescriptionToSubMajor接口添加描述
    // 这里我们逐个添加描述项，因为后端接口设计为添加单个描述项
    for (const description of uniqueDescriptions) {
      const addDescriptionData = {
        sub_major_id: selectedMajor.id,
        description: description
      };
      
      await subMajorAPI.addDescriptionToSubMajor(addDescriptionData);
    }
    
    ElMessage.success(`成功添加 ${uniqueDescriptions.length} 个描述项`);
    handleClose();
    emit('success');
    
  } catch (error) {
    console.error('添加专业描述失败:', error);
    ElMessage.error('添加专业描述失败');
  } finally {
    loading.value = false;
  }
};

// 暴露方法给父组件
defineExpose({
  open
});
</script>