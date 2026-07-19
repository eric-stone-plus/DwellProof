"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AssistantPanel } from "@/components/assistant-panel";
import { CaseDialog, type LocalCaseDraft } from "@/components/case-dialog";
import { CaseRail } from "@/components/case-rail";
import { ContextInspector, type PendingFile } from "@/components/context-inspector";
import {
  AlertIcon,
  BookIcon,
  BrandIcon,
  CalculatorIcon,
  HomeIcon,
  MenuIcon,
  MoonIcon,
  SearchIcon,
  ShieldIcon,
  SunIcon,
  XIcon,
} from "@/components/icons";
import { StatusChip, StatusDot } from "@/components/status";
import { SearchDialog } from "@/components/search-dialog";
import { WorkspacePanel } from "@/components/workspace-panels";
import { evidenceGates, officialSources, workspaces, type WorkspaceId } from "@/lib/demo-case";
import { isDesktopRuntime } from "@/lib/reasonix-bridge";
import { useOverlayFocus } from "@/lib/use-overlay-focus";

type Theme = "light" | "dark";

export default function Home() {
  const [theme, setTheme] = useState<Theme>("dark");
  const [workspace, setWorkspace] = useState<WorkspaceId>("overview");
  const [selectedGateId, setSelectedGateId] = useState("title");
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);
  const [caseDialogOpen, setCaseDialogOpen] = useState(false);
  const [localCase, setLocalCase] = useState<LocalCaseDraft | null>(null);
  const [railOpen, setRailOpen] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [railOverlay, setRailOverlay] = useState(false);
  const [inspectorOverlay, setInspectorOverlay] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [assistantPreset, setAssistantPreset] = useState<{ question: string; nonce: number } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const workspaceContentRef = useRef<HTMLDivElement>(null);
  const railContainerRef = useRef<HTMLDivElement>(null);
  const railCloseRef = useRef<HTMLButtonElement>(null);
  const inspectorContainerRef = useRef<HTMLDivElement>(null);
  const inspectorCloseRef = useRef<HTMLButtonElement>(null);
  const toastTimerRef = useRef<number | undefined>(undefined);

  const selectedGate = useMemo(
    () => evidenceGates.find((gate) => gate.id === selectedGateId) ?? evidenceGates[0],
    [selectedGateId],
  );

  useEffect(() => {
    const saved = window.localStorage.getItem("dwellproof-theme") as Theme | null;
    const initial = saved === "light" || saved === "dark" ? saved : "dark";
    setTheme(initial);
    document.documentElement.dataset.theme = initial;
    setIsDesktop(isDesktopRuntime());
  }, []);

  useEffect(() => () => {
    if (toastTimerRef.current) window.clearTimeout(toastTimerRef.current);
  }, []);

  useEffect(() => {
    const handleShortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLocaleLowerCase() === "k" && !caseDialogOpen && !railOpen && !(inspectorOpen && inspectorOverlay)) {
        event.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, [caseDialogOpen, inspectorOpen, inspectorOverlay, railOpen]);

  useEffect(() => {
    const railQuery = window.matchMedia("(max-width: 820px)");
    const inspectorQuery = window.matchMedia("(max-width: 1200px)");
    const syncOverlayModes = () => {
      setRailOverlay(railQuery.matches);
      setInspectorOverlay(inspectorQuery.matches);
      if (!railQuery.matches) setRailOpen(false);
      if (!inspectorQuery.matches) setInspectorOpen(false);
    };
    syncOverlayModes();
    railQuery.addEventListener("change", syncOverlayModes);
    inspectorQuery.addEventListener("change", syncOverlayModes);
    return () => {
      railQuery.removeEventListener("change", syncOverlayModes);
      inspectorQuery.removeEventListener("change", syncOverlayModes);
    };
  }, []);

  const showToast = useCallback((message: string) => {
    setToast(message);
    if (toastTimerRef.current) window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 4200);
  }, []);

  const changeWorkspace = useCallback((next: WorkspaceId) => {
    setWorkspace(next);
    setRailOpen(false);
    const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
    workspaceContentRef.current?.scrollTo({ top: 0, behavior });
    window.scrollTo({ top: 0, behavior });
    window.requestAnimationFrame(() => workspaceContentRef.current?.focus({ preventScroll: true }));
  }, []);

  const selectGate = useCallback((gateId: string) => {
    setSelectedGateId(gateId);
    setInspectorOpen(true);
  }, []);

  const toggleTheme = useCallback(() => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.dataset.theme = next;
    window.localStorage.setItem("dwellproof-theme", next);
  }, [theme]);

  const requestUpload = useCallback(() => fileInputRef.current?.click(), []);

  const askAssistant = useCallback((question: string) => {
    setAssistantPreset({ question, nonce: Date.now() });
    setAssistantOpen(true);
  }, []);

  const isMobileNavActive = useCallback((id: WorkspaceId) => {
    if (id === "evidence") return workspace === "evidence" || workspace === "risks";
    if (id === "finance") return workspace === "valuation" || workspace === "finance";
    return workspace === id;
  }, [workspace]);

  const railIsModal = railOpen && railOverlay;
  const inspectorIsModal = inspectorOpen && inspectorOverlay;
  const dialogOpen = caseDialogOpen || searchOpen;

  useEffect(() => {
    if (!dialogOpen) return;
    setRailOpen(false);
    setInspectorOpen(false);
  }, [dialogOpen]);

  useOverlayFocus({
    open: railIsModal,
    containerRef: railContainerRef,
    initialFocusRef: railCloseRef,
    onClose: () => setRailOpen(false),
  });
  useOverlayFocus({
    open: inspectorIsModal,
    containerRef: inspectorContainerRef,
    initialFocusRef: inspectorCloseRef,
    onClose: () => setInspectorOpen(false),
  });

  function handleFileSelection(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) return;

    const acceptedFiles = files.filter((file) => file.size <= 25 * 1024 * 1024).map((file, index) => ({
      id: `${Date.now()}-${index}-${file.name}`,
      name: file.name,
      size: file.size,
      gateId: selectedGate.id,
    }));
    setPendingFiles((current) => [...current, ...acceptedFiles]);
    event.target.value = "";

    if (acceptedFiles.length !== files.length) {
      showToast(`已暂存 ${acceptedFiles.length} 个文件名；超过 25 MB 的文件被拒绝。材料仍为待核验。`);
    } else {
      showToast(`已将 ${acceptedFiles.length} 个文件加入“${selectedGate.shortTitle}”待核验队列；未读取或上传内容。`);
    }
    setInspectorOpen(true);
  }

  function handleCreateCase(draft: LocalCaseDraft) {
    setLocalCase(draft);
    setCaseDialogOpen(false);
    showToast("匿名案例草稿已在当前会话创建；刷新页面后不会保留。");
  }

  function handlePrint() {
    showToast("正在打开系统打印面板；当前输出明确标记为证据缺口报告。 ");
    window.setTimeout(() => window.print(), 120);
  }

  return (
    <main className="app-shell">
      <a className="skip-link" href="#workspace-content">跳到主要内容</a>
      <input
        ref={fileInputRef}
        className="visually-hidden"
        type="file"
        multiple
        aria-label="选择待核验材料"
        accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.csv"
        onChange={handleFileSelection}
        tabIndex={-1}
      />

      <div className={`mobile-scrim ${railIsModal || inspectorIsModal ? "visible" : ""}`} onClick={() => {
        setRailOpen(false);
        setInspectorOpen(false);
      }} aria-hidden="true" />

      <div
        ref={railContainerRef}
        className={`rail-container ${railOpen ? "mobile-open" : ""}`}
        role={railIsModal ? "dialog" : undefined}
        aria-modal={railIsModal ? "true" : undefined}
        aria-label={railIsModal ? "案例导航" : undefined}
        inert={dialogOpen || inspectorIsModal ? true : undefined}
      >
        <button ref={railCloseRef} className="mobile-panel-close" type="button" onClick={() => setRailOpen(false)} aria-label="关闭案例导航"><XIcon /></button>
        <CaseRail
          activeWorkspace={workspace}
          onWorkspaceChange={changeWorkspace}
          selectedGate={selectedGateId}
          gates={evidenceGates}
          localCaseName={localCase?.name}
          localCaseRegion={localCase?.region}
          onNewCase={() => {
            setRailOpen(false);
            setCaseDialogOpen(true);
          }}
          onSelectDemo={() => showToast("当前已选择受控演示案例 GZ-DEMO-001。")}
          onSelectLocalCase={() => showToast("本地草稿尚未接持久化案例存储；当前仍显示受控演示案例。")}
          onSettings={() => {
            changeWorkspace("memo");
            showToast("当前原型只公开规则来源与安全边界；持久化设置尚未启用。");
          }}
        />
      </div>

      <section className="main-stage" inert={dialogOpen || railIsModal || inspectorIsModal ? true : undefined}>
        <header className="topbar">
          <div className="topbar-left">
            <button className="icon-button mobile-only" type="button" onClick={() => setRailOpen(true)} aria-label="打开案例导航"><MenuIcon /></button>
            <span className="mobile-brand"><BrandIcon /></span>
            <div className="case-context">
              <span className="desktop-only">受控原型 / </span>
              <strong>广州 · 天河演示</strong>
              <small>GZ-DEMO-001 · REV 0</small>
            </div>
          </div>
          <div className="topbar-actions">
            <button className="global-search" type="button" onClick={() => setSearchOpen(true)} aria-label="搜索当前案例导航">
              <SearchIcon />
              <span className="global-search-label">搜索当前案例</span>
              <kbd className="global-search-label">⌘ K</kbd>
            </button>
            <span className="rule-health desktop-only"><StatusDot status="verified" />规则快照 3 项</span>
            <button className="icon-button" type="button" onClick={toggleTheme} aria-label={theme === "dark" ? "切换到浅色模式" : "切换到深色模式"}>
              {theme === "dark" ? <SunIcon /> : <MoonIcon />}
            </button>
            <button className="inspector-trigger" type="button" onClick={() => setInspectorOpen(true)} aria-label="打开证据检查器，当前七项待补证">
              <ShieldIcon /><span className="desktop-only">证据检查器</span><em>7</em>
            </button>
          </div>
        </header>

        <div className="prototype-strip">
          <AlertIcon />
          <strong>演示数据</strong>
          <span>规则快照已核不等于房源已核。当前 0 / 7 标的级检查通过，方向性输出保持关闭。</span>
          <code>actionable: false</code>
        </div>

        <nav className="mobile-workspace-tabs" aria-label="案例工作区">
          {workspaces.map((item) => (
            <button
              key={item.id}
              type="button"
              className={workspace === item.id ? "active" : ""}
              aria-current={workspace === item.id ? "page" : undefined}
              onClick={() => changeWorkspace(item.id)}
            >
              {item.shortLabel}
            </button>
          ))}
        </nav>

        <div ref={workspaceContentRef} id="workspace-content" className="workspace-content" tabIndex={-1}>
          <WorkspacePanel
            workspace={workspace}
            gates={evidenceGates}
            selectedGate={selectedGate}
            onGateSelect={selectGate}
            onWorkspaceChange={changeWorkspace}
            onUpload={requestUpload}
            onPrint={handlePrint}
            onAskAssistant={isDesktop ? askAssistant : undefined}
            pendingCount={pendingFiles.length}
            sources={officialSources}
          />
        </div>

        <nav className="mobile-bottom-nav" aria-label="移动端主要导航">
          {workspaces.filter((item) => ["overview", "evidence", "finance", "memo"].includes(item.id)).map((item) => (
            <button
              key={item.id}
              type="button"
              className={isMobileNavActive(item.id) ? "active" : ""}
              aria-current={isMobileNavActive(item.id) ? "page" : undefined}
              onClick={() => changeWorkspace(item.id)}
            >
              {item.id === "overview" ? <HomeIcon /> : item.id === "evidence" ? <ShieldIcon /> : item.id === "finance" ? <CalculatorIcon /> : <BookIcon />}
              <span>{item.shortLabel}</span>
            </button>
          ))}
        </nav>
      </section>

      <div
        ref={inspectorContainerRef}
        className={`inspector-container ${inspectorOpen ? "mobile-open" : ""}`}
        role={inspectorIsModal ? "dialog" : undefined}
        aria-modal={inspectorIsModal ? "true" : undefined}
        aria-label={inspectorIsModal ? "证据检查器" : undefined}
        inert={dialogOpen || railIsModal ? true : undefined}
      >
        <button ref={inspectorCloseRef} className="mobile-panel-close" type="button" onClick={() => setInspectorOpen(false)} aria-label="关闭证据检查器"><XIcon /></button>
        <ContextInspector
          gate={selectedGate}
          sources={officialSources}
          pendingFiles={pendingFiles}
          onUpload={requestUpload}
          onRules={() => {
            changeWorkspace("memo");
            setInspectorOpen(false);
          }}
        />
      </div>

      <CaseDialog open={caseDialogOpen} onClose={() => setCaseDialogOpen(false)} onCreate={handleCreateCase} />
      {isDesktop && (
        <AssistantPanel
          open={assistantOpen}
          preset={assistantPreset}
          onClose={() => setAssistantOpen(false)}
        />
      )}
      <SearchDialog
        open={searchOpen}
        gates={evidenceGates}
        onClose={() => setSearchOpen(false)}
        onSelect={(nextWorkspace, gateId) => {
          if (gateId) selectGate(gateId);
          changeWorkspace(nextWorkspace);
          setSearchOpen(false);
        }}
      />
      {toast && <div className="toast" role="status" aria-live="polite"><StatusChip status="user_input" label="本地会话" /><span>{toast}</span></div>}
    </main>
  );
}
