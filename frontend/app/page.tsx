// page.tsx
"use client"
import React, { useEffect, useState } from "react";
import ImageGrid from "./components/ImageGrid";
import LabelGrid from "./components/LabelGrid";
import LossChart from "./components/LossChart";
import { useRealtime } from "./hooks/useRealtime"; 
import FPSMeter from "./components/FPSMeter";

let lastUpdateTime = 0;  

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
const GATEWAY_HTTP = process.env.NEXT_PUBLIC_GATEWAY_HTTP || "http://localhost:8000";

const handleWebSocketData = (msg: any, onMessage: (msg: any) => void) => {
  const currentTime = Date.now();
  if (currentTime - lastUpdateTime > 50) { 
    lastUpdateTime = currentTime;
    onMessage(msg);
  }
};

export default function Page() {
  const { connected, onBatch } = useRealtime(WS_URL); 
  const [tick, setTick] = useState(0);

  const [images, setImages] = useState<string[]>([]);
  const [labels, setLabels] = useState<(string | number)[]>([]);
  const [preds, setPreds] = useState<(string | number)[]>([]);
  const [loss, setLoss] = useState<[number, number][]>([]);

  useEffect(() => {
    let raf: number;
    const loop = () => {
      setTick((t) => (t + 1) & 0xffff);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => {
    onBatch((batch) => {
      for (const msg of batch) {
        console.log("Batch message:", msg); 

        handleWebSocketData(msg, (processedData) => {
          switch (processedData.type) {
            case "images":
              setImages(processedData.payload); 
              break;
            case "labels":
              setLabels(processedData.payload); 
              break;
            case "preds":
              setPreds(processedData.payload); 
              break;
            case "loss":
              console.log("Received loss data:", processedData.payload);  
              setLoss((prevLoss) => [...prevLoss, processedData.payload]);  
              break;
            default:
              break;
          }
        });
      }
    });
  }, [onBatch]); 

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
        <div>
          <ImageGrid title="Images" images={images} />
          <LabelGrid title="Predictions" items={preds} />
          <LabelGrid title="Ground Truth" items={labels} />
          <h3 className="text-sm font-medium mb-2">Loss</h3>
          <LossChart points={loss} />
        </div>

      </div>
    </main>
  );
}