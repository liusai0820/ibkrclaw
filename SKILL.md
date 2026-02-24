---
name: ibkr-readonly
description: IBKR 投资研究与只读查询（无交易功能）。用于投研分析、公司基本面调研、持仓/余额/行情查询。触发词：IBKR、分析公司、盈透、持仓、股价、行情、基本面、财报、投资建议。
---

# IBKR 只读查询技能

⚠️ **安全模式**：此技能只能查询数据，**无法执行任何交易操作**。

## 功能

| 功能 | 说明 |
|------|------|
| ✅ 查看持仓 | 显示所有股票持仓、成本、市值、盈亏 |
| ✅ 查看余额 | 显示现金余额、净资产 |
| ✅ 实时行情 | 查询任意股票的实时价格 |
| ✅ 深度基本面 | **新增**：查询公司市值、P/E市盈率、EPS、股息收益及行业分类 |
| ✅ 历史K线 | **新增**：获取过去 N 天/月/年的价格序列，用于趋势分析 |
| ✅ 市场扫描 | **新增**：查询全市场涨幅榜、跌幅榜及异动榜 |
| ❌ 下单 | **不支持** |
| ❌ 修改订单 | **不支持** |
| ❌ 取消订单 | **不支持** |

## 🤖 AI 助理执业规范 (Agent Execution Protocol)

作为用户的专属量化与投资分析顾问，当你被唤醒执行此技能时，**绝对不能仅仅返回枯燥的数字或不假思索地回答**。你必须执行以下 **“深度投研四步法”**：

1. **提取核心数据 (Data Anchoring)** 
   - 必须通过执行 `/Users/qibaoba/clawd/skills/ibkr-trader/scripts/ibkr_readonly.py` 获取查询标的（如 IBM, LMND 等）的最新基本面指标（P/E，市值，52周高低点）以及最新新闻。
2. **强制全网深度检索 (Mandatory Web Search)** 
   - 单靠 RSS 新闻是不够的！你必须使用你的 `search_web` 工具，去全网搜索该公司的**最新宏观事件、财报会议记录、产品动态及行业竞品动作**（例如：回答 IBM 时，必须要搜索目前 AI 行业如 Anthropic/OpenAI 对其护城河的影响）。
3. **推演与逻辑链 (Chain of Thought & Reasoning)** 
   - 不要只罗列新闻！你要分析这些外部变量（竞品发布、宏观政策）会如何影响公司未来的盈利预期（EPS）和估值（P/E）。分析市场情绪，解释这只股票最近大涨或大跌的**潜在深层逻辑**。
4. **输出高管级研报 (Executive Summary)** 
   - 以专业、条理清晰的格式回复用户。必须包含：`1. 📊 盘面与基本面速览`，`2. 🌪️ 核心事件驱动 (结合 web search 深度信息)`，`3. 🧠 深度竞品与护城河分析`，`4. 💡 总结与投资视角`。

## 前置条件

1. IBKR 账户（真实或模拟盘）
2. 手机安装 IBKR Key App（用于 2FA）
3. Mac 需要 Java 17+ 和 Python 3.9+

## 快速配置

### 1. 安装依赖

```bash
# 安装 Java
brew install openjdk@17

# 创建工作目录
mkdir -p ~/trading && cd ~/trading

# 创建 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install ibeam requests
```

### 2. 下载 IBKR Client Portal Gateway

```bash
cd ~/trading
curl -O https://download2.interactivebrokers.com/portal/clientportal.gw.zip
unzip clientportal.gw.zip -d clientportal
```

### 3. 配置环境变量

创建 `~/trading/.env`：
```bash
IBEAM_ACCOUNT=你的IBKR用户名
IBEAM_PASSWORD='你的密码'
IBEAM_GATEWAY_DIR=/Users/$USER/trading/clientportal
IBEAM_GATEWAY_BASE_URL=https://localhost:5000
```

### 4. 启动 Gateway

```bash
cd ~/trading/clientportal
bash bin/run.sh root/conf.yaml &
```

### 5. 认证（需要手机确认）

```bash
cd ~/trading
source venv/bin/activate
source .env
python -m ibeam --authenticate
```

⚠️ 运行后 2 分钟内需在手机上批准 IBKR Key 通知！

## 使用方法

### 查看持仓和余额

```bash
cd ~/trading && source venv/bin/activate
python /Users/$USER/clawd/skills/ibkr-trader/scripts/ibkr_readonly.py
```

### 在 OpenClaw 中使用

直接在 Telegram 问：
- "我的 IBKR 持仓有哪些？"
- "帮我查一下持仓盈亏"
- "帮我看看苹果 (AAPL) 最近的基本面，市值和市盈率怎么样？"
- "利用 IBKR 历史数据，分析一下 NVDA 最近 3 个月的走势"
- "今天美股涨得最猛的 10 只股票是哪些？"

## 会话保活

IBKR 会话 24 小时后过期。使用 keepalive 脚本保持连接：

```bash
# 每 5 分钟运行一次
*/5 * * * * cd ~/trading && source venv/bin/activate && python /path/to/keepalive.py
```

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| Gateway 无响应 | 检查 Java 进程：`ps aux \| grep GatewayStart` |
| 认证超时 | 用户未及时批准 IBKR Key，重试认证 |
| 连接被拒绝 | Gateway 未启动，运行 `bin/run.sh root/conf.yaml` |

## 安全说明

此技能设计为**完全只读**：
- 源代码中不包含任何下单 API 调用
- 即使有人要求下单，技能也无法执行
- 所有查询都通过 GET 请求，不修改任何账户状态
