#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取ML预测历史"""

import os
import json
import time
from datetime import datetime

def get_ml_prediction_history():
    """从localStorage文件中读取ML预测历史"""
    # 注意：在实际环境中，localStorage存储在浏览器中
    # 这里我们模拟从前端存储的结构中读取
    
    # 检查是否存在模拟的localStorage文件
    localStorage_path = 'localStorage.json'
    
    if not os.path.exists(localStorage_path):
        print("未找到localStorage文件，正在创建模拟数据...")
        # 创建模拟数据
        mock_history = []
        
        # 模拟最近的5条预测记录
        for i in range(5):
            timestamp = int(time.time() * 1000) - (i * 86400000)  # 每天一条
            mock_history.append({
                "id": timestamp,
                "expect": f"09{6+i}",
                "timestamp": timestamp,
                "time": datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S'),
                "type": "ml",
                "predictions": [
                    {"id": 6, "name": "牛", "probability": 0.1282},
                    {"id": 11, "name": "猴", "probability": 0.1203},
                    {"id": 9, "name": "狗", "probability": 0.1167}
                ],
                "top3": [
                    {"id": 6, "name": "牛", "probability": 0.1282},
                    {"id": 11, "name": "猴", "probability": 0.1203},
                    {"id": 9, "name": "狗", "probability": 0.1167}
                ],
                "recommendation": {"id": 6, "name": "牛", "probability": 0.1282},
                "status": "PENDING",
                "actualZodiac": None,
                "actualNumber": None,
                "isHit": None
            })
        
        # 保存模拟数据
        with open(localStorage_path, 'w', encoding='utf-8') as f:
            json.dump({'mlPredictionHistory': mock_history}, f, ensure_ascii=False, indent=2)
        
        print("已创建模拟数据")
    
    # 读取localStorage数据
    with open(localStorage_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('mlPredictionHistory', [])

def display_ml_prediction_history(history):
    """展示ML预测历史"""
    if not history:
        print("暂无ML预测历史记录")
        return
    
    print("=" * 80)
    print("ML预测历史")
    print("=" * 80)
    
    for i, record in enumerate(history, 1):
        print(f"\n#{i} 预测时间: {record['time']}")
        print(f"预测期号: {record['expect']}")
        print(f"推荐生肖: {record['recommendation']['name']} (概率: {record['recommendation']['probability']:.4f})")
        print("Top 3 预测:")
        for j, pred in enumerate(record['top3'], 1):
            print(f"  {j}. {pred['name']} (概率: {pred['probability']:.4f})")
        print(f"状态: {record['status']}")
        if record['actualZodiac']:
            print(f"实际生肖: {record['actualZodiac']}")
            print(f"是否命中: {'✓' if record['isHit'] else '✗'}")
        print("-" * 80)

if __name__ == "__main__":
    history = get_ml_prediction_history()
    display_ml_prediction_history(history)
