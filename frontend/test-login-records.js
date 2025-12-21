// 测试登录记录API调用
const testLoginRecordsAPI = async () => {
  try {
    // 模拟API调用参数
    const params = {
      page: 1,
      page_size: 20,
      start_time: '2025-11-01',
      end_time: '2025-12-20'
    };
    
    console.log('测试登录记录API调用...');
    console.log('请求参数:', params);
    
    // 使用fetch调用API
    const response = await fetch('http://localhost:8000/api/account/login-records', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + localStorage.getItem('token')
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('API响应:', data);
      console.log('数据条数:', data.data?.length || 0);
      console.log('总记录数:', data.total || 0);
    } else {
      console.error('API调用失败:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('测试失败:', error);
  }
};

// 运行测试
testLoginRecordsAPI();