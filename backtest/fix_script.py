#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复upgraded.py文件中的错误，将卖出点位Y坐标从time_col修改为price_col
"""

import os
import re

def fix_file():
    # 文件路径
    file_path = 'upgraded.py'
    
    # 确保文件存在
    if not os.path.exists(file_path):
        print(f"错误: 找不到文件 {file_path}")
        return False
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 定义正则表达式模式，匹配y=sell_trades[time_col]
    pattern = r'y=sell_trades\[time_col\]'
    replacement = r'y=sell_trades[price_col]'
    
    # 执行替换并计算替换次数
    new_content, count = re.subn(pattern, replacement, content)
    
    if count == 0:
        print("未找到需要修复的内容")
        return False
    
    # 写入修改后的内容
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print(f"成功修复 {count} 处错误")
    return True

if __name__ == "__main__":
    fix_file() 