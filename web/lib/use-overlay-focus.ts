"use client";

import { useEffect, useRef, type RefObject } from "react";

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled]):not([type='hidden'])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

export function useOverlayFocus({
  open,
  containerRef,
  initialFocusRef,
  skipRestoreFocusRef,
  onClose,
}: {
  open: boolean;
  containerRef: RefObject<HTMLElement | null>;
  initialFocusRef?: RefObject<HTMLElement | null>;
  skipRestoreFocusRef?: RefObject<boolean>;
  onClose: () => void;
}) {
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!open) return;

    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const focusTimer = window.setTimeout(() => {
      const fallback = containerRef.current?.querySelector<HTMLElement>(FOCUSABLE_SELECTOR);
      (initialFocusRef?.current ?? fallback)?.focus();
    }, 0);

    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        onCloseRef.current();
        return;
      }

      if (event.key !== "Tab") return;
      const focusable = Array.from(containerRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR) ?? [])
        .filter((element) => element.getClientRects().length > 0);
      if (!focusable.length) {
        event.preventDefault();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && (document.activeElement === first || !containerRef.current?.contains(document.activeElement))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (document.activeElement === last || !containerRef.current?.contains(document.activeElement))) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleKey, true);
    return () => {
      window.clearTimeout(focusTimer);
      document.removeEventListener("keydown", handleKey, true);
      document.body.style.overflow = previousOverflow;
      if (!skipRestoreFocusRef?.current) {
        window.setTimeout(() => previousFocus?.focus(), 0);
      }
    };
  }, [containerRef, initialFocusRef, open, skipRestoreFocusRef]);
}
