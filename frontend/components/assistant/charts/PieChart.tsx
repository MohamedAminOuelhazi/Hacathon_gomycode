"use client";

import {
  Cell,
  Pie,
  PieChart as RechartsPieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { Visualization } from "@/types/assistant";
import { CHART_COLORS, formatChartValue } from "../chart-utils";
import { ChartFrame } from "./ChartFrame";

export function PieChart({ visualization }: { visualization: Visualization }) {
  const series = visualization.series?.[0];
  return (
    <ChartFrame title={visualization.meta.title} description={visualization.meta.description} footer={visualization.meta.footer}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsPieChart>
          <Pie
            data={visualization.data}
            dataKey={visualization.valueKey}
            nameKey={visualization.nameKey}
            innerRadius="48%"
            outerRadius="78%"
            paddingAngle={2}
            stroke="#FFFFFF"
            strokeWidth={2}
          >
            {visualization.data.map((point, index) => (
              <Cell key={`${String(point[visualization.nameKey!])}-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => formatChartValue(Number(value), series)} />
        </RechartsPieChart>
      </ResponsiveContainer>
      <div className="pie-legend">
        {visualization.data.map((point, index) => (
          <div className="pie-legend__item" key={`${String(point[visualization.nameKey!])}-${index}`}>
            <span style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }} />
            <span>{String(point[visualization.nameKey!])}</span>
            <strong>{formatChartValue(Number(point[visualization.valueKey!]), series)}</strong>
          </div>
        ))}
      </div>
    </ChartFrame>
  );
}
