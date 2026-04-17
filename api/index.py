from flask import Flask, request, jsonify
import sys
import os
import time
import logging
import pickle
import numpy as np
from collections import Counter

# 确保可以导入python目录中的模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'python')))

from zodiac_ml_predictor import load_model, predict_next
import pandas as pd

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============================================
# CORS配置 - 允许前端跨域访问
# ============================================
@app.after_request
def after_request(response):
    """统一 CORS 头；OPTIONS 预检也由 Flask 自动处理并经过本钩子。"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS,PATCH'
    response.headers['Access-Control-Max-Age'] = '86400'
    return response

# ============================================
# 生肖配置 - 与zodiac_ml_predictor.py和模型训练保持一致
# 模型使用的映射：
# 1: 马, 2: 蛇, 3: 龙, 4: 兔, 5: 虎, 6: 牛,
# 7: 鼠, 8: 猪, 9: 狗, 10: 鸡, 11: 猴, 12: 羊
# ============================================
# 生肖名称列表（按ID顺序）
ZODIAC_ALL = ["马", "蛇", "龙", "兔", "虎", "牛", "鼠", "猪", "狗", "鸡", "猴", "羊"]

ZODIAC_CONFIG = {
    # ID到名称的映射 (与模型训练时一致)
    'id_to_name': {
        1: '马', 2: '蛇', 3: '龙', 4: '兔', 5: '虎', 6: '牛',
        7: '鼠', 8: '猪', 9: '狗', 10: '鸡', 11: '猴', 12: '羊'
    },
    
    # 生肖到五行的映射
    'zodiac_to_element': {
        '马': '火', '蛇': '火', '龙': '土', '兔': '木',
        '虎': '木', '牛': '土', '鼠': '水', '猪': '水',
        '狗': '土', '鸡': '金', '猴': '金', '羊': '土'
    },
    
    # 生肖到波色的映射
    'zodiac_to_color': {
        '马': '红', '蛇': '红', '龙': '红', '兔': '绿',
        '虎': '蓝', '牛': '绿', '鼠': '红', '猪': '蓝',
        '狗': '绿', '鸡': '红', '猴': '蓝', '羊': '绿'
    }
}

# 旧的ZODIAC_MAP保留用于向后兼容
ZODIAC_MAP = {
    1: '马', 2: '蛇', 3: '龙', 4: '兔', 5: '虎', 6: '牛',
    7: '鼠', 8: '猪', 9: '狗', 10: '鸡', 11: '猴', 12: '羊'
}

# 全局变量
model = None
cached_data = None
cached_data_time = 0
DATA_CACHE_TTL = 60  # 数据缓存时间（秒）

def load_model_once():
    """只加载模型一次"""
    global model
    if model is None:
        try:
            # 模型文件路径
            model_path = os.path.join(os.path.dirname(__file__), '..', 'python', 'zodiac_model.pkl')
            model = load_model(model_path)
            logger.info("模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            model = None

def get_history_data():
    """获取历史数据，带缓存机制"""
    global cached_data, cached_data_time
    current_time = time.time()
    
    # 检查缓存是否有效
    if cached_data is not None and (current_time - cached_data_time) < DATA_CACHE_TTL:
        return cached_data
    
    # 读取历史数据
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'lottery_history.csv')
    try:
        df = pd.read_csv(data_path)
        # 更新缓存
        cached_data = df
        cached_data_time = current_time
        return df
    except Exception as e:
        print(f"读取历史数据失败: {str(e)}")
        return None

def build_features_from_history(history_data):
    """
    从历史数据构建特征向量
    与ml_api_server.py中的特征工程保持一致
    """
    n_zodiacs = 12
    features = []
    
    # 转换数据格式 - 统一转为生肖名称
    zodiacs = []
    for item in history_data:
        z = item['zodiac']
        if isinstance(z, int) and 1 <= z <= 12:
            zodiacs.append(ZODIAC_CONFIG['id_to_name'][z])
        elif isinstance(z, str):
            # 处理前端传递的逗号分隔字符串（例如"鼠,牛,虎,兔,龙,蛇,马"）
            if ',' in z:
                # 取第7个元素（索引6）作为特码生肖
                zod_arr = z.split(',')
                if len(zod_arr) > 6:
                    zodiac_name = zod_arr[6].strip()
                    if zodiac_name in ZODIAC_ALL:
                        zodiacs.append(zodiac_name)
                    else:
                        zodiacs.append(ZODIAC_ALL[0])  # 默认马
                else:
                    zodiacs.append(ZODIAC_ALL[0])  # 默认马
            elif z in ZODIAC_ALL:
                zodiacs.append(z)
            else:
                zodiacs.append(ZODIAC_ALL[0])  # 默认马
        else:
            zodiacs.append(ZODIAC_ALL[0])  # 默认马
    
    # 基础统计特征
    miss_counts = {z: 0 for z in ZODIAC_ALL}
    max_miss = {z: 0 for z in ZODIAC_ALL}
    
    # 计算遗漏
    for z in ZODIAC_ALL:
        last_appear = -1
        for i, zod in enumerate(zodiacs):
            if zod == z:
                last_appear = i
        if last_appear == -1:
            miss_counts[z] = len(zodiacs)
        else:
            miss_counts[z] = len(zodiacs) - last_appear - 1
    
    # 计算最大遗漏
    for z in ZODIAC_ALL:
        current_miss = 0
        for zod in zodiacs:
            if zod == z:
                max_miss[z] = max(max_miss[z], current_miss)
                current_miss = 0
            else:
                current_miss += 1
    
    # 近N期统计
    recent_10 = zodiacs[-10:]
    recent_20 = zodiacs[-20:]
    recent_50 = zodiacs[-50:]
    
    # 计算排名
    counts_20 = Counter(recent_20)
    ranks = {}
    for z in ZODIAC_ALL:
        count = counts_20.get(z, 0)
        rank = 1
        for other_z in ZODIAC_ALL:
            if counts_20.get(other_z, 0) > count:
                rank += 1
        ranks[z] = rank
    
    # 计算连开次数
    consecutive = {z: 0 for z in ZODIAC_ALL}
    break_state = {z: 0 for z in ZODIAC_ALL}
    
    for z in ZODIAC_ALL:
        cons = 0
        for i in range(len(zodiacs) - 1, -1, -1):
            if zodiacs[i] == z:
                cons += 1
            else:
                break
        consecutive[z] = cons
        
        if len(zodiacs) >= 2:
            last = zodiacs[-1]
            second_last = zodiacs[-2]
            break_state[z] = 1 if (last == z and second_last != z) else 0
    
    # 添加基础统计特征 - 按项目内生肖顺序
    for z in ZODIAC_ALL:
        miss = miss_counts[z]
        max_m = max_miss[z] if max_miss[z] > 0 else 1
        
        features.extend([
            miss,
            miss / max_m,
            recent_10.count(z),
            recent_20.count(z),
            recent_50.count(z),
            recent_10.count(z) / 10,
            recent_20.count(z) / 20,
            ranks[z],
            consecutive[z],
            break_state[z],
        ])
    
    # 动态特征
    prev_zodiac = zodiacs[-1]
    prev_zodiac_id = ZODIAC_ALL.index(prev_zodiac) + 1
    features.append(prev_zodiac_id)
    features.append(0)
    features.append(1)
    features.extend([0, 0, 0, 0, 0, 0])
    
    # 时序特征
    for z in ZODIAC_ALL:
        appear_indices = [i for i, zod in enumerate(zodiacs) if zod == z]
        
        if len(appear_indices) >= 2:
            intervals = [appear_indices[i] - appear_indices[i-1] 
                       for i in range(1, len(appear_indices))]
            interval_mean = np.mean(intervals[-5:])
            interval_std = np.std(intervals[-5:]) if len(intervals) >= 5 else 0
        else:
            interval_mean = 0
            interval_std = 0
        
        features.extend([interval_mean, interval_std, 0])
    
    return features

# ==================== 旧API端点 (保持向后兼容) ====================

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查端点"""
    return jsonify({'status': 'ok', 'message': 'API is running'})

