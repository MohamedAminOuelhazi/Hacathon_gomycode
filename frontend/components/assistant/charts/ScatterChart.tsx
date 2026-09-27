"use client";

import {
  CartesianGrid,
  Legend,
  Scatter,
  ScatterChart as RechartsScatterChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { Visualization } from "@/types/assistant";
import { CHART_COLORS, formatChartValue } from "../chart-utils";
import { ChartFrame } from "./ChartFrame";

export function ScatterChart({ visualization }: { visualization: Visualization }) {
  const series = visualization.series!;
  return (
    <ChartFrame title={visualization.meta.title} description={visualization.meta.description} footer={visualization.meta.footer}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsScatterChart margin={{ top: 12, right: 18, left: 2, bottom: 4 }}>
          <CartesianGrid stroke="#E4E5E1" />
          <XAxis
            type="number"
            dataKey="__soufetX"
            name={visualization.xAxisLabel ?? visualization.xKey}
            tickLine={false}
            axisLine={false}
            tick={{ fill: "#66707A", fontSize: 11 }}
          />
          <YAxis
            type="number"
            dataKey="__soufetY"
            name={series[0].label ?? series[0].dataKey}
            tickLine={false}
            axisLine={false}
            width={72}
            tick={{ fill: "#66707A", fontSize: 11 }}
            tickFormatter={(value: number) => formatChartValue(Number(value), series[0])}
            label={{ value: series[0].axisLabel ?? series[0].label ?? series[0].dataKey, angle: -90, position: "insideLeft", fill: "#66707A", fontSize: 10 }}
          />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          <ZAxis range={[54, 54]} />
          <Tooltip
            cursor={{ strokeDasharray: "4 4" }}
            formatter={(value, name) => {
              const item = series.find((entry) => entry.label === name || entry.dataKey === name);
              return [formatChartValue(Number(value), item), String(name)];
            }}
          />
          {series.map((item, index) => (
            <Scatter
              key={item.dataKey}
              name={item.label ?? item.dataKey}
              data={visualization.data.map((point) => ({
                ...point,
                __soufetX: point[visualization.xKey!],
                __soufetY: point[item.dataKey],
              }))}
              dataKey="__soufetY"
              fill={CHART_COLORS[index % CHART_COLORS.length]}
            />
          ))}
        </RechartsScatterChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
