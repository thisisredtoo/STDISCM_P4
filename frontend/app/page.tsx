// page.tsx
"use client";
import React, { useEffect, useState } from "react";
import ImageGrid from "./components/ImageGrid";
import LabelGrid from "./components/LabelGrid";
import LossChart from "./components/LossChart";
import { useRealtime } from "./hooks/useRealtime";  // Import the custom hook
import FPSMeter from "./components/FPSMeter";

let lastUpdateTime = 0;  // Track the last update time for throttling

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
const GATEWAY_HTTP = process.env.NEXT_PUBLIC_GATEWAY_HTTP || "http://localhost:8000";

// Throttled WebSocket data handler
const handleWebSocketData = (msg: any, onMessage: (msg: any) => void) => {
  const currentTime = Date.now();
  if (currentTime - lastUpdateTime > 50) {  // Throttle updates to 20 FPS
    lastUpdateTime = currentTime;
    onMessage(msg);
  }
};

export default function Page() {
  const { connected, onBatch } = useRealtime(WS_URL);  // Use the hook
  const [tick, setTick] = useState(0);

  // States for images, labels, predictions, and loss
  const [images, setImages] = useState<string[]>([]);
  const [labels, setLabels] = useState<(string | number)[]>([]);
  const [preds, setPreds] = useState<(string | number)[]>([]);
  const [loss, setLoss] = useState<[number, number][]>([]);

  // Update the tick count for the FPSMeter
  useEffect(() => {
    let raf: number;
    const loop = () => {
      setTick((t) => (t + 1) & 0xffff);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  // Handling WebSocket data reception and updating states
  useEffect(() => {
    onBatch((batch) => {
      for (const msg of batch) {
        console.log("Batch message:", msg);  // Log the received batch data

        // Throttling the processing of WebSocket data updates
        handleWebSocketData(msg, (processedData) => {
          switch (processedData.type) {
            case "images":
              setImages(processedData.payload);  // Update images
              break;
            case "labels":
              setLabels(processedData.payload);  // Update labels
              break;
            case "preds":
              setPreds(processedData.payload);  // Update predictions
              break;
            case "loss":
              console.log("Received loss data:", processedData.payload);  // Log the received loss data
              setLoss((prevLoss) => [...prevLoss, processedData.payload]);  // Add new loss data
              break;
            default:
              break; // Ignore unknown message types
          }
        });
      }
    });
  }, [onBatch]);  // Re-run whenever `onBatch` changes

  // Handling RPC actions (pause, resume, etc.)
  const postRPC = async (body: any) => {
    await fetch(`${GATEWAY_HTTP}/rpc`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  };

  return (
    <main className="p-4 space-y-4">
      <header className="flex items-center gap-3">
        <h1 className="text-xl font-semibold">Training Dashboard</h1>
        <span className={"text-xs px-2 py-1 rounded " + (connected ? "bg-green-600" : "bg-red-600")}>
          {connected ? "connected" : "disconnected"}
        </span>
        <FPSMeter />
      </header>

      <div className="grid grid-cols-2 gap-6">
        {/* Left side: Images and Labels */}
        <div>
          <ImageGrid title="Images" images={images} />
          <LabelGrid title="Predictions" items={preds} />
          <LabelGrid title="Ground Truth" items={labels} />
          <h3 className="text-sm font-medium mb-2">Loss</h3>
          <LossChart points={loss} />  {/* Loss chart now updates in real time */}
        </div>

        {/* Right side: Loss chart */}
        <div>
          <section className="mt-4 ml-10">
            {/* You can add additional UI components here */}
          </section>
        </div>
      </div>
    </main>
  );
}