import { useEffect, useState } from "react";

import { checkHealth } from "../api/client";

type Status = "checking" | "up" | "down";

const POLL_INTERVAL_MS = 15_000;

const CHIP_STYLES: Record<Status, string> = {
  checking: "bg-slate-100 text-slate-600 ring-slate-200",
  up: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  down: "bg-rose-50 text-rose-700 ring-rose-200",
};

const DOT_STYLES: Record<Status, string> = {
  checking: "bg-slate-400 animate-pulse",
  up: "bg-emerald-500",
  down: "bg-rose-500",
};

const LABELS: Record<Status, string> = {
  checking: "Checking services…",
  up: "document-service online",
  down: "document-service unreachable",
};

export function HealthBadge() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    let active = true;

    async function poll() {
      try {
        await checkHealth();
        if (active) {
          setStatus("up");
        }
      } catch {
        if (active) {
          setStatus("down");
        }
      }
    }

    void poll();
    const timer = window.setInterval(() => void poll(), POLL_INTERVAL_MS);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset ${CHIP_STYLES[status]}`}
    >
      <span className={`size-2 rounded-full ${DOT_STYLES[status]}`} aria-hidden="true" />
      {LABELS[status]}
    </span>
  );
}
