"use client";

import type { EvidenceGate, OfficialSource } from "@/lib/demo-case";
import { AlertIcon, ArrowIcon, EyeIcon, FileIcon, LinkIcon, LockIcon, UploadIcon } from "@/components/icons";
import { StatusChip } from "@/components/status";

export type PendingFile = {
  id: string;
  name: string;
  size: number;
  gateId: string;
};

function formatBytes(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

export function ContextInspector({
  gate,
  sources,
  pendingFiles,
  onUpload,
  onRules,
}: {
  gate: EvidenceGate;
  sources: OfficialSource[];
  pendingFiles: PendingFile[];
  onUpload: () => void;
  onRules: () => void;
}) {
  const relatedSource = gate.id === "tax"
    ? sources[0]
    : gate.id === "loan"
      ? sources[2]
      : gate.id === "comparables"
        ? sources[1]
        : undefined;
  const files = pendingFiles.filter((file) => file.gateId === gate.id);

  return (
    <aside className="context-inspector" aria-label="证据上下文检查器">
      <div className="inspector-header">
        <div>
          <span className="eyebrow">EVIDENCE INSPECTOR</span>
          <h2>{gate.title}</h2>
        </div>
        <StatusChip status={gate.status} />
      </div>

      <section className="inspector-block requirement-card">
        <div className="block-title"><LockIcon /><span>开放分析所需</span></div>
        <p>{gate.requirement}</p>
        <dl className="compact-facts">
          <div><dt>最迟节点</dt><dd>{gate.deadline}</dd></div>
          <div><dt>建议负责</dt><dd>{gate.owner}</dd></div>
        </dl>
      </section>

      <section className="inspector-block">
        <div className="block-title"><FileIcon /><span>可接受材料</span></div>
        <ul className="accepted-list">
          {gate.accepted.map((item) => <li key={item}>{item}</li>)}
        </ul>
        <button className="button-primary full-width" type="button" onClick={onUpload}>
          <UploadIcon />添加到待核验队列
        </button>
        <p className="privacy-note">文件仅在当前浏览器会话中列名，不上传、不读取内容，也不会自动改变证据状态。</p>
      </section>

      {files.length > 0 && (
        <section className="inspector-block">
          <div className="block-title"><EyeIcon /><span>待核验材料</span><em>{files.length}</em></div>
          <div className="pending-file-list">
            {files.map((file) => (
              <div key={file.id}>
                <FileIcon />
                <span><strong>{file.name}</strong><small>{formatBytes(file.size)} · 未读取</small></span>
                <StatusChip status="user_input" label="待审" />
              </div>
            ))}
          </div>
        </section>
      )}

      {relatedSource ? (
        <section className="inspector-block source-context">
          <div className="block-title"><LinkIcon /><span>相关官方背景</span></div>
          <a href={relatedSource.url} target="_blank" rel="noopener noreferrer">
            <span><strong>{relatedSource.title}</strong><small>{relatedSource.authority}</small></span>
            <ArrowIcon />
          </a>
          <p><AlertIcon />{relatedSource.boundary}</p>
        </section>
      ) : (
        <section className="inspector-block source-empty">
          <div className="block-title"><AlertIcon /><span>没有可替代的官方快照</span></div>
          <p>必须取得与本套房、当事人和交易时点直接相关的材料。</p>
        </section>
      )}

      <button className="button-secondary full-width" type="button" onClick={onRules}>查看全部规则来源</button>
    </aside>
  );
}
