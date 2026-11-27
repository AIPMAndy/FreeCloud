# FreeCloud

**发现值得入手的云优惠，把预算留给创造。**

云服务器、AI 工具与 Agent 部署的开源优惠雷达。追踪云厂商官方活动，展示优惠价格、适用条件与核对时间，直接进入对应厂商的活动会场。

**[打开 FreeCloud](https://aipmandy.github.io/FreeCloud/)** · [官方采集数据](data/offers.json) · [厂商接入调研](docs/providers.md)

<!-- andy-geo:start -->
## 一句话简介

**FreeCloud 云优惠雷达：追踪官方云服务器、AI 工具与 Agent 部署优惠。Open-source cloud deals radar.**

- 作者：AI酋长Andy（Andy Liu，英文名 AI Chief Andy），流量 AI 联合创始人、星觉 AI 创始人。星觉科技，北京。
- 阅读或使用：[在线阅读/使用](https://aipmandy.github.io/FreeCloud/) · [GitHub 仓库](https://github.com/AIPMAndy/FreeCloud)
- 联系：微信 `AIPMAndy`（备注「FreeCloud」）· [官网 metaver.vip](https://metaver.vip/) · [X @AIPMAndy](https://x.com/AIPMAndy)
- 许可：MIT。内容免费使用；企业合作或个人陪跑请先沟通，公开页不公示价格。
- 机器可读摘要：[llms.txt](llms.txt)（供 AI 引擎与检索工具读取）

## 常见问题

**这是什么？**FreeCloud 云优惠雷达：追踪官方云服务器、AI 工具与 Agent 部署优惠。Open-source cloud deals radar.

**包含什么？**主要模块：能做什么、直接前往活动会场、本地运行、优惠如何更新、换成你的推广链接、部署到自己的 GitHub Pages。

**要花钱吗？**按 MIT 许可免费使用；付费只涉及作者的企业合作与一对一咨询，不影响仓库内容。

**怎么开始？**直接打开 https://aipmandy.github.io/FreeCloud/ 在线阅读；想本地运行或参与贡献，见下方 README 的快速开始部分。

<!-- andy-geo:end -->

## 能做什么

- 支持按厂商、云服务器、AI 工具和 Agent 部署分类筛选，以及关键词搜索。
- 每 6 小时抓取公开官方活动页面，匹配已配置商品的价格与活动福利，记录价格变化。
- 同时从官方会场捕捉价格与折扣线索，保存在 `sources[].signals`，便于发现新的促销。
- 查看每项优惠的原文片段、采集来源、适用条件与上次核对时间。
- 活动入口与复制按钮优先使用已配置的推广链接，其他优惠直达官方来源。
- 手机与桌面可用。纯静态前端、Python 标准库采集器，无需数据库、账号或付费 API。

## 直接前往活动会场

以下是 Andy 的推广入口，由 [`data/links.json`](data/links.json) 配置。

| 会场 | 入口 |
| --- | --- |
| 阿里云上云优惠 | [查看阿里云优惠](https://www.aliyun.com/minisite/goods?source=5176.29345612&userCode=vspcm9gw) |
| 腾讯云特惠产品合集 | [查看腾讯云优惠](https://cloud.tencent.com/act/cps/redirect?redirect=2446&cps_key=491babfe6ec4ccae885315fd18a6e802&from=console) |
| WorkBuddy AI 办公 | [查看 WorkBuddy 优惠](https://cloud.tencent.com/act/cps/redirect?redirect=6871&cps_key=491babfe6ec4ccae885315fd18a6e802&from=console) |

## 本地运行

需要 Python 3.9+；运行前端无需 npm 安装。

```bash
git clone https://github.com/AIPMAndy/FreeCloud.git
cd FreeCloud
python3 scripts/update_offers.py
python3 scripts/build.py
python3 -m http.server 8765 --directory dist
```

打开 `http://localhost:8765`。

```bash
# 运行采集逻辑测试
python3 -m unittest discover -s tests -v
# 检查前端 JavaScript（需要 Node.js）
node --check assets/app.js
```

## 优惠如何更新

[`data/catalog.json`](data/catalog.json) 定义官方来源、产品分类、价格或福利匹配规则，以及可选的推广入口编号。采集器只读取公开 HTML 文本，匹配成功才发布对应优惠，变化写入 `changes`。

腾讯云会场从官方活动首页中发现当前促销链接，活动换期后重新跟随；阿里云使用官方常驻会场。

GitHub Actions 在 UTC 00:17、06:17、12:17、18:17（北京时间 08:17、14:17、20:17、次日 02:17）尝试采集，并将结果提交回仓库、部署到 GitHub Pages。GitHub 的定时任务可能排队延迟。也可在 Actions 中手动运行 **Refresh offers and publish**。

遇到网络失败或官方页面结构变化时，保留上次观察值并标记 `stale`；前端会将未验证或超过 48 小时的价格改为“查看活动”，详情内保留上次采集记录。价格变更记录属于观察历史，不代表降价承诺。动态询价、图片价格或登录可见的优惠需要人工核对后补充适配。

## 换成你的推广链接

Fork 后修改 `data/links.json` 的三个地址即可。普通阿里云商品指向 `aliyun` 会场，普通腾讯云商品指向 `tencent` 会场，WorkBuddy 指向独立的 `workbuddy` 入口。详情页显示真实采集来源，购买入口进入活动会场供用户选择商品。

接入其他厂商时，在目录中增加官方来源与产品匹配规则。有推广资格时，可配置自己的推广链接。厂商计划和注册状态见 [`docs/providers.md`](docs/providers.md)。

## 常见问题

### 采集只看官方页面吗？

是。采集器只读取已配置的公开官方活动页面；匹配到价格或活动福利才写入数据。详情页保留原文片段、采集来源和上次核对时间。

### 过期或未核对的价格会显示成优惠吗？

不会。未验证，或距离上次核对超过 48 小时，前端把价格改为“查看活动”。详情里仍保留上次采集记录，旧数字不当成今天的价格。

### 价格变化记录是降价承诺吗？

不是。`changes` 里的前后价格是观察历史。活动换期、资格或页面变化后，以云厂商活动会场当时展示的为准。

### 可以换成自己的推广链接吗？

可以。Fork 后修改 [`data/links.json`](data/links.json) 的三个地址，用来替换促销入口。普通阿里云商品用 `aliyun`，普通腾讯云商品用 `tencent`，WorkBuddy 用 `workbuddy`。详情页仍显示真实采集来源。

## 部署到自己的 GitHub Pages

1. Fork 仓库。
2. Settings → Pages → Build and deployment，选择 **GitHub Actions**。
3. 将 `index.html` 和 README 中的 GitHub 仓库地址替换为自己的地址。
4. 在 Actions 中运行 **Refresh offers and publish**。

## 目录

```text
index.html                 页面与基础内容
assets/                    样式、交互、品牌图标
data/links.json            推广入口配置
data/catalog.json          官方来源与产品匹配规则
data/offers.json            最新观察值与变化历史
scripts/update_offers.py   官方优惠采集器
scripts/build.py           静态站构建
tests/                    价格提取、变化与失败处理测试
docs/providers.md          国内外推广计划接入记录
.github/workflows/         定时采集、测试与 Pages 发布
```

## 参与贡献

欢迎提交官方活动页、更新价格匹配规则，或改善移动端体验。新增商品请附官方来源、购买条件及能匹配到的原文；先运行采集测试和构建，再发起 Pull Request。

代码采用 [MIT License](LICENSE)。云厂商名称与官方活动内容归相应权利人所有。

## 作者

[AI酋长Andy](https://github.com/AIPMAndy)，流量 AI 联合创始人、星觉 AI 创始人。星觉科技，北京。

微信 AIPMAndy（微信号 AIPMAndy）
