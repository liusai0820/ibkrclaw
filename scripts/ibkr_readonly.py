#!/usr/bin/env python3
"""
IBKR Read-Only Client - 进阶分析版本
查询持仓、余额、实时行情、个股基本面、历史K线、全市场扫描等。
安全特性：此脚本不包含任何下单、修改订单、取消订单的功能。
"""

import requests
import urllib3
import json
import os
import time
from datetime import datetime
import xml.etree.ElementTree as ET
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

@dataclass
class FundamentalData:
    conid: int
    symbol: str
    company_name: str
    industry: str
    category: str
    market_cap: str
    pe_ratio: str
    eps: str
    dividend_yield: str
    high_52w: str
    low_52w: str
    avg_volume: str

class IBKRReadOnlyClient:
    """
    IBKR 只读客户端 - 数据与投研版
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
        
    def _post(self, endpoint: str, json_data: dict = None) -> dict:
        r = self.session.post(f"{self.base_url}{endpoint}", json=json_data, timeout=15)
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
        time.sleep(0.5)
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
                        change_pct=float(d.get("83", 0).replace('%', '')) if str(d.get("83", "0")).replace('%', '') else 0.0
                    )
            time.sleep(1)
        return None
        
    def get_fundamentals(self, conid: int, symbol: str = "") -> Optional[FundamentalData]:
        """获取个股基本面指标和公司业务分类"""
        # 获取公司基础信息 (行业类别, 名字)
        info = self._get(f"/v1/api/iserver/contract/{conid}/info")
        company_name = info.get("company_name", "")
        industry = info.get("industry", "")
        category = info.get("category", "")
        
        # 获取核心财务与市场表现指标
        # 7289: Market Cap, 7290: P/E, 7291: EPS, 7287: Div Yield, 7293: 52w High, 7294: 52w Low, 7282: Avg Volume
        fields = "7289,7290,7291,7287,7293,7294,7282"
        self._get("/v1/api/iserver/marketdata/snapshot", {"conids": str(conid), "fields": fields})
        time.sleep(1)
        
        for _ in range(3):
            data = self._get("/v1/api/iserver/marketdata/snapshot", {"conids": str(conid), "fields": fields})
            if data and len(data) > 0:
                d = data[0]
                return FundamentalData(
                    conid=conid,
                    symbol=symbol,
                    company_name=company_name,
                    industry=industry,
                    category=category,
                    market_cap=str(d.get("7289", "N/A")),
                    pe_ratio=str(d.get("7290", "N/A")),
                    eps=str(d.get("7291", "N/A")),
                    dividend_yield=str(d.get("7287", "N/A")),
                    high_52w=str(d.get("7293", "N/A")),
                    low_52w=str(d.get("7294", "N/A")),
                    avg_volume=str(d.get("7282", "N/A"))
                )
            time.sleep(1)
        return None
        
    def get_historical_data(self, conid: int, period: str = "3m", bar: str = "1d") -> dict:
        """
        获取历史 K 线数据，供趋势分析
        period 可选: 1d, 1w, 1m, 3m, 6m, 1y, 5y
        bar 可选: 1min, 5min, 1h, 1d, 1w, 1m
        """
        return self._get("/v1/api/iserver/marketdata/history", {
            "conid": str(conid),
            "period": period,
            "bar": bar
        })
        
    def run_scanner(self, instrument: str = "STK", scan_type: str = "TOP_PERC_GAIN", location: str = "STK.US.MAJOR", size: int = 10) -> List[dict]:
        """
        全市场智能扫描
        scan_type 可选: 
        - TOP_PERC_GAIN (涨幅榜)
        - TOP_PERC_LOSE (跌幅榜)
        - MOST_ACTIVE (最活跃)
        - HIGH_VS_13W_HL (成交量异动)
        """
        paylod = {
            "instrument": instrument,
            "type": scan_type,
            "filter": [
                {"code": "marketCapAbove", "value": 100000000} # 过滤掉微盘股
            ],
            "location": location,
            "size": str(size)
        }
        return self._post("/v1/api/iserver/scanner/run", json_data=paylod)

    def get_company_news(self, symbol: str, limit: int = 5) -> List[dict]:
        """
        获取公司的最新新闻 (通过 Yahoo Finance 免费 RSS，因为 IBKR News API 通常需要额外付费订阅)
        获取最新的标题和发布时间，供 AI 进行事件驱动的情绪分析。
        """
        try:
            url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                root = ET.fromstring(r.text)
                news = []
                for item in root.findall(".//item")[:limit]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    pubDate = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    news.append({"title": title, "date": pubDate, "link": link})
                return news
        except Exception:
            pass
        return []


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
    print("🏦 IBKR 投研辅助与只读查询工具")
    print("=" * 50)
    print("⚠️  安全模式：仅查询，无法执行任何交易操作")
    print("=" * 50)
    print()
    
    client = IBKRReadOnlyClient()
    
    if not client.is_authenticated():
        print("❌ 未认证。请先在浏览器登录 https://localhost:5001。")
        return
    
    print("✅ 已连接 IBKR Gateway")
    
    # 账户余额与持仓
    accounts = client.get_accounts()
    if accounts:
        client.account_id = accounts[0]["accountId"]
        print(f"📊 账户: {client.account_id}")
    
    balance = client.get_balance()
    cash = balance.get("totalcashvalue", {}).get("amount", 0)
    net_liq = balance.get("netliquidation", {}).get("amount", 0)
    print(f"💵 现金余额: {format_currency(cash)}")
    print(f"💰 净资产: {format_currency(net_liq)}")
    print("-" * 50)
    
    # 测试一下基本面获取功能
    print("🔍 测试获取 AAPL 基本面数据...")
    aapl_conid = client.search_symbol("AAPL")
    if aapl_conid:
        fund = client.get_fundamentals(aapl_conid, "AAPL")
        if fund:
            print(f"🍎 公司: {fund.company_name} | 所属行业: {fund.category} ({fund.industry})")
            print(f"💰 市值: {fund.market_cap} | 市盈率 (P/E): {fund.pe_ratio} | 每股收益 (EPS): {fund.eps}")
            print(f"📈 52周最高: {fund.high_52w} | 52周最低: {fund.low_52w}")
            print(f"💧 股息收益率: {fund.dividend_yield} | 日均成交量: {fund.avg_volume}")
        else:
            print("❌ 获取基本面信息失败")
            
    print("-" * 50)
    print("📰 测试获取 LMND 最新公司新闻事件...")
    news = client.get_company_news("LMND")
    if news:
        for idx, item in enumerate(news):
            print(f"  {idx+1}. [{item['date']}] {item['title']}")
    else:
        print("无最新新闻或获取失败。")
            

if __name__ == "__main__":
    main()