@app.route('/api/predict', methods=['POST'])
def predict():
    """预测下一期生肖 - 旧格式"""
    try:
        # 加载模型
        load_model_once()
        if model is None:
            return jsonify({'error': '模型加载失败'}), 500
        
        # 获取请求数据
        data = request.get_json()
        
        # 优先使用前端传递的历史数据
        if data and 'history' in data and data['history']:
            # 处理前端传递的历史数据
            history_data = data['history']
            
            # 转换数据格式
            periods = []
            zodiacs = []
            
            for item in history_data:
                if 'period' in item and 'zodiac' in item:
                    # 处理前端传递的生肖名称，转换为数字
                    zodiac_name = item['zodiac']
                    # 反向映射：生肖名称到数字
                    zodiac_num = None
                    for num, name in ZODIAC_MAP.items():
                        if name == zodiac_name:
                            zodiac_num = num
                            break
                    
                    if zodiac_num:
                        periods.append(item['period'])
                        zodiacs.append(zodiac_num)
            
            # 创建DataFrame
            if periods and zodiacs:
                df = pd.DataFrame({'period': periods, 'zodiac': zodiacs})
                # 按期号排序
                df = df.sort_values('period').reset_index(drop=True)
                print(f"使用前端传递的历史数据: {len(df)} 条记录")
            else:
                # 前端数据无效，使用本地数据
                df = get_history_data()
                if df is None:
                    return jsonify({'error': '无法读取历史数据'}), 500
        else:
            # 没有前端数据，使用本地数据
            df = get_history_data()
            if df is None:
                return jsonify({'error': '无法读取历史数据'}), 500
        
        # 预测下一期
        if len(df) == 0:
            return jsonify({'error': '历史数据为空'}), 400
        
        # 检查数据量是否足够
        if len(df) < 50:
            # 数据量不足，使用本地数据作为补充
            local_df = get_history_data()
            if local_df is not None and len(local_df) > len(df):
                df = local_df
                print(f"数据量不足，使用本地数据: {len(df)} 条记录")
        
        last_row = df.iloc[-1]
        predictions = predict_next(model, last_row, df)
        
        # 生肖元素和颜色映射
        zodiac_element_map = {
            1: '火', 2: '火', 3: '土', 4: '木', 5: '木', 6: '土',
            7: '水', 8: '水', 9: '土', 10: '金', 11: '金', 12: '土'
        }
        
        zodiac_color_map = {
            1: '红', 2: '红', 3: '绿', 4: '绿', 5: '绿', 6: '蓝',
            7: '蓝', 8: '蓝', 9: '红', 10: '红', 11: '红', 12: '绿'
        }
        
        # 格式化结果
        results = []
        for i, prob in enumerate(predictions):
            zodiac_num = i + 1
            results.append({
                'name': ZODIAC_MAP.get(zodiac_num, f'未知{zodiac_num}'),
                'number': zodiac_num,
                'probability': float(prob),
                'element': zodiac_element_map.get(zodiac_num, ''),
                'color': zodiac_color_map.get(zodiac_num, '')
            })
        
        # 按概率排序
        results.sort(key=lambda x: x['probability'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'predictions': results,
            'top3': results[:3],
            'recommendation': results[0] if results else None
        })
        
    except Exception as e:
        print(f"预测失败: {str(e)}")
        return jsonify({'error': '预测过程中发生错误'}), 500

