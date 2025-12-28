# upgraded_app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, timedelta, date
import streamlit.components.v1 as components
from order_panel_component import generate_trade_statistics, display_trade_statistics
import re
from decimal import Decimal, InvalidOperation, getcontext
from collections import defaultdict
import math
import json
import base64

# Optional: Set higher precision for Decimal context if calculations require it
# getcontext().prec = 28

# --- Helper Functions ---

def parse_value_currency(value_str):
    """Parses string like '404.89HIVE' or '-0.001BTC' into (Decimal, currency_symbol)."""
    if not isinstance(value_str, str):
        if isinstance(value_str, (int, float)) or isinstance(value_str, Decimal):
             return Decimal(value_str), None
        return Decimal(0), None
    value_str = value_str.strip()
    if not value_str: return Decimal(0), None
    match = re.match(r"^\s*(-?[\d\.E\+\-e]+)\s*([A-Z]+)\s*$", value_str, re.IGNORECASE)
    if match:
        num_str, currency = match.groups()
        try: return Decimal(num_str), currency.upper()
        except InvalidOperation: print(f"Warning: Could not parse numeric part of value: {value_str}"); return Decimal(0), None
        except Exception as e: print(f"Warning: Unexpected error parsing value '{value_str}': {e}"); return Decimal(0), None
    else:
        try:
            value = Decimal(value_str)
            if re.fullmatch(r"^\s*-?[\d\.E\+\-e]+\s*$", value_str, re.IGNORECASE): return value, None
            else: print(f"Warning: Could not parse value string or identify currency: {value_str}"); return Decimal(0), None
        except InvalidOperation: print(f"Warning: Could not parse value string as number: {value_str}"); return Decimal(0), None
        except Exception as e: print(f"Warning: Unexpected error parsing value '{value_str}': {e}"); return Decimal(0), None

def safe_to_decimal(x):
    """更安全地将输入转换为Decimal，处理各种潜在错误。"""
    if pd.isna(x): 
        return Decimal(0)
    
    try:
        # 如果是字符串，先尝试清理可能的问题字符
        if isinstance(x, str):
            # 移除所有可能导致问题的非数字字符（保留负号和小数点）
            x = re.sub(r'[^\d\-\.]', '', x)
            if not x or x in ['-', '.']: 
                return Decimal(0)
        
        # 转换前确保是字符串格式
        return Decimal(str(x))
    except (InvalidOperation, ValueError, TypeError, Exception) as e:
        print(f"警告: 无法将'{x}'转换为Decimal: {str(e)}")
        return Decimal(0)  # 转换失败返回0

# --- New Function to Calculate PnL based on FIFO matching ---
def calculate_pnl_from_trades(trades_df):
    """
    根据交易记录计算盈亏（使用FIFO匹配方法）
    
    Args:
        trades_df (pd.DataFrame): 包含交易记录的DataFrame，必须含有symbol, timestamp, side, price, qty, amount列
        
    Returns:
        pd.DataFrame: 添加了pnl列的原始DataFrame
    """
    if trades_df.empty:
        return trades_df
    
    # 确保必要列存在
    required_cols = ['symbol', 'timestamp', 'side', 'price', 'qty', 'amount']
    if not all(col in trades_df.columns for col in required_cols):
        st.error(f"计算PnL所需的列不完整。需要: {required_cols}")
        return trades_df
    
    # 创建结果DataFrame的副本
    result_df = trades_df.copy()
    result_df['pnl'] = Decimal(0)
    
    # 按照交易对分组处理
    symbols = result_df['symbol'].unique()
    
    for symbol in symbols:
        # 获取当前交易对的所有交易，按时间排序
        symbol_trades = result_df[result_df['symbol'] == symbol].sort_values('timestamp').copy()
        
        # 初始化买入库存队列 (FIFO)
        buy_queue = []
        
        # 遍历交易记录
        for idx, trade in symbol_trades.iterrows():
            side = trade['side'].upper()
            price = safe_to_decimal(trade['price'])
            qty = safe_to_decimal(trade['qty'])
            amount = safe_to_decimal(trade['amount'])
            
            if side == 'BUY':
                # 买入交易: 加入库存队列，PnL暂记为成本的负值
                buy_queue.append({
                    'price': price,
                    'qty': qty,
                    'amount': amount,
                    'idx': idx
                })
                result_df.at[idx, 'pnl'] = -amount  # 买入成本记为负PnL
                
            elif side == 'SELL':
                # 卖出交易: 与之前的买入匹配计算盈亏
                remaining_qty = qty
                sell_amount = amount
                sell_pnl = Decimal(0)
                
                # 继续匹配直到卖出数量用完或买入队列为空
                while remaining_qty > 0 and buy_queue:
                    oldest_buy = buy_queue[0]
                    match_qty = min(remaining_qty, oldest_buy['qty'])
                    
                    # 计算此次匹配的买入成本部分
                    match_ratio = match_qty / oldest_buy['qty']
                    match_cost = oldest_buy['amount'] * match_ratio
                    
                    # 计算此次匹配的卖出收入部分
                    match_income = sell_amount * (match_qty / qty)
                    
                    # 累计盈亏 (卖出收入 - 买入成本)
                    match_pnl = match_income - match_cost
                    sell_pnl += match_pnl
                    
                    # 更新剩余数量
                    remaining_qty -= match_qty
                    
                    # 更新或移除买入记录
                    if match_qty == oldest_buy['qty']:
                        buy_queue.pop(0)  # 完全匹配，移除
                    else:
                        # 部分匹配，更新剩余
                        oldest_buy['qty'] -= match_qty
                        oldest_buy['amount'] -= match_cost
                        buy_queue[0] = oldest_buy
                
                # 记录卖出交易的盈亏
                result_df.at[idx, 'pnl'] = sell_pnl
            
            # 其他类型交易(如FEE_OUT)保持pnl为0或直接使用amount作为pnl
            elif side == 'FEE_OUT':
                result_df.at[idx, 'pnl'] = -amount  # 手续费支出视为负盈亏
    
    # 计算USDT的盈亏副本
    result_df['pnl_usdt'] = result_df['pnl'].copy()
    
    # 处理币本位合约的USDT盈亏转换（如果能识别）
    if 'is_coin_margined' in result_df.columns:
        coin_margined_mask = result_df['is_coin_margined'] == True
        if not result_df[coin_margined_mask].empty:
            for idx, row in result_df[coin_margined_mask].iterrows():
                if pd.notna(row['price']) and pd.notna(row['pnl']):
                    result_df.at[idx, 'pnl_usdt'] = row['pnl'] * row['price']
                    
    return result_df
    
    # --- create_ohlc_data Function (Based on user data) ---
def create_ohlc_data(df, timeframe='D'):
    """
    从交易数据创建OHLC数据 (确保输入df有datetime索引)

    Args:
        df (pd.DataFrame): Input DataFrame with 'timestamp', 'price', 'qty' columns.
                           'timestamp' should be datetime type.
        timeframe (str): Pandas resampling timeframe string (e.g., 'D', '4H', 'H', '30T').

    Returns:
        pd.DataFrame: OHLCV data with 'timestamp', 'open', 'high', 'low', 'close', 'volume'.
                      Returns empty DataFrame on error.
    """
    try:
        # Ensure required columns exist
        if not all(col in df.columns for col in ['timestamp', 'price', 'qty']):
            st.error("创建OHLC数据所需的列（timestamp, price, qty）不完整。")
            return pd.DataFrame()

        # Ensure timestamp is datetime and set as index
        df = df.copy() # Avoid modifying original DataFrame
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.dropna(subset=['timestamp'], inplace=True)
        if df.empty:
            return pd.DataFrame()
        df.set_index('timestamp', inplace=True)

        # Ensure price and qty are numeric (Decimal preferred, float fallback)
        df['price'] = df['price'].apply(safe_to_decimal)
        df['qty'] = df['qty'].apply(safe_to_decimal)

        # Convert Decimal to float for resampling compatibility
        df['price_float'] = df['price'].astype(float)
        df['qty_float'] = df['qty'].astype(float)

        # Resample to get OHLC - REMOVED numeric_only=True based on error
        ohlc = df['price_float'].resample(timeframe).ohlc()

        # Resample to get Volume (Sum of quantity)
        volume = df['qty_float'].resample(timeframe).sum()

        # Combine OHLC and Volume
        ohlc_data = pd.concat([ohlc, volume], axis=1)
        ohlc_data.columns = ['open', 'high', 'low', 'close', 'volume']

        # Handle potential all-NaN intervals
        ohlc_data.dropna(subset=['open', 'high', 'low', 'close'], how='all', inplace=True)
        ohlc_data.fillna(0, inplace=True)

        # Reset index to make timestamp a column again
        ohlc_data = ohlc_data.reset_index()
        ohlc_data.rename(columns={'index': 'timestamp'}, inplace=True, errors='ignore') # Keep consistent column name

        return ohlc_data

    except Exception as e:
        st.error(f"创建OHLC数据时出错: {e}")
        import traceback
        st.code(traceback.format_exc(), language='python')
        return pd.DataFrame()

# --- Calculate Fee Statistics with Currency Conversion ---
def calculate_fee_statistics(df):
    """
    计算费用统计信息，针对币本位合约将费用转换为USDT计价
    """
    try:
        if df.empty or 'fee' not in df.columns:
            return None
        
        fee_col = 'fee'
        fee_currency_col = 'fee_currency'
        price_col = 'price'
        data_type_col = 'data_type'
        
        # Create a copy to avoid modifying the original dataframe
        df = df.copy()
        
        # Convert fees to Decimal if not already
        df[fee_col] = df[fee_col].apply(safe_to_decimal)
        
        # Create a new column for fee in USDT value
        df['fee_usdt'] = df[fee_col].copy()
        
        # For coin-margined contracts, convert fees to USDT value
        if data_type_col in df.columns:
            coin_margined_mask = df[data_type_col] == '合约' 
            
            if fee_currency_col in df.columns and price_col in df.columns:
                # Convert non-USDT fees to USDT equivalent using the price at trade time
                for idx, row in df[coin_margined_mask].iterrows():
                    if pd.notna(row[fee_currency_col]) and row[fee_currency_col] != 'USDT':
                        # Check if fee currency matches trading pair base currency
                        if row[fee_currency_col] in row['symbol']:
                            df.at[idx, 'fee_usdt'] = row[fee_col] * row[price_col]
        
        # Calculate total fees in USDT
        total_fees_usdt = df['fee_usdt'].sum()
        
        # Calculate original total fees (without conversion)
        total_fees_original = df[fee_col].sum()
        
        # Calculate average fee per trade
        avg_fee_per_trade_usdt = total_fees_usdt / len(df) if len(df) > 0 else Decimal(0)
        
        # Calculate fees by currency (keep original amounts for per-currency breakdown)
        fees_by_currency = None
        if fee_currency_col in df.columns:
            # Group by currency and calculate both original and USDT-converted sums
            currency_groups = df.groupby(fee_currency_col)
            
            # Get original fees by currency
            original_fees = currency_groups[fee_col].sum().reset_index()
            original_fees.columns = ['货币', '原始总费用']
            
            # Get USDT-converted fees by currency
            usdt_fees = currency_groups['fee_usdt'].sum().reset_index()
            usdt_fees.columns = ['货币', 'USDT价值总费用']
            
            # Combine both
            fees_by_currency = pd.merge(original_fees, usdt_fees, on='货币', how='outer')
            fees_by_currency = fees_by_currency.sort_values('USDT价值总费用', ascending=False)
        
        # Calculate fee as percentage of transaction volume if amount column exists
        fee_percentage = None
        if 'amount' in df.columns:
            df['amount'] = df['amount'].apply(safe_to_decimal)
            total_volume = df['amount'].abs().sum()
            fee_percentage = (total_fees_usdt / total_volume * 100) if total_volume > 0 else Decimal(0)
        
        return {
            'total_fees_usdt': total_fees_usdt,
            'total_fees_original': total_fees_original,
            'avg_fee_per_trade_usdt': avg_fee_per_trade_usdt,
            'fees_by_currency': fees_by_currency,
            'fee_percentage': fee_percentage
        }
    except Exception as e:
        st.error(f"计算费用统计时出错: {str(e)}")
        import traceback
        st.code(traceback.format_exc(), language="python")
        return None

