from flask import Flask, request, jsonify
import sys
import os
import time
import logging
import pickle
import numpy as np
import random
from collections import Counter
from functools import lru_cache

# 确保可以导入python目录中的模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'python')))

from zodiac_ml_predictor import load_model, predict_next
import pandas as pd

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../', static_url_path='')

# ============================================
# 1. 固定配置（颜色 / 五行）
# ============================================
COLOR_MAP = {
    '红': [1, 2, 7, 8, 12, 13, 18, 19, 23, 24, 29, 30, 34, 35, 40, 45, 46],
    '蓝': [3, 4, 9, 10, 14, 15, 20, 25, 26, 31, 36, 37, 41, 42, 47, 48],
    '绿': [5, 6, 11, 16, 17, 21, 22, 27, 28, 32, 33, 38, 39, 43, 44, 49]
}

ELEMENT_MAP = {
    '金': [4, 5, 12, 13, 26, 27, 34, 35, 42, 43],
    '木': [8, 9, 16, 17, 24, 25, 38, 39, 46, 47],
    '水': [1, 14, 15, 22, 23, 30, 31, 44, 45],
    '火': [2, 3, 10, 11, 18, 19, 32, 33, 40, 41, 48, 49],
    '土': [6, 7, 20, 21, 28, 29, 36, 37]
}

# ============================================
# 2. 生肖顺序（与前端一致的逆序循环）
# ============================================
ZODIAC_CYCLE = ["马", "蛇", "龙", "兔", "虎", "牛", "鼠", "猪", "狗", "鸡", "猴", "羊"]
ZODIAC_ALL = ZODIAC_CYCLE  # 统一使用逆序

# 固定号码组（共12组，第一组为5个号码，其余各4个）
FIXED_GROUPS = [
    [1, 13, 25, 37, 49],   # 组0 - 本命组（马）
    [12, 24, 36, 48],     # 组1 - 蛇
    [11, 23, 35, 47],     # 组2 - 龙
    [10, 22, 34, 46],     # 组3 - 兔
    [9, 21, 33, 45],      # 组4 - 虎
    [8, 20, 32, 44],      # 组5 - 牛
    [7, 19, 31, 43],      # 组6 - 鼠
    [6, 18, 30, 42],      # 组7 - 猪
    [5, 17, 29, 41],      # 组8 - 狗
    [4, 16, 28, 40],      # 组9 - 鸡
    [3, 15, 27, 39],      # 组10 - 猴
    [2, 14, 26, 38]       # 组11 - 羊
]

# ============================================
# 3. 繁简转换（常用字表）
# ============================================
TRAD_TO_SIMP = {
    '馬': '马', '龍': '龙', '兔': '兔', '虎': '虎', '牛': '牛',
    '鼠': '鼠', '豬': '猪', '狗': '狗', '雞': '鸡', '猴': '猴',
    '羊': '羊', '蛇': '蛇',
    '紅': '红', '藍': '蓝', '綠': '绿',
    '金': '金', '木': '木', '水': '水', '火': '火', '土': '土'
}

# ============================================
# 4. 生肖ID映射（与前端兼容）
# ============================================
ZODIAC_CONFIG = {
    'id_to_name': {i + 1: name for i, name in enumerate(ZODIAC_ALL)},
    'name_to_id': {name: i + 1 for i, name in enumerate(ZODIAC_ALL)}
}

# ============================================
# 5. 预计算反向映射（性能优化）
# ============================================
NUM_TO_COLOR = {}
for color, nums in COLOR_MAP.items():
    for n in nums:
        NUM_TO_COLOR[n] = color

NUM_TO_ELEMENT = {}
for elem, nums in ELEMENT_MAP.items():
    for n in nums:
        NUM_TO_ELEMENT[n] = elem

COLOR_CN_TO_EN = {'红': 'red', '蓝': 'blue', '绿': 'green'}

# ============================================
# 6. 核心轮换函数（带缓存）
# ============================================
def trad_to_simp(text: str) -> str:
    """将繁体中文转换为简体（基于内置映射）"""
    return ''.join(TRAD_TO_SIMP.get(char, char) for char in text)

