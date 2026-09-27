import type { VisualizationSeries } from "@/types/assistant";

export const CHART_COLORS = ["#2B5CFF", "#12A594", "#E67E56", "#8B69C6", "#A6BF20"];

export function formatChartValue(value: number, series?: VisualizationSeries) {
  const format = series?.valueFormat ?? "compact";
  let formatted: string;

  if (format === "currency" && series?.valuePrefix === "$") {
    formatted = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      notation: "compact",
      maximumFractionDigits: 2,
    }).format(value);
    return `${formatted}${series.valueSuffix ?? ""}`;
  }

  const options: Intl.NumberFormatOptions =
    format === "compact"
      ? { notation: "compact", maximumFractionDigits: 2 }
      : format === "integer"
        ? { maximumFractionDigits: 0 }
        : format === "percent"
          ? { style: "percent", maximumFractionDigits: 2 }
          : {};

  formatted = new Intl.NumberFormat("en-US", options).format(value);
  return `${series?.valuePrefix ?? ""}${formatted}${series?.valueSuffix ?? ""}`;
}
