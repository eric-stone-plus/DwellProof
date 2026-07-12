# DwellProof 下次续作备忘

更新时间：2026-07-13

## 从这里恢复

- 源码真相：当前 DwellProof 仓库根目录；不要在公开备忘中固化工作站绝对路径。
- 公开备份：`https://github.com/eric-stone-plus/DwellProof`
- 主分支：`main`；每次恢复先核对本地、`origin/main` 和 GitHub，不依赖文档中易过期的 SHA。
- DwellProof 自有软件和配套文档采用 MIT License；QueryForge/COFORGE 派生设计材料的 Apache-2.0/MIT 通知保存在 `THIRD_PARTY_NOTICES.md`。
- 产品仍是受控原型。当前唯一可靠结论是 `INSUFFICIENT_EVIDENCE`；演示案例的七项标的级门槛均未通过，不得输出估值、NPV、IRR 或买卖建议。

## 当前真实状态

- `core/` 已实现带证据作用域的 readiness、契税、贷款和三情景现金流；最近收口记录为核心测试 `77 / 77`、legacy 回归 `46 / 46`。
- `web/` 是 Next.js 静态专业工作台，当前数据来自 `web/lib/demo-case.ts`。案例草稿只在内存，材料选择只记录文件名、大小和目标门槛，不读取、保存或核验文件内容。
- `src-tauri/` 使用 Tauri 2 和系统 WebView；当前权限列表为空，不含 Node、Chromium、Python 或 Reasonix。macOS 包只是 x86_64、ad-hoc 签名的本机测试件，不能公开分发。
- `core/` 尚未与 Web/Tauri 接通；当前界面是展示壳，不是可执行投资建议系统。
- Reasonix 仅保留未来只读解释接口，不得拥有事实、证据核验、确定性计算、readiness 或建议权。
- Firecrawl 额度为 0；不得把检索缺口写成已验证事实。已知官方页面可直接留存快照，新来源发现需等待可用检索能力或用户明确认可的来源路径。

## 不可回退的准确性边界

- 城市指数只作背景，LPR 只作基准；二者不能替代房源可比成交或借款人的书面执行利率。
- 关键输入必须保留来源、时间、地理及 case/property/borrower 作用域、语义角色、验证/新鲜度和规则版本。
- 缺失、过期、冲突、精度不足或跨案例混用必须 fail closed；前端不得复写税费、贷款和现金流算法，模型不得补齐缺失事实。
- 真实姓名、证件、产权和财务材料不得进入 Git，也不得默认发送给托管模型。

## 尚未完成

- 没有 Web/Tauri 到 Python core 的版本化协议、资源上限或可重放计算快照。
- 没有本地证据库、内容哈希、人工核验、冲突/过期处理和审计日志。
- 没有房源级可比成交、地方税费/交易限制、产权与处分权查询、银行书面报价的可信闭环。
- 缺少完整个案 E2E、新鲜度监控和“来源失效后重新锁定旧结果”的验证。
- 桌面端外链 allowlist、arm64/universal、Developer ID、hardened runtime、公证/stapling 和 Rust advisory scan 尚未完成。

## 下一轮优先级

1. **P0：合成案例最小可信竖切。** 冻结 `sidecar.v1` JSON 输入、输出和错误协议；受限 Python runner 只调用现有 core，输出含证据引用、规则/公式版本、输入摘要和结果摘要的不可变计算快照，并覆盖篡改、过期、冲突、跨作用域和资源上限测试。
2. **P1：本地证据闭环。** 设计 case/evidence/snapshot 存储、显式文件导入、内容哈希、人工验证状态和审计日志；先只使用匿名合成材料。
3. **P2：逐门槛接真实来源。** 优先银行书面报价、地方税费和同小区可比成交，再处理产权/限制材料；每个适配器都必须保存原始快照、来源和时间并支持离线重放。
4. **P3：产品级 E2E。** 覆盖“缺证拒绝 -> 补证 -> core 计算 -> UI 备忘录 -> 来源过期后重新锁定”。
5. **P4：分发与 Reasonix。** 先完成 Apple 双架构签名/公证；Reasonix 只在证据库、只读 API、引用约束、隔离和隐私决策完成后进入 shadow mode。

## 恢复与复核命令

```sh
cd <DwellProof repository>
gh auth status
git status --short --branch
git fetch origin
git rev-parse HEAD origin/main
python3 -m unittest discover -s tests -v
python3 legacy/legacy_test.py
python3 scripts/verify_official_page_hashes.py
python3 scripts/verify_official_70city.py
npm --prefix web audit
npm --prefix web run typecheck
npm --prefix web run build
cargo check --manifest-path src-tauri/Cargo.toml --locked
```

只有需要刷新本机测试包时才运行 `./desktop/build_macos.sh`；该脚本会重建被忽略的 `desktop/dist/`，产物仍然只是本机 ad-hoc 测试件。