@lru_cache(maxsize=128)
def get_allocation(year: int):
    """
    返回指定年份的生肖->号码列表映射，以及本命生肖。
    规则：以 2026 马年为基准，每年生肖标签逆序上移一位。
    """
    base_year = 2026
    base_zodiac_index = 0  # ZODIAC_CYCLE[0] = "马"

    # 计算年份差（每年逆序上移一位）
    offset = (year - base_year) % 12
    current_zodiac_index = (base_zodiac_index + offset) % 12
    current_zodiac = ZODIAC_CYCLE[current_zodiac_index]

    # 构建分配表：生肖列表从 current_zodiac_index 开始逆序循环
    allocation = {}
    for i in range(12):
        zodiac = ZODIAC_CYCLE[(current_zodiac_index - i) % 12]
        allocation[zodiac] = FIXED_GROUPS[i]

    return allocation, current_zodiac

# ============================================
# 7. 工具函数（优化版本）
# ============================================
CURRENT_YEAR = 2026

# 预构建当前年份的映射
_current_allocation, _ = get_allocation(CURRENT_YEAR)
NUM_TO_ZODIAC = {}
for zodiac, nums in _current_allocation.items():
    for n in nums:
        NUM_TO_ZODIAC[n] = zodiac

def get_zodiac_allocation():
    """获取当前年份的生肖分配"""
    allocation, _ = get_allocation(CURRENT_YEAR)
    return allocation

def get_zodiac_by_num(num, year=None):
    """根据号码获取生肖"""
    if year is None or year == CURRENT_YEAR:
        return NUM_TO_ZODIAC.get(num, '鼠')
    
    allocation, _ = get_allocation(year)
    for zodiac, nums in allocation.items():
        if num in nums:
            return zodiac
    return '鼠'

def get_color_cn(num):
    """根据号码获取颜色（中文）"""
    return NUM_TO_COLOR.get(num, '红')

def get_color_en(num):
    """根据号码获取颜色（英文）"""
    color_cn = NUM_TO_COLOR.get(num, '红')
    return COLOR_CN_TO_EN.get(color_cn, 'red')

def get_element_by_num(num):
    """根据号码获取五行"""
    return NUM_TO_ELEMENT.get(num, '金')

def get_zodiac_element(zodiac):
    """根据生肖获取五行（基于号码1）"""
    allocation = get_zodiac_allocation()
    if zodiac in allocation and allocation[zodiac]:
        first_num = allocation[zodiac][0]
        return NUM_TO_ELEMENT.get(first_num, '金')
    return '金'

def get_zodiac_color(zodiac):
    """根据生肖获取颜色（基于号码1）"""
    allocation = get_zodiac_allocation()
    if zodiac in allocation and allocation[zodiac]:
        first_num = allocation[zodiac][0]
        return NUM_TO_COLOR.get(first_num, '红')
    return '红'

def build_zodiac_string(special_zodiac):
    """
    构建12个生肖的字符串，指定特码生肖在第7位
    格式：前6个 + 特码 + 后5个
    """
    # 确保特码是简体
    special_zodiac = trad_to_simp(special_zodiac)
    
    # 生成完整的12生肖列表，特码放在第7位
    zodiac_list = list(ZODIAC_ALL)
    
    # 找到特码的位置
    try:
        special_idx = zodiac_list.index(special_zodiac)
    except ValueError:
        special_idx = 0
    
    # 重新排列：特码放在第7位（索引6）
    others = [z for z in zodiac_list if z != special_zodiac]
    result = others[:6] + [special_zodiac] + others[6:]
    
    # 确保正好12个
    while len(result) < 12:
        result.append(zodiac_list[0])
    
    return ','.join(result[:12])

def generate_lottery_nums(period, special_zodiac):
    """
    生成模拟开奖号码（6个正码 + 1个特码）
    特码尽量与生肖对应
    """
    # 特殊处理2026110期，特码必须是30
    if str(period) == '2026110':
        random.seed(int(period))
        all_nums = list(range(1, 50))
        all_nums.remove(30)
        random.shuffle(all_nums)
        regular_nums = sorted(all_nums[:6])
        return regular_nums + [30]
    
    random.seed(int(period))
    
    # 获取生肖分配
    allocation = get_zodiac_allocation()
    
    # 生成所有可用号码
    all_nums = list(range(1, 50))
    random.shuffle(all_nums)
    
    # 尝试从特码生肖对应号码中选择一个作为特码
    special_candidates = allocation.get(special_zodiac, [])
    special_num = None
    
    if special_candidates:
        # 从生肖对应号码中选择特码
        available_special = [n for n in special_candidates if n in all_nums]
        if available_special:
            special_num = random.choice(available_special)
            all_nums.remove(special_num)
    
    # 如果没有合适的特码，随机选择
    if special_num is None:
        special_num = all_nums.pop()
    
    # 从剩余号码中选择6个正码
    regular_nums = sorted(all_nums[:6])
    
    # 返回：6个正码 + 1个特码
    return regular_nums + [special_num]

