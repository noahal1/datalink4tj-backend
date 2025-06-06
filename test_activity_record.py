import sys
import os
import json
import requests
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# API基础URL
API_BASE_URL = "http://localhost:8000"

# 测试用户凭据
TEST_USER = {
    "username": "admin",
    "password": "admin"
}

def get_auth_token():
    """获取认证令牌"""
    response = requests.post(
        f"{API_BASE_URL}/users/token",
        data=TEST_USER,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        data = response.json()
        return data["access_token"]
    else:
        print(f"获取令牌失败: {response.status_code}")
        print(response.text)
        return None

def test_create_event():
    """测试创建事件并记录活动"""
    token = get_auth_token()
    if not token:
        return
    
    # 创建一个新事件
    event_data = {
        "name": "测试事件",
        "department": "QA",
        "start_time": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "end_time": (datetime.now() + timedelta(days=2)).date().isoformat()
    }
    
    response = requests.post(
        f"{API_BASE_URL}/events/",
        json=event_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        event = response.json()
        print(f"事件创建成功: {event['name']}, ID: {event['id']}")
        return event
    else:
        print(f"创建事件失败: {response.status_code}")
        print(response.text)
        return None

def test_update_event(event_id):
    """测试更新事件并记录活动"""
    token = get_auth_token()
    if not token:
        return
    
    # 更新事件
    event_data = {
        "name": "已更新的测试事件",
        "department": "ADMIN",
        "start_time": (datetime.now() + timedelta(days=2)).date().isoformat(),
        "end_time": (datetime.now() + timedelta(days=3)).date().isoformat()
    }
    
    response = requests.put(
        f"{API_BASE_URL}/events/{event_id}",
        json=event_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        event = response.json()
        print(f"事件更新成功: {event['name']}, ID: {event['id']}")
        return event
    else:
        print(f"更新事件失败: {response.status_code}")
        print(response.text)
        return None

def test_delete_event(event_id):
    """测试删除事件并记录活动"""
    token = get_auth_token()
    if not token:
        return
    
    response = requests.delete(
        f"{API_BASE_URL}/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        print(f"事件删除成功: ID {event_id}")
        return True
    else:
        print(f"删除事件失败: {response.status_code}")
        print(response.text)
        return False

def test_get_activities():
    """测试获取活动记录"""
    token = get_auth_token()
    if not token:
        return
    
    response = requests.get(
        f"{API_BASE_URL}/activities/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        activities = response.json()
        print(f"获取到 {len(activities)} 条活动记录:")
        for activity in activities[:5]:  # 只显示前5条
            print(f"- {activity['title']} ({activity['time']}): {activity['action']}")
        return activities
    else:
        print(f"获取活动记录失败: {response.status_code}")
        print(response.text)
        return None

def run_tests():
    """运行所有测试"""
    print("开始测试数据变更记录功能...")
    
    # 创建事件
    event = test_create_event()
    if not event:
        return
    
    # 更新事件
    updated_event = test_update_event(event["id"])
    if not updated_event:
        return
    
    # 删除事件
    if not test_delete_event(event["id"]):
        return
    
    # 获取活动记录
    activities = test_get_activities()
    
    print("\n测试完成!")

if __name__ == "__main__":
    run_tests() 