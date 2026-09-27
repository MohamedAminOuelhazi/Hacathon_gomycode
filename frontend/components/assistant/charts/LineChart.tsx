"use client";

import {
  CartesianGrid,
  Line,
  LineChart as RechartsLineChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Visualization } from "@/types/assistant";
import { CHART_COLORS, formatChartValue } from "../chart-utils";
import { ChartFrame } from "./ChartFrame";

export function LineChart({ visualization }: { visualization: Visualization }) {
  const xKey = visualization.xKey!;
  const series = visualization.series!;
  return (
    <ChartFrame title={visualization.meta.title} description={visualization.meta.description} footer={visualization.meta.footer}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsLineChart data={visualization.data} margin={{ top: 12, right: 12, left: 2, bottom: 16 }}>
          <CartesianGrid stroke="#E4E5E1" vertical={false} />
          <XAxis dataKey={xKey} tickLine={false} axisLine={false} tick={{ fill: "#66707A", fontSize: 11 }} minTickGap={16} label={{ value: visualization.xAxisLabel ?? xKey, position: "insideBottom", offset: -10, fill: "#66707A", fontSize: 10 }} />
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
            cursor={{ stroke: "#BFC5D2", strokeDasharray: "4 4" }}
            formatter={(value, name) => {
              const item = series.find((entry) => entry.dataKey === name);
              return [formatChartValue(Number(value), item), item?.label ?? String(name)];
            }}
          />
          {series.map((item, index) => (
            <Line
              key={item.dataKey}
              type="monotone"
              dataKey={item.dataKey}
              name={item.label ?? item.dataKey}
              stroke={CHART_COLORS[index % CHART_COLORS.length]}
              strokeWidth={2.5}
              dot={{ r: 3, fill: CHART_COLORS[index % CHART_COLORS.length], strokeWidth: 0 }}
              activeDot={{ r: 5 }}
              connectNulls={false}
            />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
