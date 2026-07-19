"use client";

import type { EvidenceGate, OfficialSource, WorkspaceId } from "@/lib/demo-case";
import { caseFacts, scenarioRows } from "@/lib/demo-case";
import {
  AlertIcon,
  ArrowIcon,
  CalculatorIcon,
  ChartIcon,
  CheckIcon,
  ClockIcon,
  DatabaseIcon,
  FileIcon,
  LinkIcon,
  LockIcon,
  ShieldIcon,
  SparkIcon,
  UploadIcon,
} from "@/components/icons";
import { StatusChip, StatusDot } from "@/components/status";

type SharedProps = {
  gates: EvidenceGate[];
  selectedGate: EvidenceGate;
  onGateSelect: (gateId: string) => void;
  onWorkspaceChange: (workspace: WorkspaceId) => void;
  onUpload: () => void;
  onPrint: () => void;
  onAskAssistant?: (question: string) => void;
  pendingCount: number;
  sources: OfficialSource[];
};

function WorkspaceHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="workspace-header">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </header>
  );
}

function DecisionGate({
  onUpload,
  onAskAssistant,
}: {
  onUpload: () => void;
  onAskAssistant?: (question: string) => void;
}) {
  return (
    <section className="decision-gate" aria-labelledby="decision-gate-title">
      <div className="decision-icon"><LockIcon /></div>
      <div className="decision-copy">
        <span>DECISION GATE · CLOSED</span>
        <h2 id="decision-gate-title">证据不足，暂不形成投资建议</h2>
        <p>七项标的级准入检查均未通过。系统可以整理缺口和规则边界，但不会输出价格区间、IRR 或买入结论。</p>
      </div>
      <div className="decision-actions">
        <code>INSUFFICIENT_EVIDENCE</code>
        <button className="button-primary" type="button" onClick={onUpload}><UploadIcon />继续补证</button>
        {onAskAssistant && (
          <button
            className="button-secondary"
            type="button"
            onClick={() => onAskAssistant("请解释当前七项准入检查各自的缺口，并按交易风险给出最优先的三件事。")}
          >
            <SparkIcon />解释缺口
          </button>
        )}
      </div>
    </section>
  );
}

function OverviewPanel(props: SharedProps) {
  const priority = props.gates.slice(0, 3);
  return (
    <>
      <WorkspaceHeader
        eyebrow="CASE GZ-DEMO-001 · REVISION 0"
        title="案例概览"
        description="广州 · 天河演示标的 · 基准日 2026-07-12 · 所有金额均为未核演示输入"
        action={<StatusChip status="user_input" label="演示案例" />}
      />
      <DecisionGate onUpload={props.onUpload} onAskAssistant={props.onAskAssistant} />

      <section className="readiness-grid" aria-label="分析完整度">
        <article>
          <span className="metric-glyph warning"><ShieldIcon /></span>
          <div><small>法律与交易证据</small><strong>0 / 4</strong><p>产权、负担、性质、占用均待补证</p></div>
        </article>
        <article>
          <span className="metric-glyph warning"><DatabaseIcon /></span>
          <div><small>可比估值样本</small><strong>0 / 3+</strong><p>没有可归属的近期真实成交</p></div>
        </article>
        <article>
          <span className="metric-glyph warning"><CalculatorIcon /></span>
          <div><small>成本与融资输入</small><strong>0 / 2</strong><p>地方税费与银行执行利率缺失</p></div>
        </article>
        <article>
          <span className="metric-glyph accent"><FileIcon /></span>
          <div><small>待核验材料</small><strong>{props.pendingCount}</strong><p>添加材料不会自动晋级为已核实</p></div>
        </article>
      </section>

      <div className="overview-columns">
        <section className="panel-card next-actions">
          <div className="panel-title">
            <div><span className="title-icon"><ClockIcon /></span><span><strong>现在先做什么</strong><small>按交易风险与最迟节点排序</small></span></div>
            <em>3 项最高优先级</em>
          </div>
          <div className="action-list">
            {priority.map((gate, index) => (
              <button key={gate.id} type="button" onClick={() => {
                props.onGateSelect(gate.id);
                props.onWorkspaceChange("evidence");
              }}>
                <span className="action-index">0{index + 1}</span>
                <span><strong>{gate.title}</strong><small>{gate.reason}</small></span>
                <span className="action-deadline">{gate.deadline}<ArrowIcon /></span>
              </button>
            ))}
          </div>
        </section>

        <section className="panel-card fact-register">
          <div className="panel-title">
            <div><span className="title-icon"><FileIcon /></span><span><strong>案例事实登记</strong><small>事实与用户输入必须分开</small></span></div>
            <StatusChip status="user_input" />
          </div>
          <dl>
            {caseFacts.map((fact) => (
              <div key={fact.label}><dt>{fact.label}</dt><dd>{fact.value}</dd><StatusDot status={fact.status} /></div>
            ))}
          </dl>
          <p className="inline-notice"><AlertIcon />当前值只用于界面演示，未绑定原始材料，不会进入确定性计算。</p>
        </section>
      </div>

      <section className="panel-card source-boundary-strip">
        <div><span className="title-icon"><LinkIcon /></span><span><strong>规则库有 3 个官方快照</strong><small>它们证明规则与城市背景，不证明本套房状态</small></span></div>
        <button type="button" onClick={() => props.onWorkspaceChange("memo")}>查看来源边界<ArrowIcon /></button>
      </section>
    </>
  );
}