# --- Display Fee Statistics ---
def display_fee_statistics(fee_stats, key_prefix="fee_stats"):
    """显示费用统计信息"""
    if not fee_stats:
        st.info("没有足够的费用数据生成统计信息")
        return
    
    st.write("### 费用统计")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("总费用 (USDT价值)", f"{fee_stats['total_fees_usdt']:.8f}")
        if fee_stats['fee_percentage'] is not None:
            st.metric("费用占交易量百分比", f"{fee_stats['fee_percentage']:.4f}%")
    
    with col2:
        st.metric("平均每笔交易费用 (USDT)", f"{fee_stats['avg_fee_per_trade_usdt']:.8f}")
    
    # Display fees by currency if available
    if fee_stats['fees_by_currency'] is not None and not fee_stats['fees_by_currency'].empty:
        st.write("#### 按货币统计费用")
        st.dataframe(fee_stats['fees_by_currency'], use_container_width=True)
        
        
        
        
# --- Helper function to read and embed the HTML chart component ---
def get_chart_component_content():
    """
    Read the chart_component.html file and return its content
    """
    try:
        with open('chart_component.html', 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except Exception as e:
        st.error(f"无法读取图表组件: {str(e)}")
        return None

# --- Order Panel Function ---
def create_order_panel(filtered_trades, symbols=None):
    """
    创建订单面板 (假设输入数据已标准化)
    
    参数:
    filtered_trades (DataFrame): 经过筛选和标准化的交易记录
    symbols (list): 当前选择的交易对列表 (用于筛选)
    """
    if filtered_trades.empty:
        st.info("没有符合条件的交易记录")
        return
    
    # --- 使用标准化的列名 ---
    time_col = 'timestamp'
    symbol_col = 'symbol'
    side_col = 'side'
    price_col = 'price'
    qty_col = 'qty' # 使用处理后的数值数量列
    pnl_col = 'pnl' # 使用处理后的统一PnL列
    amount_col = 'amount' # 使用处理后的数值金额列 (可能是Quote或Base，取决于数据类型)
    base_asset_col = 'base_asset'
    quote_asset_col = 'quote_asset'
    fee_col = 'fee' # 使用处理后的数值费用列
    
    # 检查必需的列是否存在 (pnl_col is checked later as it might be calculated)
    required_cols_check = [time_col, symbol_col, side_col, price_col, qty_col, amount_col, base_asset_col, quote_asset_col, fee_col]
    if not all(col in filtered_trades.columns for col in required_cols_check):
        missing = [col for col in required_cols_check if col not in filtered_trades.columns]
        st.error(f"输入数据缺少必需的标准化列。需要: {required_cols_check}, 实际缺少: {missing}")
        return
    
    # --- 如果指定了symbols，则进一步过滤 ---
    if symbols and len(symbols) == 1 and symbols[0] != "全部":
        symbol_trades = filtered_trades[filtered_trades[symbol_col] == symbols[0]].copy()
        if symbol_trades.empty:
            st.warning(f"未找到交易对 '{symbols[0]}' 的交易记录。")
            return
    else:
        # 多个交易对或全部选项
        symbol_trades = filtered_trades.copy()
    
    # 确保所有数值列都被转换为有效的数字值
    for col in [price_col, qty_col, amount_col, fee_col]:
        if col in symbol_trades.columns:
            # 先进行安全的Decimal转换
            symbol_trades[col] = symbol_trades[col].apply(lambda x: safe_to_decimal(x) if x is not None else Decimal(0))
            
            # 然后转换为pandas可以处理的数值类型并处理任何无效值
            symbol_trades[col] = pd.to_numeric(symbol_trades[col].astype(str), errors='coerce').fillna(0)
    
    # Ensure pnl_col exists and is numeric
    if pnl_col not in symbol_trades.columns:
        st.error(f"必需的 PnL 列 '{pnl_col}' 在过滤后的数据中不存在。")
        return
    
    symbol_trades[pnl_col] = symbol_trades[pnl_col].apply(lambda x: safe_to_decimal(x) if x is not None else Decimal(0))
    symbol_trades[pnl_col] = pd.to_numeric(symbol_trades[pnl_col].astype(str), errors='coerce').fillna(0)
    
    # --- 交易对概览 ---
    st.write("#### 交易对概览")
    try:
        # 检查是否有币本位合约
        has_coin_margined = 'is_coin_margined' in symbol_trades.columns and symbol_trades['is_coin_margined'].any()
        
        # 检查数据来源
        is_okx = 'exchange' in symbol_trades.columns and (symbol_trades['exchange'] == 'OKX').any()
        
        # 调整数量和金额的显示逻辑
        qty_display_col = qty_col
        amount_display_col = amount_col
        
        # 为币本位合约交易正确处理显示
        if has_coin_margined:
            # 创建币本位合约特定的列
            coin_margined_trades = symbol_trades[symbol_trades['is_coin_margined'] == True].copy()
            if not coin_margined_trades.empty:
                # 为币本位合约，正确设置数量和金额
                symbol_trades.loc[symbol_trades['is_coin_margined'] == True, 'qty_display'] = symbol_trades.loc[symbol_trades['is_coin_margined'] == True, amount_col]
                symbol_trades.loc[symbol_trades['is_coin_margined'] == True, 'amount_display'] = symbol_trades.loc[symbol_trades['is_coin_margined'] == True, qty_col]
                
                # 为USDT本位合约和现货，保持原有数据
                symbol_trades.loc[symbol_trades['is_coin_margined'] != True, 'qty_display'] = symbol_trades.loc[symbol_trades['is_coin_margined'] != True, qty_col]
                symbol_trades.loc[symbol_trades['is_coin_margined'] != True, 'amount_display'] = symbol_trades.loc[symbol_trades['is_coin_margined'] != True, amount_col]
                
                # 使用新的显示列
                qty_display_col = 'qty_display'
                amount_display_col = 'amount_display'
            
        # Group by symbol and side
        grouped = symbol_trades.groupby([symbol_col, side_col]).agg(
            总数量=(qty_display_col, 'sum'),
            总盈亏=(pnl_col, 'sum'),
            总盈亏_USDT=('pnl_usdt', 'sum') if 'pnl_usdt' in symbol_trades.columns else (pnl_col, 'sum'),
            交易次数=(time_col, 'count') # Count any non-null column
        ).reset_index()
        
        if not grouped.empty:
            # 确保分组后的数据都是有效的数值
            for col in grouped.columns:
                if col not in [symbol_col, side_col]:
                    grouped[col] = pd.to_numeric(grouped[col], errors='coerce').fillna(0)
            
            # Pivot for better display
            summary = grouped.pivot_table(
                index=symbol_col,
                columns=side_col,
                values=['总数量', '总盈亏', '总盈亏_USDT', '交易次数'],
                aggfunc='sum' # Use sum here, as agg already did the sum within group
            ).reset_index()
            
            # 处理透视表后的列名和数据
            summary.columns = [f"{col[0]}_{col[1]}" if col[1]!='' else col[0] for col in summary.columns]
            summary.fillna(0, inplace=True) # Replace NaN with 0 after pivot
            
            # 确保所有数值列都能被正确解析
            for col in summary.columns:
                if col != symbol_col:
                    summary[col] = pd.to_numeric(summary[col], errors='coerce').fillna(0)
            
            # Add Net PnL (Ensure columns exist before calculation)
            buy_pnl_col = f'总盈亏_BUY'
            sell_pnl_col = f'总盈亏_SELL'
            if sell_pnl_col in summary.columns and buy_pnl_col in summary.columns:
                summary['净盈亏'] = summary[sell_pnl_col] + summary[buy_pnl_col] # BUY PnL is already negative for spot cost
            elif sell_pnl_col in summary.columns:
                summary['净盈亏'] = summary[sell_pnl_col]
            elif buy_pnl_col in summary.columns:
                summary['净盈亏'] = summary[buy_pnl_col] # Should be negative for spot
            else:
                summary['净盈亏'] = 0
                
            # Add Net PnL USDT (for coin-margined contracts)
            buy_pnl_usdt_col = f'总盈亏_USDT_BUY'
            sell_pnl_usdt_col = f'总盈亏_USDT_SELL'
            if sell_pnl_usdt_col in summary.columns and buy_pnl_usdt_col in summary.columns:
                summary['净盈亏_USDT'] = summary[sell_pnl_usdt_col] + summary[buy_pnl_usdt_col]
            elif sell_pnl_usdt_col in summary.columns:
                summary['净盈亏_USDT'] = summary[sell_pnl_usdt_col]
            elif buy_pnl_usdt_col in summary.columns:
                summary['净盈亏_USDT'] = summary[buy_pnl_usdt_col]
            else:
                summary['净盈亏_USDT'] = summary['净盈亏']  # 如果没有USDT列，使用原始盈亏作为默认值
            
            # Add Asset Info (Example using first row of the group)
            # Ensure the columns exist before trying to group and access them
            if base_asset_col in symbol_trades.columns and quote_asset_col in symbol_trades.columns:
                asset_info = symbol_trades.groupby(symbol_col)[[base_asset_col, quote_asset_col]].first().reset_index()
                summary = pd.merge(summary, asset_info, on=symbol_col, how='left')
                base_asset_display_col = base_asset_col
                quote_asset_display_col = quote_asset_col
            else:
                base_asset_display_col = '基础资产' # Placeholder names
                quote_asset_display_col = '计价资产'
                summary[base_asset_display_col] = 'N/A'
                summary[quote_asset_display_col] = 'N/A'
            
            # Reorder and select columns for display
            display_cols_order = [symbol_col, base_asset_display_col, quote_asset_display_col, '净盈亏', '净盈亏_USDT']
            optional_cols = [
                '总数量_BUY', '总数量_SELL', 
                '总盈亏_BUY', '总盈亏_SELL',
                '总盈亏_USDT_BUY', '总盈亏_USDT_SELL',
                '交易次数_BUY', '交易次数_SELL'
            ]
            # Only include optional columns if they exist in the summary dataframe
            display_cols_order.extend([col for col in optional_cols if col in summary.columns])
            
            # Select only the columns that actually exist
            final_display_cols = [col for col in display_cols_order if col in summary.columns]
            
            # 最终显示前再确认一次所有数据类型
            for col in final_display_cols:
                if col not in [symbol_col, base_asset_display_col, quote_asset_display_col] and not pd.api.types.is_numeric_dtype(summary[col]):
                    summary[col] = pd.to_numeric(summary[col], errors='coerce').fillna(0)
            
            st.dataframe(summary[final_display_cols], use_container_width=True)
        else:
            st.info("没有足够的交易数据进行概览。")
    
    except Exception as e:
        st.error(f"创建交易对概览时出错: {str(e)}")
        import traceback
        st.code(traceback.format_exc(), language="python")
    
    
    # --- 如果选择了单个交易对，显示交易点位图表 ---
    if symbols and len(symbols) == 1 and symbols[0] != "全部":
        selected_symbol = symbols[0]
        st.write(f"#### {selected_symbol} 交易点位图表")
        try:
            symbol_data = filtered_trades[filtered_trades[symbol_col] == selected_symbol].copy()
            
            if not symbol_data.empty:
                # 创建基础价格线图
                fig = go.Figure()
                
                # 添加价格线
                fig.add_trace(go.Scatter(
                    x=symbol_data[time_col], 
                    y=symbol_data[price_col],
                    mode='lines',
                    name='价格',
                    line=dict(color='#2962FF', width=1.5)
                ))
                
                # 根据交易方向分组
                buy_trades = symbol_data[symbol_data[side_col].str.upper() == 'BUY']
                sell_trades = symbol_data[symbol_data[side_col].str.upper() == 'SELL']
                
                # 添加买入点标记
                if not buy_trades.empty:
                    hover_texts = buy_trades.apply(
                        lambda row: f"买入 @ {row[price_col]}<br>数量: {row[qty_col]}<br>时间: {pd.to_datetime(row[time_col]).strftime('%Y-%m-%d %H:%M')}<br>盈亏: {row[pnl_col]}", 
                        axis=1
                    )
                    
                    fig.add_trace(go.Scatter(
                        x=buy_trades[time_col],
                        y=buy_trades[price_col],
                        mode='markers',
                        name='买入点',
                        marker=dict(
                            color='green',
                            size=10,
                            symbol='triangle-up'
                        ),
                        text=hover_texts,
                        hoverinfo='text'
                    ))
                
                # 添加卖出点标记
                if not sell_trades.empty:
                    hover_texts = sell_trades.apply(
                        lambda row: f"卖出 @ {row[price_col]}<br>数量: {row[qty_col]}<br>时间: {pd.to_datetime(row[time_col]).strftime('%Y-%m-%d %H:%M')}<br>盈亏: {row[pnl_col]}", 
                        axis=1
                    )
                    
                    fig.add_trace(go.Scatter(
                        x=sell_trades[time_col],
                        y=sell_trades[price_col],
                        mode='markers',
                        name='卖出点',
                        marker=dict(
                            color='red',
                            size=10,
                            symbol='triangle-down'
                        ),
                        text=hover_texts,
                        hoverinfo='text'
                    ))
                
                # 更新图表布局
                fig.update_layout(
                    title=f"{selected_symbol} - 交易点位图表",
                    xaxis_title="时间",
                    yaxis_title="价格",
                    height=600,
                    xaxis_rangeslider_visible=False,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    hovermode="closest"
                )
                
                # 显示图表
                st.plotly_chart(fig, use_container_width=True, key="trade_points_chart")
            else:
                st.warning(f"未找到 {selected_symbol} 的交易数据")
        except Exception as chart_e:
            st.error(f"生成交易点位图表时出错: {str(chart_e)}")
            import traceback
            st.code(traceback.format_exc(), language="python")
            
            
# --- 详细交易记录 ---
    if symbols and len(symbols) == 1 and symbols[0] != "全部":
        selected_symbol = symbols[0]
        st.write(f"#### {selected_symbol} 详细交易记录")
        try:
            # 检查是否有币本位合约
            has_coin_margined = 'is_coin_margined' in symbol_trades.columns and symbol_trades['is_coin_margined'].any()
            
            # 检查数据来源
            is_okx = 'exchange' in symbol_trades.columns and (symbol_trades['exchange'] == 'OKX').any()
            
            # 处理欧易数据的数量和金额显示问题
            if is_okx:
                # 欧易数据处理逻辑，确保数量和金额正确显示
                # 复制原始列以便后续引用
                symbol_trades['qty_orig'] = symbol_trades[qty_col]
                symbol_trades['amount_orig'] = symbol_trades[amount_col]
            
            # 调整数量和金额的显示逻辑
            if has_coin_margined:
                # 创建币本位合约特定的列
                symbol_trades.loc[symbol_trades['is_coin_margined'] == True, 'qty_display'] = symbol_trades.loc[symbol_trades['is_coin_margined'] == True, amount_col]
                symbol_trades.loc[symbol_trades['is_coin_margined'] == True, 'amount_display'] = symbol_trades.loc[symbol_trades['is_coin_margined'] == True, qty_col]
                
                # 为USDT本位合约和现货，保持原有数据
                symbol_trades.loc[symbol_trades['is_coin_margined'] != True, 'qty_display'] = symbol_trades.loc[symbol_trades['is_coin_margined'] != True, qty_col]
                symbol_trades.loc[symbol_trades['is_coin_margined'] != True, 'amount_display'] = symbol_trades.loc[symbol_trades['is_coin_margined'] != True, amount_col]
                
                # 替换原有列
                symbol_trades[qty_col] = symbol_trades['qty_display']
                symbol_trades[amount_col] = symbol_trades['amount_display']
                
            # Select columns for the detailed table
            details_cols = [time_col, side_col, price_col, qty_col, pnl_col, 'pnl_usdt', amount_col, fee_col, 'fee_currency', 'is_coin_margined']
            details_cols_present = [col for col in details_cols if col in symbol_trades.columns]
            details = symbol_trades[details_cols_present].copy()
            
            # Format timestamp
            details[time_col] = pd.to_datetime(details[time_col]).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 确保所有数值列都是有效的数字
            for col in [price_col, qty_col, pnl_col, 'pnl_usdt', amount_col, fee_col]:
                if col in details.columns:
                    details[col] = pd.to_numeric(details[col], errors='coerce').fillna(0)
            
            # Combine Fee and Currency for display
            if 'fee' in details.columns and 'fee_currency' in details.columns:
                details['费用'] = details.apply(lambda row: f"{row['fee']:.8f} {row['fee_currency']}" if pd.notna(row['fee_currency']) else f"{row['fee']:.8f}", axis=1)
            elif 'fee' in details.columns:
                details['费用'] = details['fee'].apply(lambda x: f"{x:.8f}")
            
            # Rename columns for display
            col_mapping = {
                time_col: '时间',
                side_col: '方向',
                price_col: '价格',
                qty_col: '数量',
                pnl_col: '盈亏',
                'pnl_usdt': '盈亏_USDT',
                amount_col: '金额' # This is quote value for spot, base value for futures
            }
            details = details.rename(columns=col_mapping)
            
            # Select final display columns including the new '费用'
            final_details_cols = ['时间', '方向', '价格', '数量', '金额', '费用', '盈亏']
            # 如果存在盈亏_USDT，添加到最终列表中
            if '盈亏_USDT' in details.columns:
                final_details_cols.append('盈亏_USDT')
            final_details_cols_present = [col for col in final_details_cols if col in details.columns]
            details_display = details[final_details_cols_present]
            
            # Sort by time descending
            details_display = details_display.sort_values('时间', ascending=False)
            
            # Apply styling
            def highlight_side(val):
                if val == 'BUY': return 'background-color: rgba(0, 255, 0, 0.2)'
                elif val == 'SELL': return 'background-color: rgba(255, 0, 0, 0.2)'
                return ''
            
            def highlight_pnl(val):
                try:
                    val_num = float(val)
                    if val_num > 0: return 'color: green; font-weight: bold;'
                    elif val_num < 0: return 'color: red; font-weight: bold;'
                    return ''
                except:
                    return ''
            
            # Apply formatting after potential highlights
            styled_details = details_display.style.applymap(highlight_side, subset=['方向'] if '方向' in details_display else None)\
                .applymap(highlight_pnl, subset=['盈亏'] if '盈亏' in details_display else None)\
                .applymap(highlight_pnl, subset=['盈亏_USDT'] if '盈亏_USDT' in details_display else None)\
                .format({ # Apply number formatting
                    '价格': "{:.8f}",
                    '数量': "{:.8f}",
                    '盈亏': "{:.8f}", # Format PnL as well
                    '盈亏_USDT': "{:.8f}",
                    '金额': "{:.8f}"
                }, na_rep='-')
            
            st.dataframe(styled_details, use_container_width=True, height=400) # Add height for scroll
            
            # --- PnL Visualization for the selected symbol ---
            if not details_display.empty and '盈亏' in details_display.columns and '时间' in details_display.columns:
                st.write("#### 盈亏分布")
                fig = go.Figure()
                
                # 确保盈亏值是数值型
                details_display['盈亏_numeric'] = pd.to_numeric(details_display['盈亏'], errors='coerce').fillna(0)
                cumulative_pnl = details_display['盈亏_numeric'].cumsum()
                
                fig.add_trace(go.Scatter(x=details_display['时间'], y=cumulative_pnl, mode='lines+markers', name='累计盈亏', line=dict(color='royalblue', width=2)))
                
                colors = ['green' if pnl >= 0 else 'red' for pnl in details_display['盈亏_numeric']]
                fig.add_trace(go.Bar(x=details_display['时间'], y=details_display['盈亏_numeric'], marker_color=colors, name='交易盈亏'))
                
                fig.update_layout(title=f"{selected_symbol} 盈亏分析", xaxis_title="交易时间", yaxis_title="盈亏", height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig, use_container_width=True, key=f"order_pnl_chart_{selected_symbol}")
        
        except Exception as e:
            st.error(f"创建 {selected_symbol} 详细记录时出错: {str(e)}")
            import traceback
            st.code(traceback.format_exc(), language="python")

# --- Helper function to convert dataframe to JSON for the chart ---
def prepare_chart_data(trade_data):
    """
    Prepare the trade data for the chart component
    Returns JSON string for trade data
    """
    try:
        # Prepare trade data
        if not trade_data.empty:
            trade_json = trade_data.to_dict(orient='records')
            trade_json = [{
                'timestamp': str(item['timestamp']),
                'price': float(item['price']),
                'qty': float(item['qty']),
                'side': item['side'],
                'symbol': item['symbol'],
                'pnl': float(item['pnl']) if 'pnl' in item and pd.notna(item['pnl']) else 0
            } for item in trade_json]
        else:
            trade_json = []
            
        return json.dumps(trade_json)
    except Exception as e:
        st.error(f"准备图表数据时出错: {str(e)}")
        import traceback
        st.code(traceback.format_exc(), language="python")
        return "[]"

# --- 函数：检测文件类型 ---
def detect_file_format(df):
    """
    检测上传文件的格式类型（币安或欧易或新数据格式）
    返回: 'binance', 'okx', 'new_format' 或 'unknown'
    """
    if df is None or df.empty:
        return 'unknown'
    
    # 获取列名
    cols = df.columns.tolist()
    
    # 检查是否为新数据格式
    new_format_columns = ['Date', 'Symbol', 'TradeType', 'Side', 'Price', 'Quantity', 'Amount', 'Fee']
    new_format_match_count = sum(1 for col in new_format_columns if col in cols)
    if new_format_match_count >= 6:  # 如果匹配了大部分新格式列
        return 'new_format'
    
    # 检查是否为欧易格式
    okx_columns = ['Date', 'Symbol', 'Bill Type', 'Side', 'Avg Price', 'Total Quantity', 'Total Fee', 'Total PnL', 'Trade Count']
    okx_match_count = sum(1 for col in okx_columns if col in cols)
    if okx_match_count >= 5:  # 如果匹配了大部分欧易列
        return 'okx'
    
    # 检查是否为币安格式
    binance_columns = ['Time(UTC)', 'Pair', 'Side', 'Price', 'Executed', 'Amount', 'Fee']
    binance_match_count = sum(1 for col in binance_columns if col in cols)
    
    # 也检查币安合约格式
    binance_futures_columns = ['Uid', 'Time(UTC)', 'Symbol', 'Side', 'Position Side', 'Price', 'Quantity', 'Amount', 'Fee', 'Realized Profit']
    binance_futures_match_count = sum(1 for col in binance_futures_columns if col in cols)
    
    if binance_match_count >= 4 or binance_futures_match_count >= 4:
        return 'binance'
    
    return 'unknown'
    # --- 函数：处理新数据格式 ---
def process_new_format_data(df):
    """处理新的CSV数据格式并转换为标准格式"""
    try:
        # 创建标准化的DataFrame
        standard_df = pd.DataFrame()
        
        # 映射列
        column_mappings = {
            'timestamp': 'Date',
            'symbol': 'Symbol',
            'side': 'Side',
            'price': 'Price',
            'qty': 'Quantity',
            'amount': 'Amount',
            'fee': 'Fee',
            'trade_type': 'TradeType'
        }
        
        # 复制所需的列
        for standard_name, df_name in column_mappings.items():
            if df_name in df.columns:
                standard_df[standard_name] = df[df_name]
            else:
                standard_df[standard_name] = None
        
        # 将时间转换为标准格式
        standard_df['timestamp'] = pd.to_datetime(standard_df['timestamp'], errors='coerce')
        standard_df.dropna(subset=['timestamp'], inplace=True)
        
        # 数值处理
        standard_df['price'] = standard_df['price'].apply(safe_to_decimal)
        standard_df['qty'] = standard_df['qty'].apply(safe_to_decimal)
        standard_df['amount'] = standard_df['amount'].apply(safe_to_decimal)
        standard_df['fee'] = standard_df['fee'].apply(safe_to_decimal)
        
        # 添加基础资产和计价资产
        if 'symbol' in standard_df.columns:
            # 从Symbol列提取基础资产和计价资产
            # 假设格式为BTCUSDT或BTC-USDT
            standard_df['base_asset'] = standard_df['symbol'].str.extract(r'^([A-Z0-9]+)[-/]?')
            standard_df['quote_asset'] = standard_df['symbol'].str.extract(r'[-/]?([A-Z0-9]+)$')
        else:
            standard_df['base_asset'] = None
            standard_df['quote_asset'] = None
        
        # 添加费用币种（基于交易类型判断）
        if 'trade_type' in standard_df.columns:
            # 为现货交易基于交易对判断
            standard_df['fee_currency'] = standard_df.apply(
                lambda row: row['quote_asset'] if row['side'].upper() == 'SELL' else row['base_asset'], 
                axis=1
            )
        else:
            standard_df['fee_currency'] = standard_df['base_asset']
        
        # 使用新的PnL计算函数计算盈亏
        standard_df = calculate_pnl_from_trades(standard_df)
        
        # 添加额外信息
        standard_df['exchange'] = 'Unknown'
        standard_df['data_type'] = '现货'  # 默认为现货，后续可根据实际情况修改
        standard_df['is_coin_margined'] = False  # 默认非币本位，后续可根据交易对特征判断
        
        # 选择最终列
        final_cols = [
            'timestamp', 'symbol', 'side', 'price', 'qty', 'amount', 'fee', 'pnl', 
            'pnl_usdt', 'base_asset', 'quote_asset', 'fee_currency', 'exchange', 
            'data_type', 'is_coin_margined'
        ]
        
        final_df_cols = [col for col in final_cols if col in standard_df.columns]
        final_df = standard_df[final_df_cols]
        
        return final_df
    
    except Exception as e:
        st.error(f"处理新格式数据时出错: {str(e)}")
        import traceback
        st.code(traceback.format_exc(), language="python")
        return pd.DataFrame()

# --- 函数：处理欧易数据 ---
def process_okx_data(df):
    """处理欧易CSV数据并转换为标准格式"""
    try:
        # 创建标准化的DataFrame
        standard_df = pd.DataFrame()
        
        # 映射列
        column_mappings = {
            'timestamp': 'Date',
            'symbol': 'Symbol',
            'side': 'Side',
            'price_orig': 'Avg Price',
            'qty_orig': 'Total Quantity',
            'fee_orig': 'Total Fee',
            'realized_pnl_orig': 'Total PnL',
            'trade_count': 'Trade Count',
            'bill_type': 'Bill Type'
        }
        
        # 复制所需的列
        for standard_name, okx_name in column_mappings.items():
            if okx_name in df.columns:
                standard_df[standard_name] = df[okx_name]
            else:
                standard_df[standard_name] = None
        
        # 将时间转换为标准格式
        standard_df['timestamp'] = pd.to_datetime(standard_df['timestamp'], errors='coerce')
        standard_df.dropna(subset=['timestamp'], inplace=True)
        
        # 数值处理
        standard_df['price'] = standard_df['price_orig'].apply(safe_to_decimal)
        
        # 处理数量和基础资产 (Total Quantity 作为数量)
        if 'qty_orig' in standard_df.columns and standard_df['qty_orig'].notna().any():
            parsed_qty = standard_df['qty_orig'].apply(parse_value_currency)
            standard_df['qty'] = parsed_qty.apply(lambda x: x[0])
            standard_df['base_asset'] = parsed_qty.apply(lambda x: x[1])
            # 如果没有正确解析出基础资产，尝试从交易对中提取
            if standard_df['base_asset'].isna().all() and 'symbol' in standard_df.columns:
                standard_df['base_asset'] = standard_df['symbol'].str.split('-').str[0]
        else:
            standard_df['qty'] = Decimal(0)
            standard_df['base_asset'] = None
        
        # 处理费用和费用币种
        if 'fee_orig' in standard_df.columns and standard_df['fee_orig'].notna().any():
            parsed_fee = standard_df['fee_orig'].apply(parse_value_currency)
            standard_df['fee'] = parsed_fee.apply(lambda x: x[0])
            standard_df['fee_currency'] = parsed_fee.apply(lambda x: x[1])
            # 如果没有正确解析出费用币种，使用基础资产作为费用币种
            if standard_df['fee_currency'].isna().all() and 'base_asset' in standard_df.columns:
                standard_df['fee_currency'] = standard_df['base_asset']
        else:
            standard_df['fee'] = Decimal(0)
            standard_df['fee_currency'] = None
        
        # 对于欧易数据，我们使用 qty (来自Total Quantity) 作为数量
        # 计算金额 = 价格 × 数量
        standard_df['amount'] = standard_df['price'] * standard_df['qty']
        
        # 提取计价资产（报价资产）
        if 'symbol' in standard_df.columns:
            # 欧易格式通常是 BTC-USDT 格式，尝试提取第二部分作为计价资产
            standard_df['quote_asset'] = standard_df['symbol'].str.split('-').str[1]
        else:
            standard_df['quote_asset'] = None
        
        # 处理盈亏
        if 'realized_pnl_orig' in standard_df.columns:
            standard_df['realized_pnl'] = standard_df['realized_pnl_orig'].apply(safe_to_decimal)
            standard_df['pnl'] = standard_df['realized_pnl']
        else:
            # 如果没有提供盈亏数据，使用基本计算
            standard_df['pnl'] = np.where(
                standard_df['side'].str.upper() == 'SELL',
                standard_df['amount'],
                -standard_df['amount']
            )
            standard_df['pnl'] = standard_df['pnl'].apply(safe_to_decimal)
            standard_df['realized_pnl'] = Decimal(0)
        
        # 添加USDT计价盈亏
        standard_df['is_coin_margined'] = False
        standard_df['pnl_usdt'] = standard_df['pnl'].copy()
        
        # 识别币本位合约
        coin_margined_mask = standard_df['symbol'].str.contains('-USD-', na=False) & ~standard_df['symbol'].str.contains('-USDT-', na=False)
        standard_df.loc[coin_margined_mask, 'is_coin_margined'] = True
        
        # 币本位合约的PnL需要乘以价格转换为USDT价值
        for idx, row in standard_df[coin_margined_mask].iterrows():
            if pd.notna(row['price']) and pd.notna(row['pnl']):
                standard_df.at[idx, 'pnl_usdt'] = Decimal(row['pnl']) * Decimal(row['price'])
        
        # 添加额外信息
        standard_df['exchange'] = 'OKX'
        standard_df['data_type'] = standard_df.apply(
            lambda row: '合约' if 'bill_type' in standard_df.columns and 'Contract' in str(row['bill_type']) else '现货',
            axis=1
        )
        
        # 选择最终列
        final_cols = [
            'timestamp', 'symbol', 'side', 'price', 'qty', 'amount', 'fee', 'pnl', 
            'realized_pnl', 'base_asset', 'quote_asset', 'fee_currency', 'exchange', 
            'data_type', 'trade_count', 'is_coin_margined', 'pnl_usdt'
        ]
        
        final_df_cols = [col for col in final_cols if col in standard_df.columns]
        final_df = standard_df[final_df_cols]
        
        return final_df
    
    except Exception as e:
        st.error(f"处理欧易数据时出错: {str(e)}")
        import traceback
        st.code(traceback.format_exc(), language="python")
        return pd.DataFrame()
 # Set page config FIRST
st.set_page_config(
    page_title="交易数据高级分析系统",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem; color: #1E3A8A; text-align: center;
    }
    .sub-header {
        font-size: 1.5rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #E5E7EB;
    }
    .stMetric > div {
        border: 1px solid #e6e6e6;
        border-radius: 5px;
        padding: 10px;
        background-color: #f9f9f9;
    }
    .stMetric [data-testid="stMetricLabel"] {
        font-size: 0.95rem;
        font-weight: 600;
        color: #555;
    }
    .stMetric [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .trade-panel-container {
        border: 1px solid #e6e6e6;
        border-radius: 8px;
        padding: 15px;
        margin-top: 15px;
        background-color: #fafafa;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .chart-container {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        margin-top: 15px;
        background-color: white;
    }
    .fee-stats-container {
        background-color: #f0f7ff;
        border-radius: 8px;
        padding: 15px;
        margin-top: 15px;
        border: 1px solid #cce5ff;
    }
    .positive-value { color: green; font-weight: bold; }
    .negative-value { color: red; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'processed_data' not in st.session_state: st.session_state.processed_data = None
if 'symbols' not in st.session_state: st.session_state.symbols = []
if 'date_range' not in st.session_state: st.session_state.date_range = None
if 'selected_tab' not in st.session_state: st.session_state.selected_tab = "upload"

# Title
st.markdown('<h1 class="main-header">交易数据高级分析系统</h1>', unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("导航菜单")
pages = { "数据上传与处理": "upload", "交易分析与盈亏": "dashboard_pnl", "订单分析与统计": "orders", "交易策略评估": "strategy" }
selected_page = st.sidebar.radio("选择页面", list(pages.keys()), index=0)
current_page = pages[selected_page]

# 添加全局筛选条件到侧边栏，仅当有数据时显示
if st.session_state.processed_data is not None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 全局过滤条件")
    
    # 获取交易对列表
    symbols = st.session_state.symbols
    
    # 确保 session_state 中存在全局筛选条件
    if 'global_selected_symbols' not in st.session_state:
        st.session_state.global_selected_symbols = ["全部"]
    if 'global_selected_start_date' not in st.session_state or 'global_selected_end_date' not in st.session_state:
        st.session_state.global_selected_start_date, st.session_state.global_selected_end_date = st.session_state.date_range
        
    # 1. 交易对选择（全局）
    global_selected_symbols = st.sidebar.multiselect(
        "选择交易对", 
        ["全部"] + symbols, 
        default=st.session_state.global_selected_symbols,
        key="sidebar_symbols"
    )
    
    # 处理"全部"选项逻辑
    if not global_selected_symbols:
        st.sidebar.warning("请至少选择一个交易对或选择'全部'")
        global_selected_symbols = ["全部"]
    elif "全部" in global_selected_symbols and len(global_selected_symbols) > 1:
        st.sidebar.info("已选择'全部'交易对，其他选择将被忽略")
        global_selected_symbols = ["全部"]
    
    # 保存到session state
    st.session_state.global_selected_symbols = global_selected_symbols
    
    # 2. 日期范围选择（全局）
    min_date, max_date = st.session_state.date_range
    global_selected_dates = st.sidebar.date_input(
        "选择日期范围", 
        value=(st.session_state.global_selected_start_date, st.session_state.global_selected_end_date),
        min_value=min_date, 
        max_value=max_date,
        key="sidebar_dates"
    )
    
    if len(global_selected_dates) == 2:
        st.session_state.global_selected_start_date, st.session_state.global_selected_end_date = global_selected_dates
    else: 
        st.session_state.global_selected_start_date, st.session_state.global_selected_end_date = min_date, max_date
       
  
 
# ================================================
# ============ 数据上传与处理页面 ============
# ================================================
if current_page == "upload":
    st.markdown('<h2 class="sub-header">数据上传与处理</h2>', unsafe_allow_html=True)
    with st.expander("数据上传说明", expanded=True):
        st.markdown("""
        ### 上传说明
        1. 支持上传币安 **现货** 或 **U本位/币本位合约** 交易历史CSV文件。
        2. 支持上传欧易(OKX) **现货** 或 **合约** 交易历史CSV文件。
        3. 支持上传新格式CSV文件，系统将自动计算盈亏。
        4. 系统将自动识别文件类型并处理，统一数据格式。
        5. 处理后的数据可用于后续分析页面。

        #### 支持的字段 (不完全匹配也可尝试)
        **币安现货:** `Time(UTC)`, `Pair`, `Side`, `Price`, `Executed`, `Amount`, `Fee`
        **币安合约:** `Uid`, `Time(UTC)`, `Symbol`, `Side`, `Position Side`, `Price`, `Quantity`, `Amount`, `Fee`, `Realized Profit`
        **欧易:** `Date`, `Symbol`, `Bill Type`, `Side`, `Avg Price`, `Total Quantity`, `Total Fee`, `Total PnL`, `Trade Count`
        **新格式:** `Date`, `Symbol`, `TradeType`, `Side`, `Price`, `Quantity`, `Amount`, `Fee`
        """)
    uploaded_files = st.file_uploader("上传交易数据CSV文件", type="csv", accept_multiple_files=True)
    if uploaded_files:
        temp_paths = []
        for uploaded_file in uploaded_files:
            temp_file_path = f"temp_{uploaded_file.name}"
            with open(temp_file_path, "wb") as f: f.write(uploaded_file.getbuffer())
            temp_paths.append(temp_file_path)
        if st.button("处理上传的数据", key="process_data_button"):
            with st.spinner("正在处理数据..."):
                try:
                    all_data = []
                    for file_path in temp_paths:
                        try:
                            encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']
                            df = None
                            for encoding in encodings_to_try:
                                try:
                                    df = pd.read_csv(file_path, encoding=encoding, dtype=str, keep_default_na=False)
                                    st.success(f"文件 {os.path.basename(file_path)} 使用 {encoding} 编码成功读取")
                                    break
                                except UnicodeDecodeError: continue
                                except Exception as read_e: st.warning(f"使用 {encoding} 读取 {os.path.basename(file_path)} 时出错: {read_e}"); continue
                            if df is None: raise ValueError(f"无法使用支持的编码读取文件: {os.path.basename(file_path)}")

                            df.columns = df.columns.str.strip()
                            cols = df.columns.tolist()
                            st.write(f"检测到文件 '{os.path.basename(file_path)}' 的列: {cols}")

                            # 检测文件格式（币安或欧易或新格式）
                            file_format = detect_file_format(df)
                            st.write(f"检测到文件格式: {file_format}")
                            
                            if file_format == 'new_format':
                                # 处理新格式的文件
                                final_df = process_new_format_data(df)
                                if not final_df.empty:
                                    st.success(f"成功处理新格式文件: {os.path.basename(file_path)}, 记录数: {len(final_df)}")
                                    all_data.append(final_df)
                                else:
                                    st.error(f"处理新格式文件失败: {os.path.basename(file_path)}")
                            
                            elif file_format == 'okx':
                                # 处理欧易格式的文件
                                final_df = process_okx_data(df)
                                if not final_df.empty:
                                    st.success(f"成功处理欧易文件: {os.path.basename(file_path)}, 记录数: {len(final_df)}")
                                    all_data.append(final_df)
                                else:
                                    st.error(f"处理欧易文件失败: {os.path.basename(file_path)}")
                            
                            elif file_format == 'binance':
                                # 处理币安格式的文件（保持原有的处理逻辑）
                                col_map = { 'timestamp': ['Time(UTC)'], 'symbol': ['Symbol', 'Pair'], 'side': ['Side'], 'price_orig': ['Price'], 'qty_orig': ['Quantity', 'Executed'], 'amount_orig': ['Amount'], 'fee_orig': ['Fee'], 'realized_pnl_orig': ['Realized Profit'], 'position_side': ['Position Side'], 'uid': ['Uid'], 'order_id': ['Order Id'], 'trade_id': ['Trade Id'] }
                                standard_df = pd.DataFrame()
                                original_cols_used = {}
                                for standard_name, potential_names in col_map.items():
                                    found = False
                                    for potential_name in potential_names:
                                        if potential_name in df.columns:
                                            standard_df[standard_name] = df[potential_name]
                                            original_cols_used[standard_name] = potential_name
                                            found = True; break
                                    if not found and standard_name not in ['realized_pnl_orig', 'position_side', 'uid', 'order_id', 'trade_id']:
                                        standard_df[standard_name] = None

                                is_futures = 'realized_pnl_orig' in standard_df.columns and pd.notna(standard_df['realized_pnl_orig']).astype(str).str.strip().ne('').any()
                                is_spot = 'amount_orig' in standard_df.columns and not is_futures
                                data_type = '合约' if is_futures else '现货' if is_spot else '未知'
                                st.write(f"推断数据类型: {data_type}")

                                standard_df['timestamp'] = pd.to_datetime(standard_df['timestamp'], errors='coerce')
                                standard_df.dropna(subset=['timestamp'], inplace=True)

                                # --- Parsing ---
                                if 'qty_orig' in standard_df.columns and standard_df['qty_orig'].notna().any():
                                    parsed_qty = standard_df['qty_orig'].apply(parse_value_currency)
                                    standard_df['qty'] = parsed_qty.apply(lambda x: x[0])
                                    standard_df['base_asset'] = parsed_qty.apply(lambda x: x[1])
                                else: standard_df['qty'] = Decimal(0); standard_df['base_asset'] = None

                                if 'amount_orig' in standard_df.columns and standard_df['amount_orig'].notna().any():
                                    parsed_amount = standard_df['amount_orig'].apply(parse_value_currency)
                                    standard_df['amount'] = parsed_amount.apply(lambda x: x[0])
                                    standard_df['quote_asset'] = parsed_amount.apply(lambda x: x[1])
                                else: standard_df['amount'] = Decimal(0); standard_df['quote_asset'] = None

                                if 'fee_orig' in standard_df.columns and standard_df['fee_orig'].notna().any():
                                    parsed_fee = standard_df['fee_orig'].apply(parse_value_currency)
                                    standard_df['fee'] = parsed_fee.apply(lambda x: x[0])
                                    standard_df['fee_currency'] = parsed_fee.apply(lambda x: x[1])
                                else: standard_df['fee'] = Decimal(0); standard_df['fee_currency'] = None

                                standard_df['price'] = standard_df['price_orig'].apply(safe_to_decimal)

                                # --- PnL Calculation ---
                                if is_futures and 'realized_pnl_orig' in standard_df.columns:
                                    standard_df['realized_pnl'] = standard_df['realized_pnl_orig'].apply(safe_to_decimal)
                                    standard_df['pnl'] = standard_df['realized_pnl'] - standard_df['fee']
                                    
                                    # 添加USDT计价盈亏
                                    standard_df['is_coin_margined'] = False
                                    standard_df['pnl_usdt'] = standard_df['pnl'].copy()
                                    
                                    # 检查是否是币本位合约
                                    coin_margined_mask = (standard_df['symbol'].str.contains('USD', na=False) | 
                                                         standard_df['symbol'].str.contains('_PERP', na=False)) & \
                                                        ~standard_df['symbol'].str.contains('USDT', na=False)
                                    
                                    standard_df.loc[coin_margined_mask, 'is_coin_margined'] = True
                                    
                                    # 币本位合约的PnL需要乘以价格转换为USDT价值
                                    for idx, row in standard_df[coin_margined_mask].iterrows():
                                        if pd.notna(row['price']) and pd.notna(row['pnl']):
                                            standard_df.at[idx, 'pnl_usdt'] = Decimal(row['pnl']) * Decimal(row['price'])
                                elif is_spot:
                                    # 对于现货，使用新的盈亏计算函数
                                    standard_df = calculate_pnl_from_trades(standard_df)
                                else:
                                    standard_df['realized_pnl'] = Decimal(0)
                                    standard_df['pnl'] = Decimal(0)
                                    standard_df['is_coin_margined'] = False
                                    standard_df['pnl_usdt'] = Decimal(0)

                                # --- Final Touches ---
                                standard_df['exchange'] = 'Binance'; standard_df['source_file'] = os.path.basename(file_path); standard_df['data_type'] = data_type

                                final_cols = [ 'timestamp', 'symbol', 'side', 'price', 'qty', 'amount', 'fee', 'pnl', 'pnl_usdt', 'realized_pnl', 'base_asset', 'quote_asset', 'fee_currency', 'exchange', 'source_file', 'data_type', 'position_side', 'uid', 'order_id', 'trade_id', 'fee_orig', 'realized_pnl_orig', 'is_coin_margined' ]
                                final_df_cols = [col for col in final_cols if col in standard_df.columns]
                                final_df = standard_df[final_df_cols]
                                all_data.append(final_df)
                                st.success(f"成功处理币安文件: {os.path.basename(file_path)}, 记录数: {len(final_df)}")
                                
                            else:
                                st.warning(f"无法识别文件 {os.path.basename(file_path)} 的格式，跳过此文件")
                                
                        except Exception as e: st.error(f"处理文件 {os.path.basename(file_path)} 时失败: {type(e).__name__} - {str(e)}"); import traceback; st.code(traceback.format_exc(), language="python")

                    if all_data:
                        merged_data = pd.concat(all_data, ignore_index=True)
                        merged_data.sort_values('timestamp', inplace=True)
                        numeric_cols_to_check = ['price', 'qty', 'amount', 'fee', 'pnl', 'realized_pnl']
                        for col in numeric_cols_to_check:
                            if col in merged_data.columns: merged_data[col] = merged_data[col].apply(safe_to_decimal)
                        st.session_state.processed_data = merged_data
                        st.session_state.symbols = sorted(merged_data['symbol'].unique())
                        min_date = merged_data['timestamp'].min().date(); max_date = merged_data['timestamp'].max().date()
                        st.session_state.date_range = (min_date, max_date)
                        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "processed_data_combined.csv")
                        merged_data.to_csv(desktop_path, index=False, encoding='utf-8')
                        st.success(f"成功处理 {len(uploaded_files)} 个文件, 总共 {len(merged_data)} 条交易记录")
                        st.success(f"合并并处理后的数据已保存到桌面: processed_data_combined.csv")
                        st.markdown('<h3 class="sub-header">数据预览 (处理后)</h3>', unsafe_allow_html=True)
                        st.dataframe(merged_data.head(10), use_container_width=True)
                    else: st.error("未能成功处理任何数据文件。")
                    for path in temp_paths:
                        try: os.remove(path)
                        except: pass
                except Exception as e:
                    st.error(f"处理数据时发生严重错误: {str(e)}")
                    import traceback; st.code(traceback.format_exc(), language="python")
                    for path in temp_paths:
                        try: os.remove(path)
                        except: pass
    else:
        st.info("请上传交易数据CSV文件并点击处理按钮")
        if st.session_state.processed_data is not None:
            st.success("您已有处理好的数据，可以直接前往其他页面进行分析")
            df = st.session_state.processed_data
            st.markdown('<h3 class="sub-header">当前数据概览</h3>', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("交易记录数", f"{len(df)}")
            with col2: st.metric("交易对数量", f"{len(df['symbol'].unique())}")
            with col3: date_range_str = f"{df['timestamp'].min().date()} 至 {df['timestamp'].max().date()}"; st.metric("日期范围", date_range_str)
            st.dataframe(df.head(5), use_container_width=True)
            
            # ================================================
# ========= 交易分析与盈亏页面 =========
# ================================================
elif current_page == "dashboard_pnl":
    st.markdown('<h2 class="sub-header">交易分析与盈亏</h2>', unsafe_allow_html=True)
    if st.session_state.processed_data is None: st.warning("未找到处理好的数据。请先前往'数据上传与处理'页面上传并处理数据。")
    else:
        processed_data = st.session_state.processed_data; symbols = st.session_state.symbols
        symbol_col = 'symbol'; time_col = 'timestamp'; side_col = 'side'; pnl_col = 'pnl'; fee_col = 'fee'
        
        # 配置区域
        st.markdown('<h3 class="sub-header">分析配置</h3>', unsafe_allow_html=True)
        analysis_type = st.selectbox("分析维度", ["按交易对", "按时间", "按交易方向"])
            
        # 使用全局筛选条件
        selected_symbols = st.session_state.global_selected_symbols
        selected_start_date = st.session_state.global_selected_start_date
        selected_end_date = st.session_state.global_selected_end_date
        
        try:
            filtered_data = processed_data.copy()
            
            # 修改筛选逻辑以支持多交易对
            if selected_symbols != ["全部"]:
                filtered_data = filtered_data[filtered_data[symbol_col].isin(selected_symbols)]
                
            filtered_data[time_col] = pd.to_datetime(filtered_data[time_col])
            filtered_data = filtered_data[ (filtered_data[time_col].dt.date >= selected_start_date) & (filtered_data[time_col].dt.date <= selected_end_date) ]
            if pnl_col in filtered_data.columns: filtered_data[pnl_col] = filtered_data[pnl_col].apply(safe_to_decimal)
            else: st.error(f"必需的 PnL 列 '{pnl_col}' 不存在。"); filtered_data = pd.DataFrame()
            if fee_col in filtered_data.columns:
                filtered_data[fee_col] = filtered_data[fee_col].apply(safe_to_decimal)
        except Exception as filter_e: st.error(f"过滤数据时出错: {filter_e}"); filtered_data = pd.DataFrame()
        
        # 显示当前应用的筛选条件
        if selected_symbols != ["全部"]:
            st.info(f"当前分析: {', '.join(selected_symbols)} | 日期范围: {selected_start_date} 至 {selected_end_date}")
        else:
            st.info(f"当前分析: 全部交易对 | 日期范围: {selected_start_date} 至 {selected_end_date}")
        
        if filtered_data.empty: st.warning("所选条件没有匹配的交易数据")
        else:
            # 主要分析区域
            tab1, tab2, tab3, tab4 = st.tabs(["盈亏统计", "交易分布", "交易时间分布", "交易详情"])
            
            # === Tab 1: 盈亏统计 ===
            with tab1:
                st.markdown('<h3 class="sub-header">盈亏统计摘要</h3>', unsafe_allow_html=True)
                try:
                    # --- PnL Statistics ---
                    total_pnl = filtered_data[pnl_col].sum()
                    
                    # 添加USDT计价的总盈亏
                    total_pnl_usdt = Decimal(0)
                    if 'pnl_usdt' in filtered_data.columns:
                        filtered_data['pnl_usdt'] = filtered_data['pnl_usdt'].apply(safe_to_decimal)
                        total_pnl_usdt = filtered_data['pnl_usdt'].sum()
                        
                    win_trades = filtered_data[filtered_data[pnl_col] > 0]; loss_trades = filtered_data[filtered_data[pnl_col] < 0]
                    win_count = len(win_trades); loss_count = len(loss_trades); total_count = len(filtered_data)
                    win_rate = float(win_count) / float(total_count) if total_count > 0 else 0.0
                    avg_profit_float = float(win_trades[pnl_col].astype(float).mean()) if win_count > 0 else 0.0
                    avg_loss_float = abs(float(loss_trades[pnl_col].astype(float).mean())) if loss_count > 0 else 0.0
                    profit_loss_ratio = avg_profit_float / avg_loss_float if avg_loss_float > 0 else float('inf')
                    expected_value = win_rate * avg_profit_float - (1 - win_rate) * avg_loss_float
                    
                    # --- Trade Statistics ---
                    stats = generate_trade_statistics(filtered_data, symbol=None)
                    # Remove the duplicate display that shows the same three values
                    # if stats: display_trade_statistics(stats, symbol=None)
                    
                    # --- Fee Statistics ---
                    fee_stats = calculate_fee_statistics(filtered_data)
                    total_fees = fee_stats['total_fees_usdt'] if fee_stats else Decimal(0)
                    
                    # --- Display combined metrics ---
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: 
                        st.metric("总盈亏", f"{total_pnl:.4f}")
                        if 'pnl_usdt' in filtered_data.columns:
                            st.metric("总盈亏(USDT)", f"{total_pnl_usdt:.4f}")
                        st.metric("总费用", f"{total_fees:.4f}")
                    with col2: 
                        st.metric("胜率", f"{win_rate:.2%}")
                        st.metric("净利润 (盈亏-费用)", f"{(total_pnl-total_fees):.4f}")
                        if 'pnl_usdt' in filtered_data.columns:
                            st.metric("净利润(USDT)", f"{(total_pnl_usdt-total_fees):.4f}")
                    with col3: 
                        st.metric("盈亏比", f"{profit_loss_ratio:.2f}" if math.isfinite(profit_loss_ratio) else "无限大")
                        st.metric("平均每笔费用", f"{(total_fees/total_count):.8f}" if total_count > 0 else "0")
                    with col4: 
                        st.metric("期望值/每笔", f"{expected_value:.4f}")
                        st.metric("费用占利润百分比", f"{(total_fees/total_pnl*100):.2f}%" if total_pnl > 0 else "N/A")
                    
                    if fee_stats:
                        st.markdown('<div class="fee-stats-container">', unsafe_allow_html=True)
                        display_fee_statistics(fee_stats, key_prefix="dashboard_pnl_fee_stats")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<h3 class="sub-header">{analysis_type}盈亏分析</h3>', unsafe_allow_html=True)
                    # ... [Keep PnL plotting logic] ...
                    if analysis_type == "按交易对":
                        symbol_pnl = filtered_data.groupby(symbol_col)[pnl_col].agg(['sum', 'count', 'mean']).reset_index()
                        symbol_pnl.columns = [symbol_col, '总盈亏', '交易次数', '平均盈亏']
                        symbol_pnl = symbol_pnl.sort_values('总盈亏', ascending=False)
                        if not symbol_pnl.empty:
                            fig = make_subplots(specs=[[{"secondary_y": True}]])
                            colors = ['green' if pnl >= 0 else 'red' for pnl in symbol_pnl['总盈亏']]
                            fig.add_trace(go.Bar(x=symbol_pnl[symbol_col], y=symbol_pnl['总盈亏'], marker_color=colors, name="总盈亏"), secondary_y=False)
                            fig.add_trace(go.Scatter(x=symbol_pnl[symbol_col], y=symbol_pnl['交易次数'], mode='lines+markers', name="交易次数", line=dict(color='purple')), secondary_y=True)
                            fig.update_layout(title="各交易对盈亏情况", xaxis_title="交易对", height=500)
                            fig.update_yaxes(title_text="总盈亏", secondary_y=False); fig.update_yaxes(title_text="交易次数", secondary_y=True)
                            st.plotly_chart(fig, use_container_width=True, key="dashboard_pnl_by_symbol")
                            st.dataframe(symbol_pnl, use_container_width=True)
                        else: st.info("无数据可用于按交易对分析。")
                    elif analysis_type == "按时间":
                        filtered_data['trade_date'] = pd.to_datetime(filtered_data[time_col]).dt.date
                        date_pnl = filtered_data.groupby('trade_date')[pnl_col].agg(['sum', 'count']).reset_index()
                        date_pnl.columns = ['日期', '每日盈亏', '交易次数']
                        date_pnl['累计盈亏'] = date_pnl['每日盈亏'].cumsum()
                        if not date_pnl.empty:
                            fig = make_subplots(specs=[[{"secondary_y": True}]])
                            colors = ['green' if pnl >= 0 else 'red' for pnl in date_pnl['每日盈亏']]
                            fig.add_trace(go.Bar(x=date_pnl['日期'], y=date_pnl['每日盈亏'], marker_color=colors, name="每日盈亏"), secondary_y=False)
                            fig.add_trace(go.Scatter(x=date_pnl['日期'], y=date_pnl['累计盈亏'], mode='lines', line=dict(color='blue'), name="累计盈亏"), secondary_y=False)
                            fig.add_trace(go.Scatter(x=date_pnl['日期'], y=date_pnl['交易次数'], mode='lines', line=dict(color='purple', dash='dot'), name="交易次数"), secondary_y=True)
                            fig.update_layout(title="按日期盈亏分析", xaxis_title="日期", height=500)
                            fig.update_yaxes(title_text="盈亏", secondary_y=False)
                            fig.update_yaxes(title_text="交易次数", secondary_y=True)
                            st.plotly_chart(fig, use_container_width=True, key="dashboard_pnl_by_date")
                            st.markdown('<h4>月度盈亏汇总</h4>', unsafe_allow_html=True)
                            filtered_data['year_month'] = pd.to_datetime(filtered_data[time_col]).dt.strftime('%Y-%m')
                            month_pnl = filtered_data.groupby('year_month')[pnl_col].agg(['sum', 'count', 'mean']).reset_index()
                            month_pnl.columns = ['年月', '月度盈亏', '交易次数', '平均盈亏']
                            st.dataframe(month_pnl, use_container_width=True)
                        else: st.info("无数据可用于按时间分析。")
                    elif analysis_type == "按交易方向":
                        side_pnl = filtered_data.groupby(side_col)[pnl_col].agg(['sum', 'count', 'mean']).reset_index()
                        side_pnl.columns = ['方向', '总盈亏', '交易次数', '平均盈亏']
                        if not side_pnl.empty:
                            col1, col2 = st.columns(2)
                            with col1:
                                fig1 = go.Figure(data=[go.Pie(labels=side_pnl['方向'], values=side_pnl['交易次数'], hole=.3, name="交易次数")])
                                fig1.update_layout(title="交易方向分布", height=400)
                                st.plotly_chart(fig1, use_container_width=True, key="dashboard_pnl_direction_pie")
                            with col2:
                                fig2 = go.Figure()
                                colors = ['green' if pnl >= 0 else 'red' for pnl in side_pnl['总盈亏']]
                                fig2.add_trace(go.Bar(x=side_pnl['方向'], y=side_pnl['总盈亏'], marker_color=colors, name="总盈亏"))
                                fig2.add_trace(go.Scatter(x=side_pnl['方向'], y=side_pnl['平均盈亏'], mode='lines+markers', name="平均盈亏", line=dict(color='purple')))
                                fig2.update_layout(title="交易方向盈亏分析", xaxis_title="交易方向", yaxis_title="盈亏", height=400)
                                st.plotly_chart(fig2, use_container_width=True, key="dashboard_pnl_by_direction")
                            st.dataframe(side_pnl, use_container_width=True)
                        else: st.info("无数据可用于按交易方向分析。")
                except Exception as e: st.error(f"生成盈亏分析时出错: {str(e)}"); import traceback; st.code(traceback.format_exc(), language="python")
            
            # === Tab 2: 交易分布 ===
            with tab2:
                try:
                    symbol_trades = filtered_data.groupby(symbol_col).size().reset_index(name='counts').sort_values('counts', ascending=False).head(15)
                    if not symbol_trades.empty:
                        fig = go.Figure(go.Bar(x=symbol_trades[symbol_col], y=symbol_trades['counts'], marker_color='royalblue'))
                        fig.update_layout(title='交易对分布 (前15名)', xaxis_title='交易对', yaxis_title='交易次数', height=400)
                        st.plotly_chart(fig, use_container_width=True, key="dashboard_trade_distribution")
                                
                        # 最盈利和最亏损交易对
                        symbol_pnl = filtered_data.groupby(symbol_col)[pnl_col].sum().reset_index().sort_values(pnl_col, ascending=False)
                        if not symbol_pnl.empty:
                            st.markdown('#### 最盈利和最亏损交易对')
                            top_profit = symbol_pnl.head(5); top_loss = symbol_pnl.tail(5)
                            fig = go.Figure()
                            fig.add_trace(go.Bar(x=top_profit[symbol_col], y=top_profit[pnl_col], marker_color='green', name='最盈利交易对'))
                            fig.add_trace(go.Bar(x=top_loss[symbol_col], y=top_loss[pnl_col], marker_color='red', name='最亏损交易对'))
                            fig.update_layout(title="最盈利和最亏损交易对", xaxis_title="交易对", yaxis_title="盈亏", height=400, barmode='group')
                            st.plotly_chart(fig, use_container_width=True, key="dashboard_pnl_top_analysis")
                            
                            # 如果有USDT计价的盈亏数据，增加一个显示
                            if 'pnl_usdt' in filtered_data.columns:
                                st.markdown('#### USDT计价盈亏分析')
                                symbol_pnl_usdt = filtered_data.groupby(symbol_col)['pnl_usdt'].sum().reset_index().sort_values('pnl_usdt', ascending=False)
                                top_profit_usdt = symbol_pnl_usdt.head(5); top_loss_usdt = symbol_pnl_usdt.tail(5)
                                fig_usdt = go.Figure()
                                fig_usdt.add_trace(go.Bar(x=top_profit_usdt[symbol_col], y=top_profit_usdt['pnl_usdt'], marker_color='green', name='最盈利交易对(USDT)'))
                                fig_usdt.add_trace(go.Bar(x=top_loss_usdt[symbol_col], y=top_loss_usdt['pnl_usdt'], marker_color='red', name='最亏损交易对(USDT)'))
                                fig_usdt.update_layout(title='最盈利和最亏损交易对(USDT计价)', xaxis_title='交易对', yaxis_title='盈亏(USDT)', height=400, barmode='group')
                                st.plotly_chart(fig_usdt, use_container_width=True, key="dashboard_pnl_top_analysis_usdt")
                    else: st.info("无数据可用于交易分布分析。")
                except Exception as e: st.error(f"绘制交易分布图时出错: {str(e)}")
                    
            # === Tab 3: 交易时间分布 ===
            with tab3:
                try:
                    filtered_data['trade_date'] = pd.to_datetime(filtered_data[time_col]).dt.date
                    filtered_data['trade_hour'] = pd.to_datetime(filtered_data[time_col]).dt.hour
                    date_counts = filtered_data.groupby('trade_date').size().reset_index(name='counts')
                    hour_counts = filtered_data.groupby('trade_hour').size().reset_index(name='counts')
                    if not date_counts.empty and not hour_counts.empty:
                        fig = make_subplots(rows=2, cols=1, subplot_titles=('交易日期分布', '交易时间(小时)分布'), vertical_spacing=0.1, row_heights=[0.6, 0.4])
                        fig.add_trace(go.Scatter(x=date_counts['trade_date'], y=date_counts['counts'], mode='lines+markers', name='交易次数 (日)', line=dict(color='royalblue', width=2)), row=1, col=1)
                        fig.add_trace(go.Bar(x=hour_counts['trade_hour'], y=hour_counts['counts'], marker_color='royalblue', name='交易次数 (时)'), row=2, col=1)
                        fig.update_layout(height=600, showlegend=False)
                        fig.update_xaxes(title_text='日期', row=1, col=1); fig.update_yaxes(title_text='交易次数', row=1, col=1)
                        fig.update_xaxes(title_text='小时', row=2, col=1); fig.update_yaxes(title_text='交易次数', row=2, col=1)
                        st.plotly_chart(fig, use_container_width=True, key="dashboard_time_distribution")
                    else: st.info("无数据可用于时间分布图。")
                    
                    # 添加星期几交易频率分析
                    try:
                        filtered_data['weekday'] = pd.to_datetime(filtered_data[time_col]).dt.weekday
                        weekday_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
                        filtered_data['weekday_name'] = filtered_data['weekday'].map(weekday_map)
                        
                        weekday_counts = filtered_data.groupby('weekday_name').size().reindex(['周一', '周二', '周三', '周四', '周五', '周六', '周日']).reset_index(name='交易次数')
                        weekday_pnl = filtered_data.groupby('weekday_name')[pnl_col].sum().reindex(['周一', '周二', '周三', '周四', '周五', '周六', '周日']).reset_index(name='总盈亏')
                        
                        weekday_stats = pd.merge(weekday_counts, weekday_pnl, on='weekday_name')
                        weekday_stats['平均盈亏'] = weekday_stats['总盈亏'] / weekday_stats['交易次数']
                        weekday_stats.rename(columns={'weekday_name': '星期'}, inplace=True)
                        
                        if not weekday_stats.empty:
                            st.markdown('#### 按星期交易频率分析')
                            
                            fig = make_subplots(specs=[[{"secondary_y": True}]])
                            fig.add_trace(go.Bar(x=weekday_stats['星期'], y=weekday_stats['交易次数'], name='交易次数', marker_color='royalblue'), secondary_y=False)
                            fig.add_trace(go.Scatter(x=weekday_stats['星期'], y=weekday_stats['总盈亏'], name='总盈亏', mode='lines+markers', marker=dict(color='green')), secondary_y=True)
                            fig.update_layout(title='星期交易频率与盈亏分析', height=400)
                            fig.update_yaxes(title_text='交易次数', secondary_y=False)
                            fig.update_yaxes(title_text='总盈亏', secondary_y=True)
                            st.plotly_chart(fig, use_container_width=True)
                            
                            st.dataframe(weekday_stats[['星期', '总盈亏', '平均盈亏', '交易次数']], use_container_width=True)
                    except Exception as freq_e:
                        st.error(f"生成交易频率分析时出错: {str(freq_e)}")
                except Exception as e: st.error(f"绘制时间分布图时出错: {str(e)}")
                
            # === Tab 4: 交易详情 ===
            with tab4:
                st.markdown('<h3 class="sub-header">最盈利和最亏损的交易</h3>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                display_cols = ['timestamp', 'symbol', 'side', 'price', 'qty', 'pnl', 'amount', 'fee']
                display_cols = [col for col in display_cols if col in filtered_data.columns]
                with col1:
                    st.write("#### 最盈利的5笔交易"); top_profitable = filtered_data.sort_values(pnl_col, ascending=False).head(5)
                    if not top_profitable.empty:
                        display_df = top_profitable[display_cols].copy(); display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                        st.dataframe(display_df.rename(columns={'timestamp':'时间', 'symbol':'交易对', 'side':'方向', 'price':'价格', 'qty':'数量', 'pnl':'盈亏', 'amount':'金额', 'fee':'费用'}), use_container_width=True)
                    else: st.info("没有盈利交易")
                with col2:
                    st.write("#### 最亏损的5笔交易"); top_unprofitable = filtered_data.sort_values(pnl_col).head(5)
                    if not top_unprofitable.empty:
                        display_df = top_unprofitable[display_cols].copy(); display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                        st.dataframe(display_df.rename(columns={'timestamp':'时间', 'symbol':'交易对', 'side':'方向', 'price':'价格', 'qty':'数量', 'pnl':'盈亏', 'amount':'金额', 'fee':'费用'}), use_container_width=True)
                    else: st.info("没有亏损交易")
                    
                    
                    # ================================================
# ========= 订单分析与统计页面 =========
# ================================================
elif current_page == "orders":
    st.markdown('<h2 class="sub-header">订单分析与统计</h2>', unsafe_allow_html=True)
    if st.session_state.processed_data is None: st.warning("未找到处理好的数据。请先前往'数据上传与处理'页面上传并处理数据。")
    else:
        processed_data = st.session_state.processed_data
        symbol_col = 'symbol'; time_col = 'timestamp'; fee_col = 'fee'; price_col = 'price'; qty_col = 'qty'; side_col = 'side'; pnl_col = 'pnl'
        
        # 使用全局筛选条件
        selected_symbols = st.session_state.global_selected_symbols
        selected_start_date = st.session_state.global_selected_start_date
        selected_end_date = st.session_state.global_selected_end_date
        
        # 显示当前应用的筛选条件
        if selected_symbols != ["全部"]:
            st.info(f"当前分析: {', '.join(selected_symbols)} | 日期范围: {selected_start_date} 至 {selected_end_date}")
        else:
            st.info(f"当前分析: 全部交易对 | 日期范围: {selected_start_date} 至 {selected_end_date}")
        
        try:
            filtered_data = processed_data.copy()
            
            # 修改筛选逻辑以支持多交易对
            if selected_symbols != ["全部"]:
                filtered_data = filtered_data[filtered_data[symbol_col].isin(selected_symbols)]
                
            filtered_data[time_col] = pd.to_datetime(filtered_data[time_col])
            filtered_data = filtered_data[ (filtered_data[time_col].dt.date >= selected_start_date) & (filtered_data[time_col].dt.date <= selected_end_date) ]
            for col in [fee_col, price_col, qty_col, pnl_col]:
                if col in filtered_data.columns:
                    filtered_data[col] = filtered_data[col].apply(safe_to_decimal)
        except Exception as filter_e: 
            st.error(f"过滤数据时出错: {filter_e}")
            filtered_data = pd.DataFrame()
            
        if filtered_data.empty: 
            st.warning("所选条件没有匹配的交易数据")
        else:
            # --- Fee Statistics (New!) ---
            fee_stats = calculate_fee_statistics(filtered_data)
            if fee_stats:
                st.markdown('<div class="fee-stats-container">', unsafe_allow_html=True)
                display_fee_statistics(fee_stats, key_prefix="order_tab_fee_stats")
                st.markdown('</div>', unsafe_allow_html=True)
                
            # --- Order Panel (更新为支持多交易对) ---
            create_order_panel(filtered_data, symbols=selected_symbols)

# ================================================
# ========= 交易策略评估页面 =========
# ================================================
elif current_page == "strategy":
    st.markdown('<h2 class="sub-header">交易策略评估</h2>', unsafe_allow_html=True)
    if st.session_state.processed_data is None: st.warning("未找到处理好的数据。请先前往'数据上传与处理'页面上传并处理数据。")
    else:
        processed_data = st.session_state.processed_data
        symbol_col = 'symbol'; time_col = 'timestamp'; side_col = 'side'; pnl_col = 'pnl'; fee_col = 'fee'
        
        # 使用全局筛选条件
        selected_symbols = st.session_state.global_selected_symbols
        selected_start_date = st.session_state.global_selected_start_date
        selected_end_date = st.session_state.global_selected_end_date
        
        # 显示当前应用的筛选条件
        if selected_symbols != ["全部"]:
            st.info(f"当前分析: {', '.join(selected_symbols)} | 日期范围: {selected_start_date} 至 {selected_end_date}")
        else:
            st.info(f"当前分析: 全部交易对 | 日期范围: {selected_start_date} 至 {selected_end_date}")
            
        try:
            filtered_data = processed_data.copy()
            
            # 修改筛选逻辑以支持多交易对
            if selected_symbols != ["全部"]:
                filtered_data = filtered_data[filtered_data[symbol_col].isin(selected_symbols)]
            
            filtered_data[time_col] = pd.to_datetime(filtered_data[time_col])
            filtered_data = filtered_data[ (filtered_data[time_col].dt.date >= selected_start_date) & (filtered_data[time_col].dt.date <= selected_end_date) ]
            if pnl_col in filtered_data.columns: filtered_data[pnl_col] = filtered_data[pnl_col].apply(safe_to_decimal)
            else: st.error(f"必需的 PnL 列 '{pnl_col}' 不存在。"); filtered_data = pd.DataFrame()
            if fee_col in filtered_data.columns:
                filtered_data[fee_col] = filtered_data[fee_col].apply(safe_to_decimal)
        except Exception as filter_e: st.error(f"过滤数据时出错: {filter_e}"); filtered_data = pd.DataFrame()
        
        if filtered_data.empty: st.warning("所选条件没有匹配的交易数据")
        else:
            st.markdown('<h3 class="sub-header">策略表现指标</h3>', unsafe_allow_html=True)
            try:
                # --- PnL Statistics ---
                total_pnl = filtered_data[pnl_col].sum()
                
                # 添加USDT计价的总盈亏
                total_pnl_usdt = Decimal(0)
                if 'pnl_usdt' in filtered_data.columns:
                    filtered_data['pnl_usdt'] = filtered_data['pnl_usdt'].apply(safe_to_decimal)
                    total_pnl_usdt = filtered_data['pnl_usdt'].sum()
                    
                filtered_data['trade_date'] = pd.to_datetime(filtered_data[time_col]).dt.date
                daily_pnl = filtered_data.groupby('trade_date')[pnl_col].sum().reset_index()
                
                # 添加USDT计价的日盈亏
                if 'pnl_usdt' in filtered_data.columns:
                    daily_pnl_usdt = filtered_data.groupby('trade_date')['pnl_usdt'].sum().reset_index()
                    daily_pnl['pnl_usdt'] = daily_pnl_usdt['pnl_usdt']
                
                # --- Fee Statistics ---
                fee_stats = calculate_fee_statistics(filtered_data)
                total_fees = fee_stats['total_fees_usdt'] if fee_stats else Decimal(0)

                if not daily_pnl.empty:
                    # Max Drawdown Calculation
                    daily_pnl['cumulative_pnl'] = daily_pnl[pnl_col].cumsum()
                    daily_pnl['running_max'] = daily_pnl['cumulative_pnl'].cummax()
                    daily_pnl['drawdown'] = daily_pnl['running_max'] - daily_pnl['cumulative_pnl']
                    max_drawdown = daily_pnl['drawdown'].max()

                    # Sharpe Ratio Calculation (Fixed)
                    daily_returns_float = daily_pnl[pnl_col].astype(float)
                    mean_return_float = daily_returns_float.mean()
                    std_dev_float = daily_returns_float.std()
                    if pd.notna(std_dev_float) and std_dev_float > 0: sharpe_ratio = mean_return_float / std_dev_float * math.sqrt(252)
                    else: sharpe_ratio = 0.0

                    # Consecutive Profit/Loss Days
                    daily_pnl['is_profit'] = daily_pnl[pnl_col] > 0
                    profit_streaks = daily_pnl['is_profit'].groupby((daily_pnl['is_profit'] != daily_pnl['is_profit'].shift()).cumsum()).cumsum()
                    loss_streaks = (~daily_pnl['is_profit']).groupby(((~daily_pnl['is_profit']) != (~daily_pnl['is_profit']).shift()).cumsum()).cumsum()
                    max_consecutive_profit = profit_streaks.max() if not profit_streaks.empty else 0
                    max_consecutive_loss = loss_streaks.max() if not loss_streaks.empty else 0

                    # Win Rate & P/L Ratio
                    win_count = daily_pnl['is_profit'].sum()
                    loss_count = len(daily_pnl) - win_count
                    win_rate = float(win_count) / float(len(daily_pnl)) if len(daily_pnl) > 0 else 0.0
                    avg_profit = daily_pnl[daily_pnl[pnl_col] > 0][pnl_col].mean() if win_count > 0 else Decimal(0)
                    avg_loss = abs(daily_pnl[daily_pnl[pnl_col] < 0][pnl_col].mean()) if loss_count > 0 else Decimal(0)
                    avg_profit_float = float(avg_profit); avg_loss_float = float(avg_loss)
                    profit_loss_ratio = avg_profit_float / avg_loss_float if avg_loss_float > 0 else float('inf')
                    expected_value = win_rate * avg_profit_float - (1 - win_rate) * avg_loss_float

                    # 显示选择的交易对信息
                    if selected_symbols != ["全部"]:
                        symbol_str = ", ".join(selected_symbols)
                        st.info(f"当前分析交易对: {symbol_str}")
                    else:
                        st.info("当前分析全部交易对")
                        
                    # Display Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: 
                        st.metric("总盈亏", f"{total_pnl:.4f}")
                        if 'pnl_usdt' in filtered_data.columns:
                            st.metric("总盈亏(USDT)", f"{total_pnl_usdt:.4f}")
                        st.metric("最大连盈天数", f"{int(max_consecutive_profit)}")
                        st.metric("总手续费", f"{total_fees:.4f}")
                    with col2: 
                        st.metric("最大回撤", f"{max_drawdown:.4f}")
                        st.metric("最大连亏天数", f"{int(max_consecutive_loss)}")
                        st.metric("净利润 (盈亏-费用)", f"{(total_pnl-total_fees):.4f}")
                        if 'pnl_usdt' in filtered_data.columns:
                            st.metric("净利润(USDT)", f"{(total_pnl_usdt-total_fees):.4f}")
                    with col3: 
                        st.metric("夏普比率 (年化)", f"{sharpe_ratio:.4f}")
                        st.metric("盈利天数", f"{win_count}")
                        st.metric("利润因子", f"{(avg_profit_float*win_rate)/(avg_loss_float*(1-win_rate)):.4f}" if avg_loss_float > 0 and win_rate < 1 else "N/A")
                    with col4: 
                        st.metric("日胜率", f"{win_rate:.2%}")
                        st.metric("亏损天数", f"{loss_count}")
                        st.metric("费用占利润比例", f"{(total_fees/total_pnl*100):.2f}%" if total_pnl > 0 else "N/A")

                    # Performance Curve
                    st.markdown('<h3 class="sub-header">策略表现曲线</h3>', unsafe_allow_html=True)
                    fig = make_subplots(rows=2, cols=1, subplot_titles=('每日盈亏和累计盈亏', '回撤'), vertical_spacing=0.12, row_heights=[0.7, 0.3])
                    colors = ['green' if pnl >= 0 else 'red' for pnl in daily_pnl[pnl_col]]
                    fig.add_trace(go.Bar(x=daily_pnl['trade_date'], y=daily_pnl[pnl_col], marker_color=colors, name="每日盈亏"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=daily_pnl['trade_date'], y=daily_pnl['cumulative_pnl'], mode='lines', name="累计盈亏", line=dict(color='blue')), row=1, col=1)
                    fig.add_trace(go.Scatter(x=daily_pnl['trade_date'], y=daily_pnl['drawdown'], mode='lines', name="回撤", line=dict(color='red'), fill='tozeroy'), row=2, col=1)
                    fig.update_layout(height=600, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    fig.update_xaxes(title_text='日期', row=1, col=1); fig.update_yaxes(title_text='盈亏', row=1, col=1)
                    fig.update_xaxes(title_text='日期', row=2, col=1); fig.update_yaxes(title_text='回撤', row=2, col=1)
                    st.plotly_chart(fig, use_container_width=True, key="strategy_performance_curve")

                    # 当选择多个交易对时，添加交易对之间的对比分析
                    if selected_symbols != ["全部"] and len(selected_symbols) > 1:
                        st.markdown('<h3 class="sub-header">交易对表现对比</h3>', unsafe_allow_html=True)
                        
                        # 按交易对和日期计算每日盈亏
                        symbol_daily_pnl = filtered_data.groupby([symbol_col, 'trade_date'])[pnl_col].sum().reset_index()
                        
                        # 为每个交易对创建累计盈亏
                        symbol_cum_pnl = pd.DataFrame()
                        for symbol in selected_symbols:
                            symbol_data = symbol_daily_pnl[symbol_daily_pnl[symbol_col] == symbol].copy()
                            if not symbol_data.empty:
                                symbol_data['cumulative_pnl'] = symbol_data[pnl_col].cumsum()
                                symbol_data['symbol_name'] = symbol  # 添加一个标识列
                                symbol_cum_pnl = pd.concat([symbol_cum_pnl, symbol_data])
                        
                        if not symbol_cum_pnl.empty:
                            # 创建交易对累计盈亏对比图
                            fig_symbols = go.Figure()
                            for symbol in selected_symbols:
                                symbol_data = symbol_cum_pnl[symbol_cum_pnl['symbol_name'] == symbol]
                                if not symbol_data.empty:
                                    fig_symbols.add_trace(go.Scatter(
                                        x=symbol_data['trade_date'],
                                        y=symbol_data['cumulative_pnl'],
                                        mode='lines',
                                        name=symbol
                                    ))
                            
                            fig_symbols.update_layout(
                                title="交易对累计盈亏对比",
                                xaxis_title="日期",
                                yaxis_title="累计盈亏",
                                height=500,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            st.plotly_chart(fig_symbols, use_container_width=True, key="symbol_comparison_curve")
                            
                            # 交易对绩效统计表
                            symbol_stats = filtered_data.groupby(symbol_col).agg(
                                总盈亏=(pnl_col, 'sum'),
                                交易次数=(time_col, 'count'),
                                平均盈亏=(pnl_col, 'mean'),
                                最大盈利=(pnl_col, lambda x: x.max()),
                                最大亏损=(pnl_col, lambda x: x.min())
                            ).reset_index()
                            
                            # 计算胜率
                            win_rates = []
                            for symbol in symbol_stats[symbol_col]:
                                symbol_trades = filtered_data[filtered_data[symbol_col] == symbol]
                                wins = len(symbol_trades[symbol_trades[pnl_col] > 0])
                                total = len(symbol_trades)
                                win_rate = wins / total if total > 0 else 0
                                win_rates.append(win_rate)
                            
                            symbol_stats['胜率'] = win_rates
                            symbol_stats['胜率'] = symbol_stats['胜率'].apply(lambda x: f"{x:.2%}")
                            
                            # 按总盈亏排序
                            symbol_stats = symbol_stats.sort_values('总盈亏', ascending=False)
                            
                            st.dataframe(symbol_stats, use_container_width=True)
                    
                    # Monthly PnL
                    st.markdown('<h3 class="sub-header">月度盈亏汇总</h3>', unsafe_allow_html=True)
                    filtered_data['year_month'] = pd.to_datetime(filtered_data[time_col]).dt.strftime('%Y-%m')
                    month_pnl = filtered_data.groupby('year_month')[pnl_col].agg(['sum', 'count', 'mean']).reset_index()
                    month_pnl.columns = ['年月', '月度盈亏', '交易次数', '平均盈亏']
                    if not month_pnl.empty:
                        months = month_pnl['年月'].str.split('-', expand=True); month_pnl['年'] = months[0]; month_pnl['月'] = months[1]
                        pivot_data = month_pnl.pivot_table(values='月度盈亏', index='年', columns='月', aggfunc='sum')
                        if not pivot_data.empty:
                            fig = go.Figure(data=go.Heatmap(z=pivot_data.values, x=pivot_data.columns, y=pivot_data.index, colorscale=[[0, 'red'],[0.5, 'white'],[1, 'green']], colorbar=dict(title='盈亏'), hoverongaps=False))
                            fig.update_layout(title='月度盈亏热力图', xaxis_title='月份', yaxis_title='年份', height=400)
                            st.plotly_chart(fig, use_container_width=True, key="strategy_monthly_heatmap")
                        st.dataframe(month_pnl[['年月', '月度盈亏', '交易次数', '平均盈亏']], use_container_width=True)
                    else: st.info("无月度数据可展示。")

                    # Trading Frequency Analysis
                    st.markdown('<h3 class="sub-header">交易频率分析</h3>', unsafe_allow_html=True)
                    try: # Wrap frequency analysis in its own try-except
                        filtered_data['hour'] = pd.to_datetime(filtered_data[time_col]).dt.hour
                        filtered_data['weekday'] = pd.to_datetime(filtered_data[time_col]).dt.dayofweek
                        filtered_data['weekday_name'] = pd.to_datetime(filtered_data[time_col]).dt.day_name()

                        # Group by hour - Use explicit column names after agg
                        hour_agg = filtered_data.groupby('hour').agg(交易次数=(pnl_col, 'count')).reset_index()
                        hour_stats = hour_agg.rename(columns={'hour': '小时'})

                        # Group by weekday - Use explicit column names after agg
                        weekday_agg = filtered_data.groupby(['weekday', 'weekday_name']).agg(
                            总盈亏=(pnl_col, 'sum'),
                            平均盈亏=(pnl_col, 'mean'),
                            交易次数=(pnl_col, 'count')
                        ).reset_index()
                        weekday_stats = weekday_agg.rename(columns={'weekday_name': '星期'})
                        weekday_stats = weekday_stats.sort_values('weekday')

                        # Check if dataframes were successfully created before plotting
                        if not hour_stats.empty and not weekday_stats.empty:
                            col1, col2 = st.columns(2)
                            with col1:
                                fig_h = go.Figure(go.Bar(x=hour_stats['小时'], y=hour_stats['交易次数'], name="交易次数", marker_color='royalblue'))
                                fig_h.update_layout(title="小时交易频率", xaxis_title="小时 (0-23)", yaxis_title="交易次数", height=400)
                                st.plotly_chart(fig_h, use_container_width=True, key="strategy_hour_frequency")
                            with col2:
                                fig_w = go.Figure(go.Bar(x=weekday_stats['星期'], y=weekday_stats['交易次数'], name="交易次数", marker_color='royalblue'))
                                fig_w.update_layout(title="星期几交易频率", xaxis_title="星期", yaxis_title="交易次数", height=400)
                                st.plotly_chart(fig_w, use_container_width=True, key="strategy_weekday_frequency")
                            # Weekday PnL Analysis
                            st.markdown('<h4>星期几盈亏情况</h4>', unsafe_allow_html=True)
                            fig_pnl_w = go.Figure()
                            colors = ['green' if pnl >= 0 else 'red' for pnl in weekday_stats['总盈亏']]
                            fig_pnl_w.add_trace(go.Bar(x=weekday_stats['星期'], y=weekday_stats['总盈亏'], marker_color=colors, name="总盈亏"))
                            fig_pnl_w.add_trace(go.Scatter(x=weekday_stats['星期'], y=weekday_stats['平均盈亏'], mode='lines+markers', name="平均盈亏", line=dict(color='purple')))
                            fig_pnl_w.update_layout(title="星期几盈亏分析", xaxis_title="星期", yaxis_title="盈亏", height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                            st.plotly_chart(fig_pnl_w, use_container_width=True, key="strategy_weekday_pnl")
                            st.dataframe(weekday_stats[['星期', '总盈亏', '平均盈亏', '交易次数']], use_container_width=True)
                        else:
                             st.info("无数据可用于频率分析。")

                    except Exception as freq_e:
                        st.error(f"生成交易频率分析时出错: {str(freq_e)}")
                        import traceback
                        st.code(traceback.format_exc(), language="python")
                    
                    # Fee Analysis
                    if fee_stats:
                        st.markdown('<h3 class="sub-header">费用分析</h3>', unsafe_allow_html=True)
                        st.markdown('<div class="fee-stats-container">', unsafe_allow_html=True)
                        display_fee_statistics(fee_stats, key_prefix="strategy_tab_fee_stats")
                        st.markdown('</div>', unsafe_allow_html=True)

                else: st.warning("没有足够的日盈亏数据进行策略评估。")
            except Exception as e: st.error(f"生成策略评估时出错: {str(e)}"); import traceback; st.code(traceback.format_exc(), language="python")

# All pages are done, now add the footer outside the if/elif structure
# 页脚
st.markdown("---")
st.caption("交易数据高级分析系统 © 2025 | 版本 3.1 | 优化了PnL计算机制，支持新数据格式")