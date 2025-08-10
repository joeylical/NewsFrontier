#!/usr/bin/env python3

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """测试登录功能"""
    print("测试登录...")
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": "testuser", "password": "password123"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 登录成功: {data['token'][:20]}...")
        return data['token']
    else:
        print(f"❌ 登录失败: {response.text}")
        return None

def test_register():
    """测试注册功能"""
    print("测试注册...")
    response = requests.post(
        f"{BASE_URL}/api/register",
        json={
            "username": "newuser", 
            "password": "newpassword", 
            "email": "new@example.com"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 注册成功: {data}")
    else:
        print(f"❌ 注册失败: {response.text}")

def test_protected_endpoints(token):
    """测试需要认证的API端点"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试today端点
    print("测试 /api/today...")
    response = requests.get(f"{BASE_URL}/api/today", headers=headers)
    if response.status_code == 200:
        print("✅ /api/today 成功")
    else:
        print(f"❌ /api/today 失败: {response.text}")
    
    # 测试topics端点
    print("测试 /api/topics...")
    response = requests.get(f"{BASE_URL}/api/topics", headers=headers)
    if response.status_code == 200:
        print("✅ /api/topics 成功")
    else:
        print(f"❌ /api/topics 失败: {response.text}")
    
    # 测试创建topic
    print("测试创建topic...")
    response = requests.post(
        f"{BASE_URL}/api/topics",
        headers=headers,
        json={"name": "Test Topic", "keywords": ["test", "demo"]}
    )
    if response.status_code == 200:
        print("✅ 创建topic成功")
    else:
        print(f"❌ 创建topic失败: {response.text}")
    
    # 测试topic详情
    print("测试topic详情...")
    response = requests.get(f"{BASE_URL}/api/topic/1", headers=headers)
    if response.status_code == 200:
        print("✅ topic详情成功")
    else:
        print(f"❌ topic详情失败: {response.text}")
    
    # 测试cluster详情
    print("测试cluster详情...")
    response = requests.get(f"{BASE_URL}/api/cluster/101", headers=headers)
    if response.status_code == 200:
        print("✅ cluster详情成功")
    else:
        print(f"❌ cluster详情失败: {response.text}")
    
    # 测试登出
    print("测试登出...")
    response = requests.post(f"{BASE_URL}/api/logout", headers=headers)
    if response.status_code == 200:
        print("✅ 登出成功")
    else:
        print(f"❌ 登出失败: {response.text}")

def main():
    print("开始API测试...")
    print(f"服务器地址: {BASE_URL}")
    print("-" * 50)
    
    # 测试注册
    test_register()
    print()
    
    # 测试登录
    token = test_login()
    if not token:
        print("登录失败，无法继续测试")
        return
    print()
    
    # 测试受保护的端点
    test_protected_endpoints(token)
    
    print("-" * 50)
    print("测试完成!")

if __name__ == "__main__":
    main()