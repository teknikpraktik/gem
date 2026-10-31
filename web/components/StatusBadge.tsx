const CLS: Record<string, string> = {
  VALID: "ok", WAITING_FOR_DATA: "wait", STALE_DATA: "wait", NO_SIGNAL: "wait", DATA_ERROR: "bad", OFFLINE_CACHED: "wait",
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`badge ${CLS[status] ?? "wait"}`} role="status">
      <span className="dot" aria-hidden="true" />
      {status}
    </span>
  );
}
