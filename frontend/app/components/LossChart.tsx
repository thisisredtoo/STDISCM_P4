// LossChart.tsx
import React from "react";
import { Line } from "react-chartjs-2";
import { Chart, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler } from "chart.js";

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

const LossChart = ({ points }: { points: [number, number][] }) => {
  const data = {
    labels: points.map(([iter]) => iter),
    datasets: [
      {
        label: "Loss",
        data: points.map(([, loss]) => loss),
        fill: false,
        borderColor: "white",  
        tension: 0.1,
        pointRadius: 0,
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    animation: {
      duration: 0, 
    },
    scales: {
      x: { ticks: { maxTicksLimit: 8 } },
      y: { beginAtZero: true },
    },
  };

  return <Line data={data} options={options} />;
};

export default LossChart;