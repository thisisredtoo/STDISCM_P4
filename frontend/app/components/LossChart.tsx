"use client";

import React from "react";
import { Line } from "react-chartjs-2";
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from "chart.js";

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

// ★ CUSTOM BACKGROUND PLUGIN
const chartBackgroundPlugin = {
  id: "customCanvasBackgroundColor",
  beforeDraw: (chart: any, args: any, options: any) => {
    const { ctx, chartArea } = chart;
    if (!chartArea) return;
    ctx.save();
    ctx.fillStyle = options.color || "#1e1e1e"; // default background
    ctx.fillRect(chartArea.left, chartArea.top, chartArea.right - chartArea.left, chartArea.bottom - chartArea.top);
    ctx.restore();
  }
};

Chart.register(chartBackgroundPlugin);

export default function LossChart({ points }: { points: [number, number][] }) {
  const data = {
    labels: points.map(([iter]) => iter),
    datasets: [
      {
        label: "Loss",
        data: points.map(([, loss]) => loss),
        fill: false,
        tension: 0.15,
        pointRadius: 0,
        borderWidth: 2,
        borderColor: "#00ff88",   // neon line (optional)
      },
    ],
  };

  const options: any = {
    responsive: true,
    animation: false,
    scales: {
      x: { ticks: { maxTicksLimit: 8 }, grid: { color: "#444" } },
      y: { beginAtZero: false, grid: { color: "#444" } },
    },
    plugins: {
      legend: { display: false },
      tooltip: { intersect: false, mode: "index" },

      // ★ USE THE CUSTOM BACKGROUND PLUGIN
      customCanvasBackgroundColor: {
        color: "#0f0f0f" // ← SET YOUR BACKGROUND COLOR HERE
      }
    },
  };

  return <Line data={data} options={options} />;
}