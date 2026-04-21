import pandas as pd
import os

# 测试本地CSV文件读取
data_path = os.path.join(os.path.dirname(__file__), 'data', 'lottery_history.csv')
df = pd.read_csv(data_path)

# 筛选2025年的数据
year = '2025'
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

print(f"Found {len(data_list)} records for year {year}")
if data_list:
    print("First 5 records:")
    for i, item in enumerate(data_list[:5]):
        print(f"{i+1}. {item}")
else:
    print("No records found")

# 检查CSV文件的前几行
print("\nFirst 10 lines of CSV:")
with open(data_path, 'r') as f:
    for i, line in enumerate(f):
        if i < 10:
            print(f"{i+1}: {line.strip()}")
