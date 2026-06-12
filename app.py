from flask import Flask, render_template, request
import os

# 导入新创建的独立模块
from pub_search import search_flutter_packages
from npm_search import search_npm_packages

app = Flask(__name__)

# 注入当前年份
def inject_current_year():
    import datetime
    return {'current_year': datetime.datetime.now().year}

app.context_processor(inject_current_year)

@app.route('/')
def index():
    # 设置默认的精准查询状态为True
    return render_template('index.html', 
                          pub_exact_match=True,
                          npm_exact_match=True)

# Pub搜索路由
@app.route('/search-pub', methods=['POST'])
def search_pub():
    # 同时支持表单和JSON请求
    if request.is_json:
        data = request.get_json()
        keyword = data.get('pub_keyword', '')
        exact_match = data.get('pub_exact_match', False)
    else:
        # 获取关键词，不设置默认值
        keyword = request.form.get('pub_keyword', '')
        exact_match = request.form.get('pub_exact_match') == 'on'  # 获取精准查询状态
    
    # 分割逗号分隔的包名
    keywords = [kw.strip() for kw in keyword.split(',') if kw.strip()]
    
    # 如果没有关键词，不执行搜索
    if not keywords:
        pubdev_data = []
    else:
        # 使用独立模块进行搜索
        pubdev_data = search_flutter_packages(keywords, exact_match)
    
    # 打印搜索结果
    print(f"搜索关键词: {keyword}")
    print(f"精准查询: {exact_match}")
    print(f"搜索结果数量: {len(pubdev_data)}")
    print("搜索结果:")
    for i, result in enumerate(pubdev_data, 1):
        print(f"  {i}. {result}")
    
    return render_template('index.html', 
                          active_tab='pub',
                          pub_keyword=keyword,
                          pub_exact_match=exact_match,
                          pubdev_data=pubdev_data)

# NPM搜索路由
@app.route('/search-npm', methods=['POST'])
def search_npm():
    # 同时支持表单和JSON请求
    if request.is_json:
        data = request.get_json()
        keyword = data.get('npm_keyword', '')
        exact_match = data.get('npm_exact_match', False)
    else:
        # 获取关键词，不设置默认值
        keyword = request.form.get('npm_keyword', '')
        exact_match = request.form.get('npm_exact_match') == 'on'  # 获取精准查询状态
    
    # 分割逗号分隔的包名
    keywords = [kw.strip() for kw in keyword.split(',') if kw.strip()]
    
    # 如果没有关键词，不执行搜索
    if not keywords:
        npmjs_data = []
    else:
        # 使用独立模块进行搜索
        npmjs_data = search_npm_packages(keywords, exact_match)
    
    return render_template('index.html', 
                          active_tab='npm',
                          npm_keyword=keyword,
                          npm_exact_match=exact_match,
                          npmjs_data=npmjs_data)

# CDN密钥计算器路由
@app.route('/cdn-calculator')
def cdn_calculator():
    return render_template('cdn-calculator.html')

if __name__ == '__main__':
    # 创建templates目录
    if not os.path.exists('templates'):
        os.makedirs('templates')
        # 创建index.html文件
        with open('templates/index.html', 'w') as f:
            f.write('''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>包搜索工具</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        form { margin-bottom: 20px; }
        input { padding: 8px; width: 300px; }
        button { padding: 8px 15px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #45a049; }
        .results { margin-top: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .tab { overflow: hidden; border: 1px solid #ccc; background-color: #f1f1f1; }
        .tab button { background-color: inherit; float: left; border: none; outline: none; cursor: pointer; padding: 14px 16px; transition: 0.3s; color: black; }
        .tab button:hover { background-color: #ddd; }
        .tab button.active { background-color: #ccc; }
        .tabcontent { display: none; padding: 6px 12px; border: 1px solid #ccc; border-top: none; }
    </style>
    <script>
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }
        // 默认显示第一个标签
        document.addEventListener("DOMContentLoaded", function() {
            document.getElementsByClassName("tablinks")[0].click();
        });
    </script>
</head>
<body>
    <h1>包搜索工具</h1>
    <form action="/search" method="post">
        <input type="text" name="keyword" placeholder="请输入搜索关键词" value="{{ keyword }}" required>
        <button type="submit">搜索</button>
    </form>
    
    <div class="results">
        <div class="tab">
            <button class="tablinks" onclick="openTab(event, 'pubdev')">Pub.dev 结果</button>
            <button class="tablinks" onclick="openTab(event, 'npmjs')">NPM.js 结果</button>
        </div>
        
        <div id="pubdev" class="tabcontent">
            <h2>Pub.dev 搜索结果 (关键词: {{ keyword }})</h2>
            {% if pubdev_data %}
            <table>
                <tr>
                    <th>包名</th>
                    <th>版本</th>
                    <th>更新时间</th>
                </tr>
                {% for item in pubdev_data %}
                <tr>
                    <td>{{ item[0] }}</td>
                    <td>{{ item[1] }}</td>
                    <td>{{ item[2] }}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p>没有找到相关的包信息</p>
            {% endif %}
        </div>
        
        <div id="npmjs" class="tabcontent">
            <h2>NPM.js 搜索结果 (关键词: {{ keyword }})</h2>
            {% if npmjs_data %}
            <table>
                <tr>
                    <th>包名</th>
                    <th>版本</th>
                    <th>其他信息</th>
                </tr>
                {% for item in npmjs_data %}
                <tr>
                    <td>{{ item[0] }}</td>
                    <td>{{ item[1] }}</td>
                    <td>{{ item[2] }}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p>没有找到相关的包信息</p>
            {% endif %}
        </div>
    </div>
</body>
</html>''')

# 确保在生产环境中使用正确的配置
if __name__ == '__main__':
    # 解析命令行参数获取端口（仅用于本地开发）
    import sys
    port = 5000  # 默认端口
    if len(sys.argv) > 2 and sys.argv[1] == '--port':
        try:
            port = int(sys.argv[2])
        except ValueError:
            print('Invalid port number, using default 5000')
    # 本地开发模式启动应用
    app.run(debug=True, host='0.0.0.0', port=port)

# Vercel部署需要的WSGI应用
gunicorn_app = app
# 也支持ASGI应用格式，保持兼容性
application = app