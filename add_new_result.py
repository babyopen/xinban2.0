import pandas as pd
import os

# 读取 CSV 文件
data_path = 'data/lottery_history.csv'
df = pd.read_csv(data_path)

# 创建新的开奖记录
new_record = {
    'period': 2026111,
    'zodiac': 1,  # 马对应的 ID
    'openCode': '01,13,25,37,49,02,03',  # 假设完整的开奖号码
    'wave': 'red,green,blue,green,green,red,blue',  # 假设波色
    'timestamp': '2026-04-21 21:32:32',  # 假设开奖时间
    'fetch_time': '2026-04-21 21:32:32'  # 假设抓取时间
}

# 将新记录添加到 DataFrame 的最前面
new_df = pd.DataFrame([new_record])
df = pd.concat([new_df, df], ignore_index=True)

# 保存回 CSV 文件
df.to_csv(data_path, index=False)

print('添加成功！')
print('新记录:', new_record)
print('最新几期数据:')
print(df[df['period'] >= 2026110].head())
