"""
Trading Strategy Module
交易策略模块 - 集中管理所有交易策略和入场条件

使用方法:
    from backend.services.strategy_service import TradingStrategy
    
    strategy = TradingStrategy()
    should_enter, reason = strategy.evaluate_entry(screening_result, account_config)
"""

from typing import Dict, Tuple, List
from dataclasses import dataclass
from datetime import datetime
import pytz


@dataclass
class StrategyConfig:
    """策略配置"""
    # 分数阈值
    entry_score_min: float = 70.0          # 最低入场分数
    entry_technical_min: float = 50.0      # 最低技术分数
    
    # 时间窗口加分
    time_window_bonus: float = 5.0         # 优选时段加分
    
    # 爆量突破配置
    volume_breakout_min_score: float = 60.0  # 爆量突破最低分数
    
    # 信号要求（可选）
    require_macd_golden: bool = False      # 是否要求MACD金叉
    require_above_ema: bool = False        # 是否要求价格在EMA之上
    require_volume_surge: bool = False     # 是否要求爆量


class TradingStrategy:
    """
    交易策略类
    
    入场条件（满足任一即可）:
    1. 高分入场: 调整后分数 >= entry_score_min
    2. 爆量突破: volume_surge=True 且 分数 >= volume_breakout_min_score
    """
    
    def __init__(self, config: StrategyConfig = None):
        self.config = config or StrategyConfig()
        self.beijing_tz = pytz.timezone('Asia/Shanghai')
        
        # 优选交易时间段（北京时间）
        self.preferred_windows = [
            (7, 30, 8, 30),    # 7:30-8:30
            (11, 30, 12, 30),  # 11:30-12:30
            (15, 30, 16, 30),  # 15:30-16:30
        ]
    
    def is_in_preferred_window(self) -> bool:
        """检查当前是否在优选交易时段"""
        now = datetime.now(self.beijing_tz)
        current_minutes = now.hour * 60 + now.minute
        
        for start_h, start_m, end_h, end_m in self.preferred_windows:
            start = start_h * 60 + start_m
            end = end_h * 60 + end_m
            if start <= current_minutes <= end:
                return True
        return False
    
    def get_time_bonus(self) -> float:
        """获取当前时段的加分"""
        if self.is_in_preferred_window():
            return self.config.time_window_bonus
        return 0.0
    
    def evaluate_entry(
        self,
        screening_result: Dict,
        account_config: Dict = None,
        time_bonus: float = None
    ) -> Tuple[bool, str, Dict]:
        """
        评估是否应该入场
        
        Args:
            screening_result: 筛选结果字典
            account_config: 账户配置（可覆盖默认策略配置）
            time_bonus: 时间加分（如果为None，自动计算）
        
        Returns:
            (should_enter, reason, details)
        """
        # 合并配置
        config = self.config
        if account_config:
            entry_score_min = account_config.get('entry_score_min', config.entry_score_min)
        else:
            entry_score_min = config.entry_score_min
        
        # 计算时间加分
        if time_bonus is None:
            time_bonus = self.get_time_bonus()
        
        # 获取关键指标
        total_score = screening_result.get('total_score', 0)
        volume_surge = screening_result.get('volume_surge', False)
        
        # 计算调整后分数
        adjusted_score = total_score + time_bonus
        
        # 评估入场条件
        high_score_entry = adjusted_score >= entry_score_min
        volume_breakout = volume_surge and total_score >= config.volume_breakout_min_score
        
        # 构建详情
        details = {
            'original_score': total_score,
            'time_bonus': time_bonus,
            'adjusted_score': adjusted_score,
            'entry_threshold': entry_score_min,
            'volume_surge': volume_surge,
            'high_score_entry': high_score_entry,
            'volume_breakout': volume_breakout,
            'in_preferred_window': time_bonus > 0,
        }
        
        # 判断是否入场
        should_enter = high_score_entry or volume_breakout
        
        if not should_enter:
            if time_bonus > 0:
                reason = f"Score {total_score:.1f}+{time_bonus}={adjusted_score:.1f} < {entry_score_min}, no surge"
            else:
                reason = f"Score {total_score:.1f} < {entry_score_min}, no volume surge"
            return False, reason, details
        
        # 构建入场原因
        signals = []
        if high_score_entry:
            if time_bonus > 0:
                signals.append(f"高分{total_score:.1f}+{time_bonus}")
            else:
                signals.append(f"高分{adjusted_score:.1f}")
        if volume_surge:
            signals.append('爆量突破')
        if screening_result.get('macd_golden_cross'):
            signals.append('MACD金叉')
        if screening_result.get('above_all_ema'):
            signals.append('EMA多头')
        
        reason = f"Entry: {', '.join(signals)}"
        return True, reason, details
    
    def get_entry_summary(self, screening_results: List[Dict]) -> Dict:
        """
        批量评估筛选结果，返回入场机会摘要
        
        Args:
            screening_results: 筛选结果列表
        
        Returns:
            {
                'qualified': [...],  # 符合入场条件的结果
                'rejected': [...],   # 不符合的结果
                'time_bonus': float,
                'in_preferred_window': bool
            }
        """
        time_bonus = self.get_time_bonus()
        qualified = []
        rejected = []
        
        for result in screening_results:
            should_enter, reason, details = self.evaluate_entry(result, time_bonus=time_bonus)
            entry_info = {
                'symbol': result.get('symbol'),
                'score': result.get('total_score'),
                'adjusted_score': details['adjusted_score'],
                'reason': reason,
                'volume_surge': result.get('volume_surge', False),
            }
            if should_enter:
                qualified.append(entry_info)
            else:
                rejected.append(entry_info)
        
        return {
            'qualified': qualified,
            'rejected': rejected,
            'time_bonus': time_bonus,
            'in_preferred_window': time_bonus > 0,
        }


# 便捷函数
def create_strategy(
    entry_score_min: float = 70.0,
    time_window_bonus: float = 5.0,
    volume_breakout_min_score: float = 60.0
) -> TradingStrategy:
    """创建交易策略实例"""
    config = StrategyConfig(
        entry_score_min=entry_score_min,
        time_window_bonus=time_window_bonus,
        volume_breakout_min_score=volume_breakout_min_score,
    )
    return TradingStrategy(config)


# 默认策略实例
default_strategy = TradingStrategy()
