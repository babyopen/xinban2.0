#!/bin/bash

# 生成50期模拟历史数据
ZODIAC_ALL=('鼠' '牛' '虎' '兔' '龙' '蛇' '马' '羊' '猴' '鸡' '狗' '猪')
HISTORY="["
for i in {1..50}; do
  zodiac=${ZODIAC_ALL[$((RANDOM % 12))]}
  HISTORY+="{\"zodiac\": \"$zodiac\"}"
  if [ $i -lt 50 ]; then
    HISTORY+","
  fi
done
HISTORY+"]"

# 发送预测请求
result=$(curl -s -X POST http://localhost:5001/api/predict -H "Content-Type: application/json" -d "{\"history\": $HISTORY}")

# 显示结果
echo "预测结果:"
echo "----------------------------------------"
echo "$result"
echo "----------------------------------------"