function EvidencePanel(props: SharedProps) {
  return (
    <>
      <WorkspaceHeader
        eyebrow="DUE DILIGENCE · 7 REQUIRED GATES"
        title="证据室"
        description="选择检查项查看材料要求。状态只由可追溯证据和人工核验改变。"
        action={<button className="button-primary" type="button" onClick={props.onUpload}><UploadIcon />添加材料</button>}
      />
      <section className="evidence-summary-banner">
        <div><ShieldIcon /><span><strong>0 项通过 · 7 项待补证</strong><small>任何一项缺失、过期或冲突都会关闭方向性输出。</small></span></div>
        <div className="progress-track" role="progressbar" aria-label="七项检查通过零项" aria-valuemin={0} aria-valuemax={7} aria-valuenow={0}><span style={{ width: "0%" }} /></div>
      </section>
      <section className="evidence-table-card">
        <div className="evidence-table-head">
          <span>检查项</span><span>当前状态</span><span>最迟节点</span><span>下一动作</span>
        </div>
        <div className="evidence-table-body">
          {props.gates.map((gate) => (
            <button
              key={gate.id}
              type="button"
              className={props.selectedGate.id === gate.id ? "selected" : ""}
              onClick={() => props.onGateSelect(gate.id)}
              aria-current={props.selectedGate.id === gate.id ? "true" : undefined}
            >
              <span className="gate-name"><em>{gate.code}</em><span><strong>{gate.title}</strong><small>{gate.reason}</small></span></span>
              <StatusChip status={gate.status} />
              <span className="deadline-cell">{gate.deadline}</span>
              <span className="next-cell">查看要求<ArrowIcon /></span>
            </button>
          ))}
        </div>
      </section>
      <p className="workspace-footnote"><AlertIcon />上传、OCR 或模型抽取只能产生待审核声明；必须核对签发方、观察期、标的范围和原件后才能标记为已核实。</p>
    </>
  );
}

