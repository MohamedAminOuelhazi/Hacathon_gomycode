import { AlertCircle, Check, LoaderCircle } from "lucide-react";
import type { ToolEvent } from "@/types/assistant";

const TOOL_LABELS: Record<string, string> = {
  get_database_schema: "Database schema",
  execute_sql: "Business data query",
  calculator: "Calculation",
  create_visualization: "Visualization",
  search_company_documents: "Company documents",
};

export function ToolEvents({ events }: { events: ToolEvent[] }) {
  if (events.length === 0) return null;
  return (
    <details className="tool-events">
      <summary>
        <span className="tool-events__summary-mark"><Check size={13} strokeWidth={2.5} /></span>
        <span>Analysis activity</span>
        <span className="tool-events__count">{events.length}</span>
      </summary>
      <ol>
        {events.map((event, index) => {
          const failed = event.status === "failed" || event.status === "error";
          return (
            <li key={`${event.tool}-${index}`}>
              <span className={`tool-events__status ${failed ? "is-failed" : ""}`}>
                {failed ? <AlertCircle size={14} /> : event.status === "running" ? <LoaderCircle className="animate-spin" size={14} /> : <Check size={14} />}
              </span>
              <span className="tool-events__body">
                <strong>{TOOL_LABELS[event.tool] ?? "Analysis step"}</strong>
                {event.summary && <small>{event.summary}</small>}
              </span>
              {typeof event.duration_ms === "number" && <time>{event.duration_ms < 1000 ? `${Math.round(event.duration_ms)} ms` : `${(event.duration_ms / 1000).toFixed(1)} s`}</time>}
            </li>
          );
        })}
      </ol>
    </details>
  );
}
