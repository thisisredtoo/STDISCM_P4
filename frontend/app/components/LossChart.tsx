// LossChart.tsx

import React, { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import { Chart, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler } from "chart.js";

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

const LossChart = ({ points }: { points: [number, number][] }) => {
  const [data, setData] = useState({
    labels: points.map(([iter]) => iter),
    datasets: [
      {
        label: "Loss",
        data: points.map(([, loss]) => loss),
        fill: false,
        tension: 0.15,
        pointRadius: 0,
        borderWidth: 2,
        borderColor:"white"
      },
    ],
  });

  useEffect(() => {
    const interval = setInterval(() => {
      // Fetch new loss data and update the chart
      setData({
        labels: points.map(([iter]) => iter),
        datasets: [
          {
            label: "Loss",
            data: points.map(([, loss]) => loss),
            fill: false,
            tension: 0.15,
            pointRadius: 0,
            borderWidth: 2,
            borderColor:"white"
          },
        ],
      });
    }, 1000); // Update every second

    return () => clearInterval(interval);
  }, [points]);

  return <Line data={data} options={{ responsive: true }} />;
};

export default LossChart;