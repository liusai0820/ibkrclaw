# IBKR 只读查询 Skill for OpenClaw

> 🔒 **只读安全模式**：此 Skill 仅能查询数据，**无法执行任何交易操作**。

通过 [OpenClaw](https://openclaw.ai) 在 Telegram 中直接查看你的 IBKR 持仓、余额和实时行情。

---

## ⚡ 一键安装（推荐）

直接把以下内容发送给你的 OpenClaw 机器人：

```
请帮我安装这个 Skill：https://github.com/liusai0820/ibkrclaw.git

安装完成后，请运行 setup.sh 完成环境配置，然后告诉我需要在 .env 文件里填写哪些 IBKR 账号信息。
```

OpenClaw 会自动完成所有安装步骤，完成后只需提供你的 **IBKR 账号（用户名）** 和 **密码**。

---

## 📋 前置条件

在开始前，请确认以下条件满足：

| 条件 | 说明 |
|------|------|
| IBKR 账户 | 真实账户或模拟盘均可 |
| IBKR Key App | 安装在手机上，用于 2FA 认证 |
| Java 17+ | 服务器或 Mac 上需要安装 |
| Python 3.9+ | 用于运行查询脚本 |
| Chrome/Chromium | iBeam 自动登录需要 |

---

## 🛠️ 手动安装步骤

如果你想手动安装，按以下步骤操作：

### 第 1 步：克隆此仓库

```bash
git clone https://github.com/liusai0820/ibkrclaw.git
```

### 第 2 步：运行安装脚本

```bash
bash ibkrclaw/scripts/setup.sh
```

脚本会自动完成：
- ✅ 检查 Java、Chrome、Xvfb 环境
- ✅ 下载 IBKR Client Portal Gateway
- ✅ 创建 Python 虚拟环境并安装依赖（`ibeam`, `requests`）
- ✅ 创建 `.env` 配置文件模板
- ✅ 生成 `start-gateway.sh` 和 `authenticate.sh` 快捷脚本

### 第 3 步：填写 IBKR 账号信息

编辑 `~/trading/.env` 文件，填入你的 IBKR 账号：

```bash
# 只需修改这两行
IBEAM_ACCOUNT=你的IBKR用户名
IBEAM_PASSWORD='你的IBKR密码'
```

> ⚠️ **安全提示**：`.env` 文件只保存在本地，不会上传到任何服务器。

### 第 4 步：启动 Gateway

```bash
cd ~/trading
./start-gateway.sh
```

等待约 20 秒让 Gateway 完全启动。

### 第 5 步：认证（需手机确认）

```bash
./authenticate.sh
```

**📱 运行后请立即打开手机上的 IBKR Key App，在 2 分钟内批准登录通知！**

认证成功后，Gateway 会保持运行并自动保活连接。

---

## 💬 在 OpenClaw / Telegram 中使用

安装并认证成功后，直接在 Telegram 中向 OpenClaw 机器人发送以下消息即可：

| 你说的话 | 机器人返回 |
|----------|-----------|
| 我的 IBKR 持仓有哪些？ | 所有持仓、成本价、当前市值、盈亏% |
| 帮我查一下持仓盈亏 | 账户余额 + 持仓盈亏汇总 |
| AAPL 现在多少钱？ | 苹果股票实时价格 |
| 帮我看看 NVDA 和 TSLA 的实时价格 | 批量股票行情查询 |
| 我的账户余额是多少？ | 现金余额、净资产 |

**触发词**：`IBKR`、`盈透`、`持仓`、`股价`、`行情`、`portfolio`

---

## 🔄 会话保活

IBKR 会话默认 24 小时过期。建议设置 cron 任务自动保活：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每 5 分钟执行一次）
*/5 * * * * cd ~/trading && source venv/bin/activate && python /path/to/ibkrclaw/scripts/keepalive.py >> ~/trading/keepalive.log 2>&1
```

---

## 🔧 功能说明

| 功能 | 支持 | 说明 |
|------|------|------|
| 查看持仓 | ✅ | 股票持仓、成本价、市值、盈亏 |
| 查看余额 | ✅ | 现金余额、净资产 |
| 实时行情 | ✅ | 任意股票的实时价格 |
| 批量查询 | ✅ | 同时查询多只股票 |
| 下单 | ❌ | **完全不支持** |
| 修改/取消订单 | ❌ | **完全不支持** |

---

## 🚨 故障排查

| 问题 | 解决方案 |
|------|----------|
| Gateway 无响应 | 检查 Java 进程：`ps aux \| grep GatewayStart` |
| 认证超时 | 未及时批准 IBKR Key，重新运行 `./authenticate.sh` |
| 连接被拒绝 | Gateway 未启动，运行 `./start-gateway.sh` |
| 2FA 失败 | 确认手机上已安装并登录 IBKR Key App |

---

## 🔐 安全说明

- 此 Skill **仅使用 GET 请求**，不调用任何修改账户的 API
- 账号密码存储在本地 `.env` 文件中，不会传输到第三方
- 源代码完全开源，可自行审查
- 即使有人要求下单，此 Skill **技术上无法执行**

---

## 📄 License

MIT License - 自由使用、修改和分发。
