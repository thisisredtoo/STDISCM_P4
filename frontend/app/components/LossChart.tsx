"use client";
import React, { useMemo } from "react";
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

export default function LossChart({ points }: { points: [number, number][] }) {
  const data = useMemo(() => ({
    labels: points.map(([iter]) => iter),
    datasets: [{
      label: "Loss",
      data: points.map(([, loss]) => loss),
      fill: false,
      tension: 0.15,
      pointRadius: 0,
      borderWidth: 2
    }]
  }), [points]);

  const options: any = {
    responsive: true,
    animation: false,
    parsing: false,
    normalized: true,
    maintainAspectRatio: false,
    scales: { x: { ticks: { maxTicksLimit: 8 } }, y: { beginAtZero: false } },
    plugins: { legend: { display: false }, tooltip: { intersect: false, mode: "index" } }
  };

  return (
    <div className="h-48">
      <Line data={data} options={options} updateMode="none" />
    </div>
  );
}