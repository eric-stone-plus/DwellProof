import type { EvidenceStatus } from "@/lib/demo-case";
import { AlertIcon, CheckIcon, ClockIcon, FileIcon } from "@/components/icons";

export const statusLabels: Record<EvidenceStatus, string> = {
  verified: "已核实",
  user_input: "待核验",
  missing: "待补证",
  stale: "已过期",
  conflict: "存在冲突",
  not_applicable: "不适用",
};

export function StatusDot({ status }: { status: EvidenceStatus }) {
  return <span className={`status-dot status-${status}`} aria-hidden="true" />;
}

export function StatusChip({ status, label }: { status: EvidenceStatus; label?: string }) {
  const Icon = status === "verified"
    ? CheckIcon
    : status === "conflict"
      ? AlertIcon
      : status === "stale"
        ? ClockIcon
        : FileIcon;

  return (
    <span className={`status-chip status-${status}`}>
      <Icon />
      {label ?? statusLabels[status]}
    </span>
  );
}
