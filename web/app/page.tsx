"use client";

import { useEffect, useState } from "react";
import {
  AlertIcon,
  CalculatorIcon,
  ChevronIcon,
  DatabaseIcon,
  FileIcon,
  HomeIcon,
  LinkIcon,
  MoonIcon,
  ShieldIcon,
  SunIcon,
} from "@/components/icons";

type Status = "verified" | "partial" | "missing" | "stale";
type Panel = "memo" | "evidence" | "calculation";

const statusLabels: Record<Status, string> = {
  verified: "已核实",
  partial: "部分核实",
  missing: "缺失",
  stale: "可能过期",
};

const evidence = [
  { title: "产权人与处分权", status: "missing" as Status, detail: "缺不动产查档与共有人材料", owner: "交易前人工核验" },
  { title: "抵押 / 查封 / 异议 / 居住权", status: "missing" as Status, detail: "未取得当日登记状态", owner: "定金前重新查验" },
  { title: "房屋性质与交易限制", status: "missing" as Status, detail: "土地用途、年限与限制未核", owner: "核对权证与当地规则" },
  { title: "租赁、户口与学位占用", status: "missing" as Status, detail: "交付与占用状态未核", owner: "写入合同并交叉验证" },
  { title: "地方税费与计税基础", status: "missing" as Status, detail: "仅全国优惠契税规则已确认，标的税费未核", owner: "当地税务窗口复核" },
  { title: "银行书面贷款报价", status: "missing" as Status, detail: "不得以 LPR 代替执行利率", owner: "上传预审批结果" },
  { title: "同小区可比成交", status: "missing" as Status, detail: "近 6 个月有效样本为 0", owner: "至少补充 3 笔" },
];

const cashFlowEvidence = [
  { title: "租金与空置", detail: "当前为演示假设；需补租约或可比租赁" },
  { title: "物业、维修与退出成本", detail: "尚无标的级账单或当地报价" },
];

const sources = [
  {
    title: "全国住房交易契税规则",
    authority: "财政部 / 税务总局 / 住建部",
    status: "verified" as Status,
    observed: "生效 2024-12-01",
    checked: "核验 2026-07-12",
    url: "https://guangdong.chinatax.gov.cn/gdsw/zjfg/2024-11/14/content_0289c52475614b0c9d89145c43310721.shtml",
  },
  {
    title: "2026-04 城市价格指数",
    authority: "国家统计局原表 · 五城逐项匹配",
    status: "verified" as Status,
    observed: "观察期 2026-04",
    checked: "核验 2026-07-12",
    url: "https://www.stats.gov.cn/sj/zxfb/202605/t20260518_1963715.html",
  },
  {
    title: "五年期以上 LPR",
    authority: "中国人民银行 2026-06-22 公告",
    status: "verified" as Status,
    observed: "3.5% · 仅为定价基准",
    checked: "仍缺用户银行执行利率",
    url: "https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125440/3876551/2026062208495122562/index.html",
  },
];

const scenarioRows = [
  { name: "保守", price: "-5.0%/年", vacancy: "3 个月", exit: "9 个月", result: "锁定" },
  { name: "基准", price: "0.0%/年", vacancy: "1 个月", exit: "6 个月", result: "锁定" },
  { name: "乐观", price: "+3.0%/年", vacancy: "1 个月", exit: "3 个月", result: "锁定" },
];

function StatusDot({ status }: { status: Status }) {
  return <span className={`status-dot status-${status}`} aria-hidden="true" />;
}

function StatusBadge({ status }: { status: Status }) {
  return <span className={`status-badge status-${status}`}><StatusDot status={status} />{statusLabels[status]}</span>;
}

function MetricCard({ label, value, note, status, icon }: { label: string; value: string; note: string; status: Status; icon: React.ReactNode }) {
  return (
    <article className="metric-card">
      <div className="metric-icon">{icon}</div>
      <div className="metric-copy">
        <p>{label}</p>
        <strong>{value}</strong>
        <span><StatusDot status={status} />{note}</span>
      </div>
    </article>
  );
}