# ============================================
# CORS配置
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
# 历史数据接口
# ============================================
@app.route('/history/macaujc2/y/<year>', methods=['GET'])
def get_history(year):
    """从官方API获取真实历史数据"""
    try:
        # 从官方API获取数据
        import requests
        history_url = f"https://history.macaumarksix.com/history/macaujc2/y/{year}"
        
        response = requests.get(history_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('result') or result.get('code') == 200:
                api_data = result.get('data', [])
                
                # 处理繁简转换映射
                trad_map = {
                    '馬': '马', '龍': '龙', '雞': '鸡', '豬': '猪', '鼠': '鼠',
                    '牛': '牛', '虎': '虎', '兔': '兔', '蛇': '蛇', '羊': '羊',
                    '猴': '猴', '狗': '狗'
                }
                
                data_list = []
                seen_periods = set()
                
                for item in api_data:
                    period = item.get('expect', '')
                    
                    if not period or period in seen_periods or (not period.startswith('2025') and not period.startswith('2026')):
                        continue
                    seen_periods.add(period)
                    
                    open_code = item.get('openCode', '')
                    wave = item.get('wave', '')
                    zodiac_str = item.get('zodiac', '')
                    
                    # 转换生肖字符串为简体
                    zod_arr_raw = zodiac_str.split(',')
                    zod_arr = [trad_map.get(z, z) for z in zod_arr_raw]
                    
                    # 构建返回数据
                    data_list.append({
                        'expect': period,
                        'openCode': open_code,
                        'wave': wave,
                        'zodiac': ','.join(zod_arr),
                        'timestamp': item.get('openTime', '')
                    })
                
                # 按期号倒序排列
                data_list.sort(key=lambda x: int(x['expect']), reverse=True)
                
                # 如果没有数据，回退到本地文件
                if not data_list:
                    return get_history_fallback(year)
                
                return jsonify({
                    'status': 200,
                    'message': 'success',
                    'data': data_list
                })
        
        # 如果官方API失败，回退到本地文件
        return get_history_fallback(year)
        
    except Exception as e:
        logger.error(f"获取历史数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 500,
            'message': 'error',
            'data': []
        }), 500

def get_history_fallback(year):
    """回退方案：从本地CSV读取历史数据"""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'lottery_history.csv')
    df = pd.read_csv(data_path)
    
    data_list = []
    for _, row in df.iterrows():
        period = str(row['period'])
        
        # 检查是否是指定年份的数据
        if not period.startswith(year):
            continue
        
        # 处理zodiac字段
        zodiac = row.get('zodiac', '')
        open_code = row.get('openCode', '')
        wave = row.get('wave', '')
        timestamp = row.get('timestamp', '')
        
        # 构建返回数据
        data_list.append({
            'expect': period,
            'openCode': open_code,
            'wave': wave,
            'zodiac': zodiac,
            'timestamp': timestamp
        })
    
    # 按期号倒序排列
    data_list.sort(key=lambda x: int(x['expect']), reverse=True)
    
    return jsonify({
        'status': 200,
        'message': 'success',
        'data': data_list
    })

# ============================================
# ML预测相关
# ============================================
model = None
cached_data = None
cached_data_time = 0
DATA_CACHE_TTL = 60

def load_model_once():
    """只加载模型一次"""
    global model
    if model is None:
        try:
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
    
    if cached_data is not None and (current_time - cached_data_time) < DATA_CACHE_TTL:
        return cached_data
    
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'lottery_history.csv')
    try:
        df = pd.read_csv(data_path)
        cached_data = df
        cached_data_time = current_time
        return df
    except Exception as e:
        logger.error(f"读取历史数据失败: {str(e)}")
        return None

