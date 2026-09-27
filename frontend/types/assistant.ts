export type ToolStatus = "running" | "completed" | "failed" | "error";

export interface ToolEvent {
  tool: string;
  status: ToolStatus;
  duration_ms?: number;
  summary?: string;
}

export interface VisualizationSeries {
  dataKey: string;
  label?: string;
  axisLabel?: string;
  valueFormat?: "compact" | "number" | "currency" | "percent" | "integer" | "raw";
  valuePrefix?: string;
  valueSuffix?: string;
}

export type DataPoint = Record<string, string | number | null>;

export interface Visualization {
  chartType: "line" | "bar" | "pie" | "scatter";
  meta: {
    title: string;
    description?: string;
    footer?: string;
  };
  xKey?: string;
  xAxisLabel?: string;
  series?: VisualizationSeries[];
  nameKey?: string;
  valueKey?: string;
  data: DataPoint[];
}

export interface SoufetResponse {
  answer: string;
  tool_events: ToolEvent[];
  visualizations: Visualization[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: SoufetResponse;
}