export default function Home() {
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const [panel, setPanel] = useState<Panel>("memo");
  const [detailsOpen, setDetailsOpen] = useState(false);

  useEffect(() => {
    const saved = (window.localStorage.getItem("dwellproof-theme") ??
      window.localStorage.getItem("house-theme")) as "light" | "dark" | null;
    const initial = saved ?? "dark";
    window.localStorage.setItem("dwellproof-theme", initial);
    setTheme(initial);
    document.documentElement.dataset.theme = initial;
  }, []);

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.dataset.theme = next;
    window.localStorage.setItem("dwellproof-theme", next);
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="topbar">
          <div className="brand-block">
            <div className="brand-mark"><HomeIcon /></div>
            <div>
              <div className="brand-line"><h1>DwellProof</h1><span>LOCAL CASE</span></div>
              <p>二手房投资证据工作台</p>
            </div>
          </div>
          <div className="topbar-actions">
            <div className="source-health"><StatusDot status="verified" /><span>官方快照</span><strong>3 项已核</strong></div>
            <button className="icon-button" onClick={toggleTheme} aria-label={theme === "dark" ? "切换到浅色模式" : "切换到深色模式"}>
              {theme === "dark" ? <SunIcon /> : <MoonIcon />}
            </button>
          </div>
        </header>

        <div className="prototype-banner"><strong>受控原型</strong><span>以下标的与金额均为演示输入，不代表实时市场事实。任何关键证据缺失时，系统锁定方向性建议。</span></div>

        <section className="metrics-grid" aria-label="分析状态">
          <MetricCard label="关键检查通过" value="0 / 7" note="7 项仍阻断分析" status="missing" icon={<ShieldIcon />} />
          <MetricCard label="估值状态" value="暂不可用" note="缺少可比成交" status="missing" icon={<DatabaseIcon />} />
          <MetricCard label="全成本状态" value="待复核" note="地方税费与贷款缺失" status="partial" icon={<CalculatorIcon />} />
          <MetricCard label="建议状态" value="证据不足" note="INSUFFICIENT_EVIDENCE" status="missing" icon={<AlertIcon />} />
        </section>

        <nav className="mobile-tabs" aria-label="工作台视图">
          {(["memo", "evidence", "calculation"] as Panel[]).map((item) => (
            <button key={item} className={panel === item ? "active" : ""} onClick={() => setPanel(item)}>
              {item === "memo" ? "备忘录" : item === "evidence" ? "证据" : "计算"}
            </button>
          ))}
        </nav>

        <div className="workbench-grid">
          <aside className={`case-sidebar mobile-panel ${panel === "evidence" ? "mobile-active" : ""}`}>
            <div className="panel-heading"><span>分析标的</span><button>新建案例</button></div>
            <button className="case-item active">
              <span className="case-code">GZ</span>
              <span><strong>广州 · 天河</strong><small>演示标的 · 证据收集中</small></span>
              <StatusDot status="missing" />
            </button>
            <button className="case-item muted" disabled>
              <span className="case-code">+</span>
              <span><strong>添加实际标的</strong><small>从地址与产权材料开始</small></span>
            </button>

            <div className="sidebar-section">
              <div className="section-label">标的摘要</div>
              <dl className="property-facts">
                <div><dt>城市 / 区域</dt><dd>广州 / 天河</dd></div>
                <div><dt>建筑面积</dt><dd>89 m2</dd></div>
                <div><dt>演示要约</dt><dd>520 万元</dd></div>
                <div><dt>持有周期</dt><dd>5 年</dd></div>
              </dl>
              <p className="input-warning">以上是界面演示输入，尚未由文件或市场数据核实。</p>
            </div>

            <div className="sidebar-section grow">
              <div className="section-label">关键证据</div>
              <div className="evidence-list">
                {evidence.map((item) => (
                  <div className="evidence-row" key={item.title}>
                    <StatusDot status={item.status} />
                    <div><strong>{item.title}</strong><small>{item.detail}</small></div>
                  </div>
                ))}
              </div>
              <div className="section-label supporting-label">现金流材料</div>
              <div className="evidence-list">
                {cashFlowEvidence.map((item) => (
                  <div className="evidence-row" key={item.title}>
                    <StatusDot status="missing" />
                    <div><strong>{item.title}</strong><small>{item.detail}</small></div>
                  </div>
                ))}
              </div>
            </div>
            <button className="secondary-action"><FileIcon />补充证据材料</button>
          </aside>

          <section className={`memo-panel mobile-panel ${panel === "memo" ? "mobile-active" : ""}`}>
            <div className="memo-header">
              <div>
                <span className="eyebrow">CASE GZ-DEMO-001 · REVISION 0</span>
                <h2>标的投资决策备忘录</h2>
                <p>基准日 2026-07-12 · 规则版本 CN-DEED-TAX-2024-12-01-v1 · 演示数据</p>
              </div>
              <button className="ghost-button"><FileIcon />导出锁定</button>
            </div>

            <div className="decision-lock">
              <div className="lock-icon"><AlertIcon /></div>
              <div>
                <span>当前结论</span>
                <h3>暂不形成买入建议</h3>
                <p>产权负担、可比成交、地方税费及银行书面贷款报价缺失。补齐前只提供风险线索和核验清单。</p>
              </div>
              <span className="lock-code">INSUFFICIENT_EVIDENCE</span>
            </div>

            <section className="memo-section">
              <div className="section-title"><div><span>01</span><h3>价格与估值</h3></div><StatusBadge status="missing" /></div>
              <div className="value-grid">
                <div className="value-card"><span>演示要约</span><strong>520 万元</strong><small>用户输入 · 未核实</small></div>
                <div className="value-card locked"><span>可比成交中位数</span><strong>等待样本</strong><small>至少 3 笔合格成交</small></div>
                <div className="value-card locked"><span>合理价格区间</span><strong>暂不输出</strong><small>禁止用城市指数代替估值</small></div>
              </div>
              <div className="method-note"><DatabaseIcon /><span>城市二手住宅价格指数只作为市场背景，不参与生成单套房伪精确估值。</span></div>
            </section>

            <section className="memo-section">
              <div className="section-title"><div><span>02</span><h3>全周期现金流情景</h3></div><StatusBadge status="partial" /></div>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>情景</th><th>售价变化假设</th><th>年空置</th><th>退出周期</th><th>杠杆 IRR</th></tr></thead>
                  <tbody>
                    {scenarioRows.map((row) => <tr key={row.name}><td><strong>{row.name}</strong></td><td>{row.price}</td><td>{row.vacancy}</td><td>{row.exit}</td><td><span className="locked-result">{row.result}</span></td></tr>)}
                  </tbody>
                </table>
              </div>
              <p className="scenario-caption">情景假设可编辑；结果因贷款执行利率、地方税费和可比租金未核实而锁定。</p>
            </section>

            <section className="memo-section">
              <div className="section-title"><div><span>03</span><h3>阻断项与最迟核验节点</h3></div><span className="count-pill">7 个阻断项</span></div>
              <div className="risk-grid">
                {evidence.map((item, index) => (
                  <article className="risk-card" key={item.title}>
                    <div><span>P0{index + 1}</span><StatusDot status={item.status} /></div>
                    <h4>{item.title}</h4>
                    <p>{item.detail}</p>
                    <small>{item.owner}</small>
                  </article>
                ))}
              </div>
            </section>

            <button className="calculation-disclosure" onClick={() => setDetailsOpen((open) => !open)} aria-expanded={detailsOpen}>
              <span><CalculatorIcon /><span><strong>查看计算与规则边界</strong><small>公式、版本、拒答条件与未核假设</small></span></span>
              <ChevronIcon className={detailsOpen ? "rotated" : ""} />
            </button>
            {detailsOpen && (
              <div className="formula-panel">
                <code>net_rental_yield = net_annual_rent / total_acquisition_cost</code>
                <code>cash_flow[t] = rent - vacancy - operating_cost - debt_service</code>
                <code>analysis_ready = all(seven_checks == VERIFIED_CLEAR)</code>
                <p>模型不得补齐缺失利率、税率、产权状态或成交样本。任一关键事实冲突时停止计算。</p>
              </div>
            )}
          </section>

          <aside className={`source-sidebar mobile-panel ${panel === "calculation" ? "mobile-active" : ""}`}>
            <div className="panel-heading"><span>来源与监控</span><button>规则说明</button></div>
            <div className="source-summary">
              <div><ShieldIcon /><span><strong>3 个官方快照已核实</strong><small>0 个标的级关键检查通过</small></span></div>
              <div className="source-bar"><span className="snapshot-bar" /></div>
            </div>
            <div className="section-label">数据来源</div>
            <div className="source-list">
              {sources.map((source) => (
                <article className="source-card" key={source.title}>
                  <div><StatusBadge status={source.status} /><a href={source.url} target="_blank" rel="noreferrer" aria-label={`打开${source.title}官方来源`}><LinkIcon /></a></div>
                  <h4>{source.title}</h4>
                  <p>{source.authority}</p>
                  <dl><div><dt>观察期</dt><dd>{source.observed}</dd></div><div><dt>状态</dt><dd>{source.checked}</dd></div></dl>
                </article>
              ))}
            </div>

            <div className="section-label monitor-label">核验监控</div>
            <div className="monitor-list">
              <div><span className="monitor-index">01</span><span><strong>扩展 70 城全量自动核验</strong><small>当前已核北京、上海、广州、深圳、武汉</small></span><StatusDot status="partial" /></div>
              <div><span className="monitor-index">02</span><span><strong>签约前复核当地税费</strong><small>税务窗口 / 官方系统</small></span><StatusDot status="partial" /></div>
              <div><span className="monitor-index">03</span><span><strong>定金前重新查档</strong><small>旧查档不保证当前状态</small></span><StatusDot status="missing" /></div>
            </div>
            <div className="sidebar-footer"><AlertIcon /><p>辅助决策，不构成法定房地产评估、法律税务意见或银行授信承诺。</p></div>
          </aside>
        </div>
      </section>
    </main>
  );
}
