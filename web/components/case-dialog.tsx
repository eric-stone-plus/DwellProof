"use client";

import { useEffect, useRef, useState } from "react";
import { XIcon } from "@/components/icons";
import { useOverlayFocus } from "@/lib/use-overlay-focus";

export type LocalCaseDraft = {
  name: string;
  region: string;
};

export function CaseDialog({
  open,
  onClose,
  onCreate,
}: {
  open: boolean;
  onClose: () => void;
  onCreate: (draft: LocalCaseDraft) => void;
}) {
  const [name, setName] = useState("");
  const [region, setRegion] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLElement>(null);

  useOverlayFocus({ open, containerRef: dialogRef, initialFocusRef: inputRef, onClose });

  useEffect(() => {
    if (!open) return;
    setName("");
    setRegion("");
  }, [open]);

  if (!open) return null;

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <section ref={dialogRef} className="dialog-card" role="dialog" aria-modal="true" aria-labelledby="case-dialog-title">
        <div className="dialog-header">
          <div>
            <span className="eyebrow">LOCAL SESSION</span>
            <h2 id="case-dialog-title">新建匿名案例</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="关闭新建案例窗口">
            <XIcon />
          </button>
        </div>
        <p className="dialog-note">这里只建立工作区，不采集姓名、证件号或精确门牌。案例不会在当前原型中持久化。</p>
        <form onSubmit={(event) => {
          event.preventDefault();
          const safeName = name.trim() || "未命名案例";
          onCreate({ name: safeName.slice(0, 40), region: region.trim().slice(0, 40) });
          setName("");
          setRegion("");
        }}>
          <label className="field-label" htmlFor="case-name">案例标签</label>
          <input
            ref={inputRef}
            id="case-name"
            className="text-input"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="例如：自住备选 A"
            maxLength={40}
          />
          <label className="field-label" htmlFor="case-region">城市 / 区域（可选）</label>
          <input
            id="case-region"
            className="text-input"
            value={region}
            onChange={(event) => setRegion(event.target.value)}
            placeholder="例如：广州 / 天河"
            maxLength={40}
          />
          <div className="dialog-actions">
            <button className="button-secondary" type="button" onClick={onClose}>取消</button>
            <button className="button-primary" type="submit">创建本地案例</button>
          </div>
        </form>
      </section>
    </div>
  );
}