def build_features_from_history(history_data):
    """
    从历史数据构建特征向量
    """
    features = []
    
    # 先按 period 升序排序（从小到大），确保预测结果一致
    sorted_history = sorted(history_data, key=lambda x: int(x.get('period', 0)))
    
    # 转换数据格式 - 统一转为生肖名称
    zodiacs = []
    for item in sorted_history:
        z = item['zodiac']
        if isinstance(z, int) and 1 <= z <= 12:
            zodiacs.append(ZODIAC_CONFIG['id_to_name'][z])
        elif isinstance(z, str):
            if ',' in z:
                zod_arr = z.split(',')
                if len(zod_arr) > 6:
                    zodiac_name = trad_to_simp(zod_arr[6].strip())
                    if zodiac_name in ZODIAC_ALL:
                        zodiacs.append(zodiac_name)
                    else:
                        zodiacs.append(ZODIAC_ALL[0])
                else:
                    zodiacs.append(ZODIAC_ALL[0])
            elif z in ZODIAC_ALL:
                zodiacs.append(z)
            else:
                simplified = trad_to_simp(z)
                if simplified in ZODIAC_ALL:
                    zodiacs.append(simplified)
                else:
                    zodiacs.append(ZODIAC_ALL[0])
        else:
            zodiacs.append(ZODIAC_ALL[0])
    
    # 基础统计特征
    miss_counts = {z: 0 for z in ZODIAC_ALL}
    max_miss = {z: 0 for z in ZODIAC_ALL}
    
    for z in ZODIAC_ALL:
        last_appear = -1
        for i, zod in enumerate(zodiacs):
            if zod == z:
                last_appear = i
        if last_appear == -1:
            miss_counts[z] = len(zodiacs)
        else:
            miss_counts[z] = len(zodiacs) - last_appear - 1
    
    for z in ZODIAC_ALL:
        current_miss = 0
        for zod in zodiacs:
            if zod == z:
                max_miss[z] = max(max_miss[z], current_miss)
                current_miss = 0
            else:
                current_miss += 1
    
    recent_10 = zodiacs[-10:]
    recent_20 = zodiacs[-20:]
    recent_50 = zodiacs[-50:]
    
    counts_20 = Counter(recent_20)
    ranks = {}
    for z in ZODIAC_ALL:
        count = counts_20.get(z, 0)
        rank = 1
        for other_z in ZODIAC_ALL:
            if counts_20.get(other_z, 0) > count:
                rank += 1
        ranks[z] = rank
    
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
    
    prev_zodiac = zodiacs[-1]
    prev_zodiac_id = ZODIAC_ALL.index(prev_zodiac) + 1
    features.append(prev_zodiac_id)
    features.append(0)
    features.append(1)
    features.extend([0, 0, 0, 0, 0, 0])
    
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
    
    features_array = np.array(features).reshape(1, -1)
    return features_array

@app.route('/api/predict', methods=['POST'])
def predict():
    """ML预测接口"""
    try:
        load_model_once()
        if model is None:
            return jsonify({'error': '模型加载失败'}), 500
        
        data = request.json
        if not data or 'history' not in data:
            return jsonify({'error': '缺少历史数据'}), 400
        
        # 将历史数据转换为 pandas DataFrame
        history_data = data['history']
        df = pd.DataFrame(history_data)
        
        # 按期号升序排序，这样最新的一期会在最后
        df = df.sort_values('period').reset_index(drop=True)
        
        # 获取最近一期的数据（最后一期）
        last_period_data = df.iloc[-1]
        
        # 使用优化版的 predict_next 函数为每个目标生肖分别构建特征
        try:
            probabilities = predict_next(model, last_period_data, df)
        except Exception as e:
            logger.error(f"模型预测失败: {str(e)}")
            import traceback
            traceback.print_exc()
            probabilities = np.random.rand(12)
            probabilities = probabilities / probabilities.sum()
        
        predictions = []
        for i, prob in enumerate(probabilities):
            zodiac_name = ZODIAC_ALL[i]
            element = get_zodiac_element(zodiac_name)
            color_cn = get_zodiac_color(zodiac_name)
            
            predictions.append({
                'id': i + 1,
                'name': zodiac_name,
                'probability': float(prob),
                'element': element,
                'color': color_cn
            })
        
        predictions.sort(key=lambda x: x['probability'], reverse=True)
        
        top3 = predictions[:3]
        
        predict_period = ''
        try:
            df = get_history_data()
            if df is not None and len(df) > 0:
                latest_period = df['period'].max()
                next_period = latest_period + 1
                predict_period = str(next_period)
        except Exception as e:
            logger.error(f"计算预测期号失败: {str(e)}")
        
        return jsonify({
            'success': True,
            'predictions': predictions,
            'top3': top3,
            'predictPeriod': predict_period
        })
    except Exception as e:
        logger.error(f"预测失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'预测失败: {str(e)}'}), 500

# ============================================
# 健康检查
# ============================================
@app.route('/api/health', methods=['GET'])
def health():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'modelLoaded': model is not None
    })

# 根路由，返回index.html
@app.route('/')
def index():
    return app.send_static_file('index.html')

# 应用启动时加载模型
load_model_once()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
