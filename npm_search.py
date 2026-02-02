import requests
import time
import threading
from datetime import datetime

# 添加缓存机制
CACHE = {}
CACHE_EXPIRY = 3600  # 缓存过期时间（秒）

# 线程锁，用于保护缓存
CACHE_LOCK = threading.Lock()

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

def compare_versions(version1, version2):
    """比较两个语义化版本号的大小
    返回 1 如果 version1 > version2
    返回 0 如果 version1 == version2
    返回 -1 如果 version1 < version2
    """
    try:
        # 分割版本号为数字部分
        v1_parts = list(map(int, version1.split('.')))
        v2_parts = list(map(int, version2.split('.')))
        
        # 补全长度，使两个版本号长度相同
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        # 逐个比较数字部分
        for i in range(max_len):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        
        return 0
    except Exception:
        # 如果版本号格式不正确，返回0
        return 0

def get_npm_packages(word):
    # 检查缓存
    current_time = time.time()
    with CACHE_LOCK:
        if word in CACHE:
            cached_data, timestamp = CACHE[word]
            if current_time - timestamp < CACHE_EXPIRY:
                print(f"使用缓存: {word}")
                return cached_data
    
    # 使用国内镜像源，提高访问速度
    url = f"https://registry.npmmirror.com/{word}"
    # 备用：如果国内镜像源失败，使用官方源
    backup_url = f"https://registry.npmjs.org/{word}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Accept": "application/json",
    }
    
    try:
        # 减少延迟，国内镜像源通常不需要那么长的延迟
        time.sleep(0.1)
        
        # 尝试使用国内镜像源
        response = requests.get(url, headers=headers, timeout=5)
        
        # 如果国内镜像源失败，使用备用地址
        if response.status_code != 200:
            print(f"国内镜像源失败，使用备用地址: {word}")
            response = requests.get(backup_url, headers=headers, timeout=10)
        
        # 检查响应状态
        if response.status_code == 404:
            print(f"请求失败: 包 {word} 不存在")
            return []
        
        response.raise_for_status()
        
        # 解析JSON响应
        data = response.json()
        results = []
        
        # 获取所有版本并选择版本号最大的版本
        max_version = '0.0.0'
        
        # 首先尝试从 versions 字段获取所有版本
        if 'versions' in data:
            versions = list(data['versions'].keys())
            for version in versions:
                if compare_versions(version, max_version) > 0:
                    max_version = version
        
        # 如果没有 versions 字段，回退到使用 latest 版本
        if max_version == '0.0.0':
            max_version = data.get('dist-tags', {}).get('latest', 'unknown')
        
        description = data.get('description', '暂无描述')[:80]  # 截取部分描述
        
        # 获取发布时间并转换为相对时间
        time_info = ""
        if 'time' in data and max_version in data['time']:
            publish_time_str = data['time'][max_version]
            time_info = get_relative_time(publish_time_str)
        
        # 构建结果
        results.append([word, max_version, f"{time_info}"])
        
        # 缓存结果
        with CACHE_LOCK:
            CACHE[word] = (results, current_time)
        
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"请求失败: npmjs API failed: {e}")
        return []

# 单独处理React Native相关的包搜索
def search_npm_packages(keywords, exact_match=True):
    npmjs_data = []
    
    # 如果关键词数量较少，使用串行请求
    if len(keywords) <= 3:
        # 对每个包名进行查询
        for kw in keywords:
            npm_results = get_npm_packages(kw)
            
            # 根据精准查询状态决定是否只取第一个结果
            if npm_results:
                if exact_match:
                    npmjs_data.append(npm_results[0])  # 只添加第一个结果
                else:
                    npmjs_data.extend(npm_results)  # 添加所有结果
    else:
        # 如果关键词数量较多，使用并行请求
        import concurrent.futures
        results_dict = {}
        
        # 使用线程池并行请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有任务
            future_to_kw = {executor.submit(get_npm_packages, kw): kw for kw in keywords}
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_kw):
                kw = future_to_kw[future]
                try:
                    results = future.result()
                    results_dict[kw] = results
                except Exception as e:
                    print(f"处理 {kw} 时出错: {e}")
        
        # 按照原始顺序处理结果
        for kw in keywords:
            if kw in results_dict:
                npm_results = results_dict[kw]
                if npm_results:
                    if exact_match:
                        npmjs_data.append(npm_results[0])  # 只添加第一个结果
                    else:
                        npmjs_data.extend(npm_results)  # 添加所有结果
    
    return npmjs_data