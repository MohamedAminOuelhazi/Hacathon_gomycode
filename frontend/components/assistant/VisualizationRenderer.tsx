"use client";

import type { Visualization } from "@/types/assistant";
import { BarChart } from "./charts/BarChart";
import { LineChart } from "./charts/LineChart";
import { PieChart } from "./charts/PieChart";
import { ScatterChart } from "./charts/ScatterChart";
import { validateVisualization } from "./visualization-validation";

export function VisualizationRenderer({ visualization }: { visualization: unknown }) {
  if (!validateVisualization(visualization)) {
    return <p className="visualization-error">This visualization could not be rendered.</p>;
  }

  const chart = visualization as Visualization;
  switch (chart.chartType) {
    case "line":
      return <LineChart visualization={chart} />;
    case "bar":
      return <BarChart visualization={chart} />;
    case "pie":
      return <PieChart visualization={chart} />;
    case "scatter":
      return <ScatterChart visualization={chart} />;
    default:
      return null;
  }
}
