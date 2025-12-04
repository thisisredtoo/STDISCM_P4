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
import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

export default function LossChart({ points }: { points: [number, number][] }) {
  const [chartData, setChartData] = useState<{ iteration: number; loss: number }[]>([]);

  useEffect(() => {
    if (points.length > 0) {
      // Append new loss point to chart data
      setChartData((prevData) => {
        const newData = [...prevData, { iteration: points[0][0], loss: points[0][1] }];
        return newData.length > 500 ? newData.slice(-500) : newData; // Keep only the last 500 points
      });
    }
  }, [points]); // Whenever `points` change, update chart data

  return (
    <div className="h-96 w-full border border-black rounded-md p-2">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="iteration" label={{ value: "Iteration", position: "insideBottom" }} />
          <YAxis label={{ value: "Loss", angle: -90, position: "insideLeft" }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="loss" stroke="#8884d8" activeDot={{ r: 8 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