@app.route('/api/zodiac-mapping', methods=['GET'])
def zodiac_mapping():
    """生肖映射表 - 旧格式"""
    return jsonify({'zodiacs': ZODIAC_MAP})

# ==================== 新API端点 (ml-api格式) ====================

@app.route('/ml-api/api/health', methods=['GET'])
def ml_api_health():
    """健康检查端点 - ml-api格式"""
    return jsonify({'status': 'ok', 'model_loaded': model is not None})

@app.route('/ml-api/api/zodiac-mapping', methods=['GET'])
def ml_api_zodiac_mapping():
    """生肖映射表 - ml-api格式"""
    return jsonify({
        "success": True, 
        "mapping": ZODIAC_CONFIG['id_to_name'],
        "order": ZODIAC_ALL
    })

@app.route('/ml-api/api/predict', methods=['POST'])
def ml_api_predict():
    """预测下一期生肖 - ml-api格式"""
    try:
        # 加载模型
        load_model_once()
        if model is None:
            return jsonify({"error": "模型未加载"})
        
        # 获取请求数据
        data = request.get_json()
        history_data = data.get('history', [])
        
        # 检查数据量
        if len(history_data) < 50:
            # 数据量不足，使用本地数据
            df = get_history_data()
            if df is None or len(df) < 50:
                return jsonify({"error": "历史数据不足，需要至少50期"})
            
            # 转换DataFrame为history_data格式
            history_data = []
            for _, row in df.iterrows():
                history_data.append({
                    'period': int(row['period']),
                    'zodiac': ZODIAC_CONFIG['id_to_name'].get(int(row['zodiac']), '鼠')
                })
        
        # 构建特征
        features = build_features_from_history(history_data)
        
        # 预测概率
        probabilities = model.predict_proba([features])[0]
        
        # 排序结果 - 动态使用模型返回的类别
        results = []
        num_classes = len(probabilities)
        
        for i in range(num_classes):
            # 模型返回的类别标签可能是从0开始或从1开始的
            # 我们需要根据模型的classes_属性来确定
            if hasattr(model, 'classes_'):
                zodiac_id = int(model.classes_[i])
            else:
                zodiac_id = i + 1  # 默认从1开始
            
            # 确保zodiac_id在有效范围内
            if 1 <= zodiac_id <= 12:
                zodiac_name = ZODIAC_CONFIG['id_to_name'][zodiac_id]
                results.append({
                    "id": zodiac_id,
                    "name": zodiac_name,
                    "element": ZODIAC_CONFIG['zodiac_to_element'][zodiac_name],
                    "color": ZODIAC_CONFIG['zodiac_to_color'][zodiac_name],
                    "probability": round(float(probabilities[i]), 4)
                })
        
        # 按概率排序
        results.sort(key=lambda x: x['probability'], reverse=True)
        
        return jsonify({
            "success": True,
            "predictions": results,
            "top3": results[:3],
            "recommendation": results[0]
        })
        
    except Exception as e:
        print(f"ML预测失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"预测过程中发生错误: {str(e)}"})

# 缓存前端文件内容
cached_frontend_files = {}

@app.route('/', methods=['GET'])
def index():
    """根路径，返回前端页面"""
    try:
        # 检查缓存
        if 'index.html' in cached_frontend_files:
            return cached_frontend_files['index.html']
        
        # 读取根目录下的index.html文件
        html_path = os.path.join(os.path.dirname(__file__), '..', 'index.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 缓存文件内容
        cached_frontend_files['index.html'] = html_content
        return html_content
    except Exception as e:
        logger.error(f"读取前端文件失败: {str(e)}")
        return jsonify({'error': '无法加载前端页面'}), 500

@app.route('/style.css', methods=['GET'])
def style_css():
    """返回前端样式文件"""
    try:
        # 检查缓存
        if 'style.css' in cached_frontend_files:
            return cached_frontend_files['style.css']
        
        # 读取根目录下的style.css文件
        css_path = os.path.join(os.path.dirname(__file__), '..', 'style.css')
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # 缓存文件内容
        cached_frontend_files['style.css'] = (css_content, 200, {'Content-Type': 'text/css'})
        return css_content, 200, {'Content-Type': 'text/css'}
    except Exception as e:
        logger.error(f"读取样式文件失败: {str(e)}")
        return jsonify({'error': '无法加载样式文件'}), 500

# 应用入口点
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)
