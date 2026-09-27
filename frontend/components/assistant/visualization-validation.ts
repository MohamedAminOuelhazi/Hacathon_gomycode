import type { DataPoint, Visualization } from "@/types/assistant";

const CHART_TYPES = new Set(["line", "bar", "pie", "scatter"]);

function isDataPoint(value: unknown): value is DataPoint {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  return Object.values(value).every(
    (item) => item === null || typeof item === "string" || typeof item === "number",
  );
}

export function validateVisualization(value: unknown): value is Visualization {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const chart = value as Partial<Visualization>;
  if (!CHART_TYPES.has(String(chart.chartType))) return false;
  if (!chart.meta || typeof chart.meta.title !== "string") return false;
  if (!Array.isArray(chart.data) || chart.data.length === 0 || !chart.data.every(isDataPoint)) return false;

  if (chart.chartType === "pie") {
    return Boolean(
      chart.nameKey &&
        chart.valueKey &&
        chart.data.every((point) => chart.nameKey! in point && typeof point[chart.valueKey!] === "number"),
    );
  }

  return Boolean(
    chart.xKey &&
      chart.xKey in chart.data[0] &&
      Array.isArray(chart.series) &&
      chart.series.length > 0 &&
      chart.data.every((point) => chart.xKey! in point) &&
      chart.series.every((series) => {
        if (!series || typeof series !== "object" || typeof series.dataKey !== "string") return false;
        return chart.data!.every(
          (point) => {
            const value = point[series.dataKey];
            return series.dataKey in point && (
              typeof value === "number" ||
              (value === null && (chart.chartType === "line" || chart.chartType === "bar"))
            );
          },
        );
      }),
  );
}