function ValuationPanel(props: SharedProps) {
  return (
    <>
      <WorkspaceHeader
        eyebrow="COMPARABLE SALES · PROPERTY LEVEL"
        title="可比估值"
        description="挂牌价、城市指数和模型生成值都不能代替真实可比成交。"
        action={<StatusChip status="missing" label="缺 3+ 笔成交" />}
      />
      <section className="locked-workspace">
        <span className="large-lock"><ChartIcon /></span>
        <span className="eyebrow">VALUATION LOCKED</span>
        <h2>尚不能形成合理价格区间</h2>
        <p>需要至少 3 笔同小区近期真实成交，并记录来源、日期、面积、楼层、朝向、装修与纳入/排除理由。</p>
        <button className="button-primary" type="button" onClick={() => {
          props.onGateSelect("comparables");
          props.onWorkspaceChange("evidence");
        }}>查看可比成交要求<ArrowIcon /></button>
      </section>
      <section className="panel-card empty-table">
        <div className="panel-title"><div><span className="title-icon"><DatabaseIcon /></span><span><strong>可比成交样本</strong><small>0 笔合格样本</small></span></div></div>
        <div className="empty-table-head"><span>成交日期</span><span>面积</span><span>成交总价</span><span>楼层 / 朝向</span><span>来源与质量</span></div>
        <div className="empty-table-state"><DatabaseIcon /><strong>等待可归属的成交证据</strong><small>不会用演示数据绘制价格带或伪造市场分布。</small></div>
      </section>
      <section className="market-context-note"><LinkIcon /><span><strong>国家统计局城市指数已核验</strong><small>仅描述广州城市级变化，不能证明本小区、本户型或本套房的成交价值。</small></span></section>
    </>
  );
}

function FinancePanel(props: SharedProps) {
  return (
    <>
      <WorkspaceHeader
        eyebrow="DETERMINISTIC MODEL · INPUTS LOCKED"
        title="成本与融资"
        description="规则和公式已版本化；没有标的级输入时不执行现金流模型。"
        action={<StatusChip status="missing" label="关键输入缺失" />}
      />
      <section className="verified-input-grid">
        <article><span>演示要约</span><strong>520 万元</strong><StatusChip status="user_input" /><small>无原始证据，仅界面演示</small></article>
        <article><span>全国优惠契税规则</span><strong>规则已核</strong><StatusChip status="verified" /><small>仍需当地口径与家庭套数</small></article>
        <article><span>银行执行利率</span><strong>缺失</strong><StatusChip status="missing" /><small>LPR 3.5% 不可代替报价</small></article>
        <article><span>可比租金与空置</span><strong>缺失</strong><StatusChip status="missing" /><small>尚无租约或可比租赁</small></article>
      </section>
      <section className="panel-card scenario-panel">
        <div className="panel-title"><div><span className="title-icon"><CalculatorIcon /></span><span><strong>全周期现金流情景</strong><small>依赖项补齐后由 Python 确定性核心计算</small></span></div><StatusChip status="missing" label="输出锁定" /></div>
        <div className="scenario-table">
          <div className="scenario-head"><span>情景</span><span>售价变化假设</span><span>年空置</span><span>退出周期</span><span>杠杆 IRR</span></div>
          {scenarioRows.map((row) => (
            <div key={row.name}><strong>{row.name}</strong><span>{row.price}</span><span>{row.vacancy}</span><span>{row.exit}</span><span className="locked-value"><LockIcon />锁定</span></div>
          ))}
        </div>
      </section>
      <section className="formula-boundary">
        <SparkIcon />
        <div><strong>模型与智能助手的职责分离</strong><p>税费、贷款计划、现金流、NPV 与 IRR 只能由版本化代码复算；Reasonix 或其他模型只能解释已验证结果，不能补造输入。</p></div>
      </section>
    </>
  );
}

