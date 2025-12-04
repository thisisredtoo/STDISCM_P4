// "use client";
// import React, { useMemo } from "react";
// import { Line } from "react-chartjs-2";
// import {
//   Chart,
//   CategoryScale,
//   LinearScale,
//   PointElement,
//   LineElement,
//   Tooltip,
//   Filler,
// } from "chart.js";

// Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

// export default function LossChart({ points }: { points: [number, number][] }) {
//   const data = useMemo(() => ({
//     // labels: points.map(([iter]) => iter),
//     datasets: [{
//       label: "Loss",
//       data: points.map(([, loss]) => loss),
//       fill: false,
//       tension: 0.15,
//       pointRadius: 2,
//       showLine: true,
//       borderWidth: 4
//     }]
//   }), [points]);

//   const options: any = {
//     responsive: true,
//     animation: false,
//     parsing: false,
//     normalized: true,
//     maintainAspectRatio: false,
//     scales: { x: { ticks: { maxTicksLimit: 8 } }, y: { beginAtZero: false } },
//     plugins: { legend: { display: false }, tooltip: { intersect: false, mode: "index" } }
//   };

//   return (
//     <div className="h-48 border border-black rounded-md p-2">
//       <Line data={data} options={options} updateMode="none" />
//     </div>
//   );
// }


"use client";
import React, { useMemo, useState, useEffect } from "react";
import { Line } from "react-chartjs-2";
import { Chart, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler } from "chart.js";

// Register Chart.js components
Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

export default function LossChart({ points }: { points: [number, number][] }) {
  console.log("Points received in LossChart:", points);  // Log the points received

  const [chartData, setChartData] = useState<{ x: number; y: number }[]>([]);

  useEffect(() => {
    if (points.length > 0) {
      console.log("Updating chart data with points:", points);  // Log points before updating
      setChartData((prevData) => {
        const newData = [...prevData, { x: points[0][0], y: points[0][1] }];
        return newData.length > 500 ? newData.slice(-500) : newData; // Keep only the last 500 points
      });
    }
  }, [points]); // When points change, update chartData

  const data = useMemo(() => ({
    datasets: [{
      label: "Loss",
      data: chartData,
      fill: false,
      tension: 0.4,  // Controls line smoothness
      pointRadius: 3,
      borderWidth: 4,
      borderColor: "rgba(75, 192, 192, 1)",
      pointBackgroundColor: "rgba(75, 192, 192, 1)",
    }]
  }), [chartData]);  // Re-render chart when chartData updates

  const options: any = {
    responsive: true,
    animation: false,
    parsing: false,
    maintainAspectRatio: false,
    scales: {
      x: { type: 'linear', position: 'bottom', title: { text: 'Iteration', display: true } },
      y: { title: { text: 'Loss', display: true }, beginAtZero: false }
    },
    plugins: {
      legend: { display: false },
      tooltip: { intersect: false, mode: "index" }
    }
  };

  return (
    <div className="h-64 border border-black rounded-md p-2">
      <Line data={data} options={options} />
    </div>
  );
}
