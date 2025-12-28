#!/usr/bin/env python3
# 用于修复OKX转换函数顺序问题的脚本

import re

# 获取转换函数的源代码
def get_convert_function_source():
    return '''
# --- 函数：将OKX交易对格式转换为币安API可接受的格式 ---
def convert_okx_symbol_to_binance(okx_symbol):
    """
    将OKX交易对格式转换为币安API可接受的格式
    
    Args:
        okx_symbol (str): OKX格式的交易对，如 "BTC-USDT-SWAP", "BTC-USDT", "ETH-USD-SWAP"
        
    Returns:
        str: 币安格式的交易对，如 "BTCUSDT", "ETHUSDT"
    """
    try:
        # 移除所有空格
        symbol = okx_symbol.strip().upper()
        
        # 存储原始符号供日志使用
        original_symbol = symbol
        
        # 基本清理
        symbol = symbol.replace("-", "").replace("_", "")
        
        # 处理特殊情况: 永续合约和交割合约
        if "SWAP" in symbol:
            # 移除SWAP和任何日期标记
            symbol = re.sub(r'SWAP.*$', '', symbol)
        elif re.search(r'[0-9]{6,}', symbol):  # 包含日期的交割合约
            # 移除日期部分 (通常是6-8位数字)
            symbol = re.sub(r'[0-9]{6,}.*$', '', symbol)
        
        # 处理币本位合约 (USD而非USDT结尾)
        if symbol.endswith("USD") and not symbol.endswith("USDT"):
            symbol = symbol[:-3] + "USDT"  # 将USD替换为USDT
        
        # 确保交易对有合理的长度
        if len(symbol) < 5:  # 太短可能表示格式问题
            st.warning(f"交易对格式可能有问题: {original_symbol} -> {symbol}, 尝试修复...")
            # 尝试推断交易对
            if symbol.startswith("BTC"):
                symbol = "BTCUSDT"
            elif symbol.startswith("ETH"):
                symbol = "ETHUSDT"
            else:
                # 默认添加USDT如果缺少计价货币
                symbol = symbol + "USDT"
        
        # 记录转换信息
        if symbol != original_symbol:
            st.info(f"已将OKX交易对 {original_symbol} 转换为币安格式 {symbol}")
        
        return symbol
    
    except Exception as e:
        st.warning(f"转换交易对格式时出错: {str(e)}，尝试使用默认格式BTCUSDT")
        return "BTCUSDT"
'''

# 读取原文件
file_path = 'upgraded.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找safe_to_decimal函数的位置
safe_to_decimal_pattern = r'def safe_to_decimal\(x\):\s*""".*?return Decimal\(0\)\s*# 转换失败返回0'
safe_to_decimal_match = re.search(safe_to_decimal_pattern, content, re.DOTALL)

# 查找fetch_historical_klines函数的位置
fetch_klines_pattern = r'# --- 获取币安历史K线数据 ---\s*\ndef fetch_historical_klines'
fetch_klines_match = re.search(fetch_klines_pattern, content)

# 查找convert_okx_symbol_to_binance函数的位置
convert_pattern = r'def convert_okx_symbol_to_binance\(okx_symbol\):'
convert_func_match = re.search(convert_pattern, content)

# 打印匹配结果
print(f"safe_to_decimal 函数匹配: {safe_to_decimal_match is not None}")
print(f"fetch_historical_klines 函数匹配: {fetch_klines_match is not None}")
print(f"convert_okx_symbol_to_binance 函数匹配: {convert_func_match is not None}")

# 确保找到了所需的函数
if safe_to_decimal_match and fetch_klines_match:
    # 如果找到了原来的转换函数，我们需要它的完整定义来删除
    if convert_func_match:
        # 找到函数的开始位置
        convert_start = convert_func_match.start()
        
        # 查找函数的结束位置 - 寻找下一个def或文件结束
        next_def_pattern = r'(\n# ---|\ndef )'
        next_def_match = re.search(next_def_pattern, content[convert_start + 20:])
        
        if next_def_match:
            convert_end = convert_start + 20 + next_def_match.start()
        else:
            convert_end = len(content)
        
        # 获取完整函数文本用于确认
        convert_full_text = content[convert_start:convert_end]
        print(f"找到转换函数，长度: {len(convert_full_text)} 字符")
        
        # 在safe_to_decimal之后插入转换函数
        insert_pos = safe_to_decimal_match.end() + 1  # +1 to skip the last line's newline
        
        # 构建新内容
        new_content = content[:insert_pos] + "\n" + get_convert_function_source() + "\n" + content[insert_pos:convert_start] + content[convert_end:]
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("成功修复了convert_okx_symbol_to_binance函数的位置！")
    else:
        # 如果没找到原来的函数，只需要添加就可以了
        insert_pos = safe_to_decimal_match.end() + 1
        new_content = content[:insert_pos] + "\n" + get_convert_function_source() + "\n" + content[insert_pos:]
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("已添加convert_okx_symbol_to_binance函数！")
else:
    print("未找到必要的函数位置，无法完成修复。") 