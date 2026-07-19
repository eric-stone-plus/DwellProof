"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertIcon,
  ArrowIcon,
  CheckIcon,
  ShieldIcon,
  SparkIcon,
  XIcon,
} from "@/components/icons";
import { buildCaseSnapshot } from "@/lib/demo-case";
import {
  asReasonixError,
  explainWithReasonix,
  getReasonixStatus,
  isDesktopRuntime,
  type ReasonixStatus,
} from "@/lib/reasonix-bridge";

const CONSENT_KEY = "dwellproof-assistant-consent";
const CITATION_PATTERN = /G0[1-7]|deed-tax|nbs-index|lpr/g;

const SUGGESTED_QUESTIONS = [
  "七项缺口按交易风险怎么排序？先做哪三件？",
  "为什么不能把 LPR 当作本借款人的执行利率？",
  "城市指数已核验，为什么还不能估值？",
];

type Turn = {
  question: string;
  text: string;
  state: "streaming" | "done" | "refused" | "error";
  errorCode?: string;
  errorMessage?: string;
};

function citationsIn(text: string): string[] {
  return Array.from(new Set(text.match(CITATION_PATTERN) ?? []));
}

export function AssistantPanel({
  open,
  preset,
  onClose,
}: {
  open: boolean;
  preset: { question: string; nonce: number } | null;
  onClose: () => void;
}) {
  const [status, setStatus] = useState<ReasonixStatus | null>(null);
  const [consent, setConsent] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!open) return;
    setConsent(window.localStorage.getItem(CONSENT_KEY) === "yes");
    let cancelled = false;
    getReasonixStatus()
      .then((value) => {
        if (!cancelled) setStatus(value);
      })
      .catch((error) => {
        if (!cancelled) {
          setStatus({
            status: "unavailable",
            reason: String(error),
            version: "-",
            model: "-",
            platform: "-",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [turns]);

  const ask = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed || busy) return;
      setBusy(true);
      setDraft("");
      setTurns((current) => [
        ...current,
        { question: trimmed, text: "", state: "streaming" },
      ]);
      try {
        const result = await explainWithReasonix(trimmed, buildCaseSnapshot(), (event) => {
          if (event.type === "chunk") {
            setTurns((current) => {
              const next = [...current];
              const last = next[next.length - 1];
              if (last && last.state === "streaming") {
                next[next.length - 1] = { ...last, text: last.text + event.text };
              }
              return next;
            });
          }
        });
        setTurns((current) => {
          const next = [...current];
          const last = next[next.length - 1];
          if (last) {
            next[next.length - 1] = {
              ...last,
              text: result.text,
              state: result.citations_ok ? "done" : "refused",
            };
          }
          return next;
        });
      } catch (error) {
        const parsed = asReasonixError(error);
        setTurns((current) => {
          const next = [...current];
          const last = next[next.length - 1];
          if (last) {
            next[next.length - 1] = {
              ...last,
              state: "error",
              errorCode: parsed.code,
              errorMessage: parsed.message,
            };
          }
          return next;
        });
      } finally {
        setBusy(false);
      }
    },
    [busy],
  );

  const lastPresetNonceRef = useRef<number>(-1);
  useEffect(() => {
    if (
      open &&
      preset &&
      preset.nonce !== lastPresetNonceRef.current &&
      status?.status === "available" &&
      consent &&
      !busy
    ) {
      lastPresetNonceRef.current = preset.nonce;
      ask(preset.question);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, preset, status, consent]);

  const ready = status?.status === "available";
  const statusView = useMemo(() => {
    if (!status) return <p className="assistant-note">正在检查 Reasonix 运行时…</p>;
    if (status.status === "setup_required") {
      return (
        <div className="assistant-callout">
          <AlertIcon />
          <div>
            <strong>需要 DeepSeek API Key</strong>
            <p>
              在启动 DwellProof 前设置环境变量 <code>DEEPSEEK_API_KEY</code>。密钥只从进程环境读取，
              不写入磁盘；模型调用走 DeepSeek 官方 API（{status.model} · effort max）。
            </p>
          </div>
        </div>
      );
    }
    if (status.status === "unavailable") {
      return (
        <div className="assistant-callout">
          <AlertIcon />
          <div>
            <strong>Reasonix 运行时不可用</strong>
            <p>
              {status.reason ?? "pinned 二进制缺失或校验失败"}。开发环境可运行
              <code>python3 scripts/fetch_reasonix_runtime.py</code> 获取并校验 v{status.version}。
            </p>
          </div>
        </div>
      );
    }
    if (status.status === "disabled") {
      return (
        <div className="assistant-callout">
          <AlertIcon />
          <div>
            <strong>助手已禁用</strong>
            <p>当前通过 DWELLPROOF_REASONIX_ENABLED=0 显式关闭了 Reasonix 影子层。</p>
          </div>
        </div>
      );
    }
    return null;
  }, [status]);

  if (!open) return null;

  return (
    <div className="assistant-backdrop" onClick={onClose} aria-hidden="false">
      <aside
        className="assistant-panel"
        role="dialog"
        aria-modal="true"
        aria-label="Reasonix 缺口解释助手"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="assistant-header">
          <div>
            <span className="eyebrow">REASONIX · SHADOW MODE</span>
            <h2>缺口解释助手</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="关闭助手">
            <XIcon />
          </button>
        </header>

        {!consent ? (
          <div className="assistant-consent">
            <span className="title-icon"><ShieldIcon /></span>
            <h3>使用前确认</h3>
            <p>
              助手由 DeepSeek 托管模型（deepseek-v4-pro）驱动，你的提问和<strong>演示案例快照</strong>
              会发送至 api.deepseek.com。快照只含本仓库的公开演示常量，不含你的文件、真实房源或身份信息。
            </p>
            <p>
              助手输出是<strong>非权威解释</strong>：不能核实证据、不能改变任何检查状态、不会给出买卖建议。
            </p>
            <button
              className="button-primary full-width"
              type="button"
              onClick={() => {
                window.localStorage.setItem(CONSENT_KEY, "yes");
                setConsent(true);
              }}
            >
              明白并继续
            </button>
          </div>
        ) : (
          <>
            {statusView}
            {ready && (
              <>
                <div ref={scrollRef} className="assistant-messages">
                  {turns.length === 0 && (
                    <div className="assistant-empty">
                      <SparkIcon />
                      <p>基于只读案例快照解释缺口。所有回答都必须引用检查项或来源编号，否则不会展示。</p>
                      {SUGGESTED_QUESTIONS.map((question) => (
                        <button key={question} type="button" onClick={() => ask(question)}>
                          {question}
                          <ArrowIcon />
                        </button>
                      ))}
                    </div>
                  )}
                  {turns.map((turn, index) => (
                    <div key={index} className="assistant-turn">
                      <p className="assistant-question">{turn.question}</p>
                      {turn.state === "refused" ? (
                        <div className="assistant-refusal">
                          <AlertIcon />
                          <span>
                            这条回复没有引用任何检查项或来源编号，按证据契约<strong>未予展示</strong>。
                            请换一种问法，或先补齐对应证据。
                          </span>
                        </div>
                      ) : turn.state === "error" ? (
                        <div className="assistant-refusal">
                          <AlertIcon />
                          <span>
                            调用失败（{turn.errorCode}）：{turn.errorMessage}
                          </span>
                        </div>
                      ) : (
                        <div className="assistant-answer">
                          <p>
                            {turn.text}
                            {turn.state === "streaming" && <span className="assistant-caret" />}
                          </p>
                          {turn.state === "done" && (
                            <div className="assistant-citations">
                              {citationsIn(turn.text).map((id) => (
                                <span key={id} className="citation-chip">
                                  <CheckIcon />
                                  {id}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                <form
                  className="assistant-input-row"
                  onSubmit={(event) => {
                    event.preventDefault();
                    ask(draft);
                  }}
                >
                  <textarea
                    ref={inputRef}
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        ask(draft);
                      }
                    }}
                    placeholder="就演示案例提问…"
                    rows={2}
                    maxLength={4000}
                    aria-label="向助手提问"
                  />
                  <button className="button-primary" type="submit" disabled={busy || !draft.trim()}>
                    {busy ? "…" : <ArrowIcon />}
                  </button>
                </form>
              </>
            )}
          </>
        )}
        <footer className="assistant-footer">
          <ShieldIcon />
          <span>非权威解释 · 不改变任何证据状态 · token 用量不可得（usageUnavailable）</span>
        </footer>
      </aside>
    </div>
  );
}
