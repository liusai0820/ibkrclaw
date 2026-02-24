#!/usr/bin/env python3
"""
IBKR Read-Only Client - 只读版本
只能查询持仓、余额、实时行情，不能下单！

安全特性：此脚本不包含任何下单、修改订单、取消订单的功能。
"""

import requests
import urllib3
import json
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
BASE_URL = os.getenv("IBEAM_GATEWAY_BASE_URL", "https://localhost:5001")
ACCOUNT_ID = os.getenv("IBKR_ACCOUNT_ID", "")

@dataclass
class Position:
    symbol: str
    conid: int
    quantity: float
    avg_cost: float
    market_value: float
    unrealized_pnl: float
    pnl_percent: float

@dataclass
class Quote:
    conid: int
    symbol: str
    last_price: float
    bid: float
    ask: float
    volume: int
    change: float
    change_pct: float

class IBKRReadOnlyClient:
    """
    IBKR 只读客户端 - 仅查询，无交易功能
    
    ⚠️ 安全说明：此类不包含任何下单、修改、取消订单的方法。
    """
    
    def __init__(self, base_url: str = BASE_URL, account_id: str = ACCOUNT_ID):
        self.base_url = base_url
        self.account_id = account_id
        self.session = requests.Session()
        self.session.verify = False
    
    def _get(self, endpoint: str, params: dict = None) -> dict:
        r = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=15)
        return r.json() if r.text else {}
    
    def is_authenticated(self) -> bool:
        """检查会话是否已认证"""
        try:
            status = self._get("/v1/api/iserver/auth/status")
            return status.get("authenticated", False)
        except:
            return False
    
    def keepalive(self) -> bool:
        """保持会话活跃"""
        try:
            self.session.post(f"{self.base_url}/v1/api/tickle", verify=False, timeout=10)
            return self.is_authenticated()
        except:
            return False
    
    def get_accounts(self) -> List[dict]:
        """获取账户列表"""
        return self._get("/v1/api/portfolio/accounts")
    
    def get_balance(self) -> dict:
        """获取账户余额/总结"""
        return self._get(f"/v1/api/portfolio/{self.account_id}/summary")
    
    def get_positions(self) -> List[Position]:
        """获取当前持仓"""
        data = self._get(f"/v1/api/portfolio/{self.account_id}/positions/0")
        positions = []
        for p in data if isinstance(data, list) else []:
            avg_cost = p.get("avgCost", 0)
            mkt_value = p.get("mktValue", 0)
            quantity = p.get("position", 0)
            unrealized_pnl = p.get("unrealizedPnl", 0)
            
            # 计算盈亏百分比
            cost_basis = avg_cost * quantity if quantity else 0
            pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis else 0
            
            positions.append(Position(
                symbol=p.get("contractDesc", ""),
                conid=p.get("conid", 0),
                quantity=quantity,
                avg_cost=avg_cost,
                market_value=mkt_value,
                unrealized_pnl=unrealized_pnl,
                pnl_percent=pnl_pct
            ))
        return positions
    
    def search_symbol(self, symbol: str) -> Optional[int]:
        """搜索股票代码，返回 conid"""
        data = self._get("/v1/api/iserver/secdef/search", {"symbol": symbol})
        if data and len(data) > 0:
            return data[0].get("conid")
        return None
    
    def get_quote(self, conid: int) -> Optional[Quote]:
        """获取实时行情快照"""
        fields = "31,84,86,87,88,82,83"  # last, bid, ask, volume, close, change, change%
        
        # 首次请求初始化
        self._get("/v1/api/iserver/marketdata/snapshot", {
            "conids": str(conid),
            "fields": fields
        })
        
        # 重试获取数据
        for _ in range(3):
            data = self._get("/v1/api/iserver/marketdata/snapshot", {
                "conids": str(conid),
                "fields": fields
            })
            if data and len(data) > 0:
                d = data[0]
                if d.get("31"):  # 有最新价
                    return Quote(
                        conid=conid,
                        symbol=d.get("symbol", ""),
                        last_price=float(d.get("31", 0)),
                        bid=float(d.get("84", 0)),
                        ask=float(d.get("86", 0)),
                        volume=int(d.get("87", 0)),
                        change=float(d.get("82", 0)),
                        change_pct=float(d.get("83", 0))
                    )
        return None
    
    def get_quotes_batch(self, symbols: List[str]) -> Dict[str, Quote]:
        """批量获取多个股票的实时行情"""
        quotes = {}
        for symbol in symbols:
            conid = self.search_symbol(symbol)
            if conid:
                quote = self.get_quote(conid)
                if quote:
                    quotes[symbol] = quote
        return quotes


def format_currency(value: float) -> str:
    """格式化货币显示"""
    if value >= 0:
        return f"${value:,.2f}"
    else:
        return f"-${abs(value):,.2f}"


def format_pnl(value: float, pct: float) -> str:
    """格式化盈亏显示"""
    sign = "📈" if value >= 0 else "📉"
    color_value = f"+{format_currency(value)}" if value >= 0 else format_currency(value)
    return f"{sign} {color_value} ({pct:+.2f}%)"


def main():
    """主函数 - 展示账户信息"""
    print("🏦 IBKR 只读查询工具")
    print("=" * 50)
    print("⚠️  安全模式：仅查询，无法执行任何交易操作")
    print("=" * 50)
    print()
    
    client = IBKRReadOnlyClient()
    
    if not client.is_authenticated():
        print("❌ 未认证。请先运行认证脚本。")
        print("   提示：检查 IBKR Gateway 是否运行中")
        return
    
    print("✅ 已连接 IBKR Gateway")
    
    # 获取账户信息
    accounts = client.get_accounts()
    if accounts:
        client.account_id = accounts[0]["accountId"]
        print(f"📊 账户: {client.account_id}")
    
    # 获取余额
    balance = client.get_balance()
    cash = balance.get("totalcashvalue", {}).get("amount", 0)
    net_liq = balance.get("netliquidation", {}).get("amount", 0)
    print(f"💵 现金余额: {format_currency(cash)}")
    print(f"💰 净资产: {format_currency(net_liq)}")
    print()
    
    # 获取持仓
    positions = client.get_positions()
    print(f"📈 持仓数量: {len(positions)}")
    print("-" * 50)
    
    total_pnl = 0
    for p in positions:
        total_pnl += p.unrealized_pnl
        pnl_str = format_pnl(p.unrealized_pnl, p.pnl_percent)
        print(f"  {p.symbol}")
        print(f"    数量: {p.quantity:.0f} | 成本: {format_currency(p.avg_cost)} | 市值: {format_currency(p.market_value)}")
        print(f"    盈亏: {pnl_str}")
        print()
    
    print("-" * 50)
    print(f"📊 持仓总盈亏: {format_pnl(total_pnl, (total_pnl/net_liq*100) if net_liq else 0)}")


if __name__ == "__main__":
    main()
