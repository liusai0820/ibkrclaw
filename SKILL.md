---
name: ibkr-readonly
description: IBKR 只读数据查询（无交易功能）。用于查看持仓、余额、实时行情。触发词：IBKR、盈透、持仓、股价、行情、portfolio。
---

# IBKR 只读查询技能

⚠️ **安全模式**：此技能只能查询数据，**无法执行任何交易操作**。

## 功能

| 功能 | 说明 |
|------|------|
| ✅ 查看持仓 | 显示所有股票持仓、成本、市值、盈亏 |
| ✅ 查看余额 | 显示现金余额、净资产 |
| ✅ 实时行情 | 查询任意股票的实时价格 |
| ✅ 批量查询 | 同时查询多个股票行情 |
| ❌ 下单 | **不支持** |
| ❌ 修改订单 | **不支持** |
| ❌ 取消订单 | **不支持** |

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
- "AAPL 现在多少钱？"
- "帮我看看 NVDA 和 TSLA 的实时价格"

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
