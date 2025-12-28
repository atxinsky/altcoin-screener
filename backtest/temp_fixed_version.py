# 将此代码块插入到 upgraded.py 文件中
# 插入位置：在 safe_to_decimal 函数之后，fetch_historical_klines 函数之前

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
        elif re.search(r'\d{6,}', symbol):  # 包含日期的交割合约
            # 移除日期部分 (通常是6-8位数字)
            symbol = re.sub(r'\d{6,}.*$', '', symbol)
        
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

# 然后需要删除在文件底部（约2396行）的相同函数定义 