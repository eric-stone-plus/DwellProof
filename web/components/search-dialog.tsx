"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { EvidenceGate, WorkspaceId } from "@/lib/demo-case";
import { workspaces } from "@/lib/demo-case";
import { ArrowIcon, SearchIcon, ShieldIcon, XIcon } from "@/components/icons";
import { useOverlayFocus } from "@/lib/use-overlay-focus";

type SearchResult = {
  id: string;
  title: string;
  description: string;
  group: "工作区" | "证据门槛";
  workspace: WorkspaceId;
  gateId?: string;
};

export function SearchDialog({
  open,
  gates,
  onClose,
  onSelect,
}: {
  open: boolean;
  gates: EvidenceGate[];
  onClose: () => void;
  onSelect: (workspace: WorkspaceId, gateId?: string) => void;
}) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const skipRestoreFocusRef = useRef(false);
  const composingRef = useRef(false);

  const results = useMemo<SearchResult[]>(() => {
    const all: SearchResult[] = [
      ...workspaces.map((workspace) => ({
        id: `workspace-${workspace.id}`,
        title: workspace.label,
        description: workspace.description,
        group: "工作区" as const,
        workspace: workspace.id,
      })),
      ...gates.map((gate) => ({
        id: `gate-${gate.id}`,
        title: gate.title,
        description: `${gate.code} · ${gate.deadline}`,
        group: "证据门槛" as const,
        workspace: "evidence" as const,
        gateId: gate.id,
      })),
    ];
    const normalized = query.trim().toLocaleLowerCase("zh-CN");
    if (!normalized) return all;
    return all.filter((item) => `${item.title} ${item.description}`.toLocaleLowerCase("zh-CN").includes(normalized));
  }, [gates, query]);

  useEffect(() => {
    if (!open) return;
    skipRestoreFocusRef.current = false;
    setQuery("");
  }, [open]);

  useOverlayFocus({ open, containerRef: dialogRef, initialFocusRef: inputRef, skipRestoreFocusRef, onClose });

  function selectResult(result: SearchResult) {
    skipRestoreFocusRef.current = true;
    onSelect(result.workspace, result.gateId);
  }

  if (!open) return null;

  return (
    <div className="dialog-backdrop search-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <section ref={dialogRef} className="search-dialog" role="dialog" aria-modal="true" aria-labelledby="search-dialog-title">
        <div className="search-input-row">
          <SearchIcon />
          <label className="visually-hidden" htmlFor="case-search" id="search-dialog-title">搜索当前案例导航</label>
          <form onSubmit={(event) => {
            event.preventDefault();
            if (composingRef.current) return;
            if (results[0]) selectResult(results[0]);
          }}>
            <input
              ref={inputRef}
              id="case-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onCompositionStart={() => { composingRef.current = true; }}
              onCompositionEnd={() => { composingRef.current = false; }}
              placeholder="搜索工作区、产权、税费、贷款或可比成交…"
            />
          </form>
          <button type="button" onClick={onClose} aria-label="关闭搜索"><XIcon /></button>
        </div>
        <div className="search-results">
          {results.length ? results.map((result) => (
            <button key={result.id} type="button" onClick={() => selectResult(result)}>
              <span className="search-result-icon">{result.group === "证据门槛" ? <ShieldIcon /> : <SearchIcon />}</span>
              <span><strong>{result.title}</strong><small>{result.group} · {result.description}</small></span>
              <ArrowIcon />
            </button>
          )) : (
            <div className="search-empty"><SearchIcon /><strong>没有匹配的案例入口</strong><small>试试“产权”“税费”“贷款”或“备忘录”。</small></div>
          )}
        </div>
        <div className="search-hint"><span><kbd>Enter</kbd> 打开首项</span><span><kbd>Esc</kbd> 关闭</span></div>
      </section>
    </div>
  );
}
