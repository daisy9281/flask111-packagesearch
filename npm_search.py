import requests
import time
from datetime import datetime

def get_relative_time(publish_time_str):
    """计算相对时间，返回如"12天前"这样的格式"""
    try:
        # 解析发布时间
        publish_time = datetime.strptime(publish_time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        
        # 获取当前时间
        current_time = datetime.utcnow()
        
        # 计算时间差
        delta = current_time - publish_time
        
        # 转换为秒
        seconds = delta.total_seconds()
        
        # 根据时间差返回不同格式
        if seconds < 60:
            return f"{int(seconds)}秒前"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}分钟前"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}小时前"
        elif seconds < 2592000:
            days = int(seconds / 86400)
            return f"{days}天前"
        elif seconds < 31536000:
            months = int(seconds / 2592000)
            return f"{months}个月前"
        else:
            years = int(seconds / 31536000)
            return f"{years}年前"
            
    except Exception as e:
        print(f"时间格式转换错误: {e}")
        return "未知时间"

def get_npm_packages(word):
    # 使用npm官方的单个包信息API
    url = f"https://registry.npmjs.org/{word}"
    # 也可以选择使用国内镜像源，可能更快且更稳定
    # url = f"https://registry.npmmirror.com/{word}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Accept": "application/json",
    }
    
    try:
        # 添加延迟，避免请求过于频繁
        time.sleep(0.5)
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # 检查响应状态
        if response.status_code == 404:
            print(f"请求失败: 包 {word} 不存在")
            return []
        
        response.raise_for_status()
        
        # 解析JSON响应
        data = response.json()
        results = []
        
        # 获取最新版本信息
        latest_version = data.get('dist-tags', {}).get('latest', 'unknown')
        description = data.get('description', '暂无描述')[:80]  # 截取部分描述
        
        # 获取发布时间并转换为相对时间
        time_info = ""
        if 'time' in data and latest_version in data['time']:
            publish_time_str = data['time'][latest_version]
            time_info = get_relative_time(publish_time_str)
        
        # 构建结果
        results.append([word, latest_version, f"{time_info}"])
        
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"请求失败: npmjs API failed: {e}")
        return []

# 单独处理React Native相关的包搜索
def search_npm_packages(keywords, exact_match=True):
    npmjs_data = []
    
    # 对每个包名进行查询
    for kw in keywords:
        npm_results = get_npm_packages(kw)
        
        # 根据精准查询状态决定是否只取第一个结果
        if npm_results:
            if exact_match:
                npmjs_data.append(npm_results[0])  # 只添加第一个结果
            else:
                npmjs_data.extend(npm_results)  # 添加所有结果
    
    return npmjs_data