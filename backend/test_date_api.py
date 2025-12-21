#!/usr/bin/env python3
"""
测试前端和后端日期处理一致性
"""

import sys
import os
import requests
import json
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_date_api():
    """测试日期API调用"""
    
    base_url = "http://localhost:8000"
    
    # 模拟前端发送的日期参数（只精确到日）
    today = datetime.now().date()
    last_month_first_day = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    
    # 格式化日期为字符串（YYYY-MM-DD）
    start_date = last_month_first_day.strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    
    print("📅 测试日期参数：")
    print(f"开始日期: {start_date}")
    print(f"结束日期: {end_date}")
    print(f"今天: {today}")
    
    # 构建API请求参数
    params = {
        "page": 1,
        "page_size": 10,
        "start_time": start_date,
        "end_time": end_date
    }
    
    print("\n📡 发送API请求...")
    print(f"URL: {base_url}/api/account/login-records")
    print(f"参数: {json.dumps(params, indent=2)}")
    
    try:
        # 发送API请求
        response = requests.get(f"{base_url}/api/account/login-records", params=params)
        
        print(f"\n📊 API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API调用成功！")
            print(f"📊 返回记录数量: {len(data.get('data', []))}")
            print(f"📄 总记录数: {data.get('total', 0)}")
            print(f"📄 当前页: {data.get('page', 1)}")
            print(f"📄 总页数: {data.get('total_pages', 1)}")
            
            # 显示前几条记录的时间信息
            records = data.get('data', [])
            if records:
                print("\n📋 前5条记录的时间信息：")
                for i, record in enumerate(records[:5]):
                    login_time = record.get('login_time', '')
                    print(f"  {i+1}. {login_time}")
            else:
                print("⚠️  没有找到匹配的记录")
                
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务器，请确保后端服务正在运行")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

def test_specific_date_range():
    """测试特定日期范围"""
    
    base_url = "http://localhost:8000"
    
    # 测试今天的记录
    today = datetime.now().date()
    
    print("\n🔍 测试今天的登录记录...")
    
    params = {
        "page": 1,
        "page_size": 10,
        "start_time": today.strftime("%Y-%m-%d"),
        "end_time": today.strftime("%Y-%m-%d")
    }
    
    print(f"测试日期范围: {today} 到 {today}")
    
    try:
        response = requests.get(f"{base_url}/api/account/login-records", params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 找到 {len(data.get('data', []))} 条今天的记录")
            
            # 显示今天的记录
            records = data.get('data', [])
            for record in records:
                login_time = record.get('login_time', '')
                username = record.get('username', '')
                print(f"  - {username} 在 {login_time} 登录")
        else:
            print(f"❌ 查询失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main