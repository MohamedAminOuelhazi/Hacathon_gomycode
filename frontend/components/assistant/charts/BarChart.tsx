"use client";

import {
  Bar,
  BarChart as RechartsBarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Visualization } from "@/types/assistant";
import { CHART_COLORS, formatChartValue } from "../chart-utils";
import { ChartFrame } from "./ChartFrame";

export function BarChart({ visualization }: { visualization: Visualization }) {
  const series = visualization.series!;
  return (
    <ChartFrame title={visualization.meta.title} description={visualization.meta.description} footer={visualization.meta.footer}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsBarChart data={visualization.data} margin={{ top: 12, right: 12, left: 2, bottom: 16 }}>
          <CartesianGrid stroke="#E4E5E1" vertical={false} />
          <XAxis dataKey={visualization.xKey} tickLine={false} axisLine={false} tick={{ fill: "#66707A", fontSize: 11 }} label={{ value: visualization.xAxisLabel ?? visualization.xKey, position: "insideBottom", offset: -10, fill: "#66707A", fontSize: 10 }} />
          <YAxis
            tickLine={false}
            axisLine={false}
            width={72}
            tick={{ fill: "#66707A", fontSize: 11 }}
            tickFormatter={(value: number) => formatChartValue(Number(value), series[0])}
            label={{ value: series[0].axisLabel ?? series[0].label ?? series[0].dataKey, angle: -90, position: "insideLeft", fill: "#66707A", fontSize: 10 }}
          />
          <Legend wrapperStyle={{ fontSize: 10, paddingTop: 2 }} />
          <Tooltip
            cursor={{ fill: "#F5F4EE" }}
            formatter={(value, name) => {
              const item = series.find((entry) => entry.dataKey === name);
              return [formatChartValue(Number(value), item), item?.label ?? String(name)];
            }}
          />
          {series.map((item, index) => (
            <Bar
              key={item.dataKey}
              dataKey={item.dataKey}
              name={item.label ?? item.dataKey}
              fill={CHART_COLORS[index % CHART_COLORS.length]}
              radius={[3, 3, 0, 0]}
              maxBarSize={44}
            />
          ))}
        </RechartsBarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
