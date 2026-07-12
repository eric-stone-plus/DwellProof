"use client";

import type { EvidenceGate, WorkspaceId } from "@/lib/demo-case";
import { workspaces } from "@/lib/demo-case";
import {
  BookIcon,
  CalculatorIcon,
  ChartIcon,
  FileIcon,
  GridIcon,
  HomeIcon,
  PlusIcon,
  ShieldIcon,
  SlidersIcon,
} from "@/components/icons";
import { StatusDot } from "@/components/status";

const workspaceIcons: Record<WorkspaceId, React.ComponentType<React.SVGProps<SVGSVGElement>>> = {
  overview: GridIcon,
  evidence: ShieldIcon,
  valuation: ChartIcon,
  finance: CalculatorIcon,
  risks: FileIcon,
  memo: BookIcon,
};

export function CaseRail({
  activeWorkspace,
  onWorkspaceChange,
  selectedGate,
  gates,
  localCaseName,
  localCaseRegion,
  onNewCase,
  onSelectDemo,
  onSelectLocalCase,
  onSettings,
}: {
  activeWorkspace: WorkspaceId;
  onWorkspaceChange: (workspace: WorkspaceId) => void;
  selectedGate: string;
  gates: EvidenceGate[];
  localCaseName?: string;
  localCaseRegion?: string;
  onNewCase: () => void;
  onSelectDemo: () => void;
  onSelectLocalCase: () => void;
  onSettings: () => void;
}) {
  return (
    <aside className="case-rail">
      <div className="rail-brand">
        <span className="brand-mark"><HomeIcon /></span>
        <span>
          <strong>DwellProof</strong>
          <small>住宅交易证据工作台</small>
        </span>
      </div>

      <div className="rail-scroll">
        <section className="rail-section">
          <div className="rail-section-heading">
            <span>当前案例</span>
            <button type="button" onClick={onNewCase} aria-label="新建匿名案例"><PlusIcon /></button>
          </div>
          <button type="button" className="case-card active" onClick={onSelectDemo}>
            <span className="case-avatar">GZ</span>
            <span className="case-card-copy">
              <strong>广州 · 天河演示</strong>
              <small>GZ-DEMO-001 · 修订 0</small>
            </span>
            <StatusDot status="missing" />
            <span className="visually-hidden">当前案例，待补证</span>
          </button>
          {localCaseName && (
            <button type="button" className="case-card local-draft" onClick={onSelectLocalCase}>
              <span className="case-avatar">LC</span>
              <span className="case-card-copy">
                <strong>{localCaseName}</strong>
                <small>{localCaseRegion || "未填写区域"} · 空白草稿</small>
              </span>
              <StatusDot status="user_input" />
              <span className="visually-hidden">本地草稿，待核验</span>
            </button>
          )}
        </section>

        <nav className="rail-section" aria-label="案例工作区">
          <div className="rail-section-heading static"><span>分析流程</span><em>0 / 6</em></div>
          <div className="workspace-nav">
            {workspaces.map((workspace) => {
              const Icon = workspaceIcons[workspace.id];
              const active = activeWorkspace === workspace.id;
              return (
                <button
                  key={workspace.id}
                  type="button"
                  className={active ? "active" : ""}
                  aria-current={active ? "page" : undefined}
                  onClick={() => onWorkspaceChange(workspace.id)}
                >
                  <span className="workspace-icon"><Icon /></span>
                  <span>
                    <strong>{workspace.label}</strong>
                    <small>{workspace.description}</small>
                  </span>
                </button>
              );
            })}
          </div>
        </nav>

        <section className="rail-section gate-progress">
          <div className="rail-section-heading static"><span>准入门槛</span><em>0 / 7</em></div>
          <div className="gate-mini-list">
            {gates.map((gate) => (
              <div key={gate.id} className={gate.id === selectedGate ? "selected" : ""}>
                <StatusDot status={gate.status} />
                <span>{gate.shortTitle}</span>
                <small>{gate.code}</small>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="rail-footer">
        <button type="button" onClick={onSettings}><SlidersIcon /><span>规则与设置</span><small>本地原型</small></button>
        <p><ShieldIcon />真实地址、证件及贷款文件不得进入公开仓库。</p>
      </div>
    </aside>
  );
}