function RisksPanel(props: SharedProps) {
  const stages = [
    { title: "支付定金前", gates: props.gates.filter((gate) => ["title", "encumbrance"].includes(gate.id)) },
    { title: "签署合同前", gates: props.gates.filter((gate) => ["property_nature", "occupancy", "tax", "loan"].includes(gate.id)) },
    { title: "形成价格意见前", gates: props.gates.filter((gate) => gate.id === "comparables") },
  ];
  return (
    <>
      <WorkspaceHeader
        eyebrow="TRANSACTION CONTROL · BEFORE MONEY MOVES"
        title="风险与交割"
        description="按资金与合同节点安排核验，不把七项缺口重复包装成风险分数。"
        action={<StatusChip status="missing" label="7 个阻断项" />}
      />
      <section className="transaction-timeline">
        {stages.map((stage, stageIndex) => (
          <article key={stage.title}>
            <div className="timeline-marker"><span>0{stageIndex + 1}</span></div>
            <div className="timeline-content">
              <div className="timeline-title"><strong>{stage.title}</strong><small>{stage.gates.length} 项必须完成</small></div>
              {stage.gates.map((gate) => (
                <button key={gate.id} type="button" onClick={() => {
                  props.onGateSelect(gate.id);
                  props.onWorkspaceChange("evidence");
                }}>
                  <StatusDot status={gate.status} />
                  <span><strong>{gate.title}</strong><small>{gate.reason}</small></span>
                  <ArrowIcon />
                </button>
              ))}
            </div>
          </article>
        ))}
      </section>
      <section className="hard-stop-card"><AlertIcon /><div><strong>硬停止规则</strong><p>出现查封、处分权不足、材料冲突或无法解释的证据复用时，系统不是“降低评分”，而是停止分析并保留审计原因。</p></div></section>
    </>
  );
}

function MemoPanel(props: SharedProps) {
  return (
    <>
      <WorkspaceHeader
        eyebrow="AUDITABLE OUTPUT · REVISION 0"
        title="决策备忘录"
        description="当前只允许导出证据缺口报告，不输出方向性投资结论。"
        action={<button className="button-secondary" type="button" onClick={props.onPrint}><FileIcon />打印缺口报告</button>}
      />
      <DecisionGate onUpload={props.onUpload} onAskAssistant={props.onAskAssistant} />
      <section className="memo-document panel-card">
        <div className="memo-document-header">
          <div><span>DwellProof / GZ-DEMO-001</span><strong>受控原型证据缺口报告</strong></div>
          <StatusChip status="missing" label="不可操作" />
        </div>
        <div className="memo-section-grid">
          <section><span>01</span><div><strong>当前能确认什么</strong><p>三个官方快照证明全国契税优惠规则、LPR 市场基准和选定城市指数行。它们均不能证明本套房权利状态、税负、融资或价值。</p></div></section>
          <section><span>02</span><div><strong>当前不能计算什么</strong><p>合理价格区间、完整取得成本、贷款计划、租金现金流、NPV、IRR 与投资方向全部锁定。</p></div></section>
          <section><span>03</span><div><strong>解除锁定需要什么</strong><p>七项证据门槛必须由同一案例、同一标的和同一借款人范围内的最新、清晰、无冲突材料通过。</p></div></section>
        </div>
      </section>
      <section className="panel-card source-register">
        <div className="panel-title"><div><span className="title-icon"><LinkIcon /></span><span><strong>官方规则与背景来源</strong><small>快照已核，但不等于标的级证据</small></span></div><em>{props.sources.length} 项</em></div>
        <div className="source-register-list">
          {props.sources.map((source) => (
            <a key={source.id} href={source.url} target="_blank" rel="noopener noreferrer">
              <CheckIcon />
              <span><strong>{source.title}</strong><small>{source.authority} · {source.observed}</small><p>{source.boundary}</p></span>
              <LinkIcon />
            </a>
          ))}
        </div>
      </section>
    </>
  );
}

export function WorkspacePanel({ workspace, ...props }: SharedProps & { workspace: WorkspaceId }) {
  if (workspace === "evidence") return <EvidencePanel {...props} />;
  if (workspace === "valuation") return <ValuationPanel {...props} />;
  if (workspace === "finance") return <FinancePanel {...props} />;
  if (workspace === "risks") return <RisksPanel {...props} />;
  if (workspace === "memo") return <MemoPanel {...props} />;
  return <OverviewPanel {...props} />;
}
