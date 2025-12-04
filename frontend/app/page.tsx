"use client";
import React, { useEffect, useRef, useState } from "react";
import ImageGrid from "./components/ImageGrid";
import LabelGrid from "./components/LabelGrid";
import LossChart from "./components/LossChart";
import { useRealtime } from "./hooks/useRealtime";
import FPSMeter from "./components/FPSMeter";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
const GATEWAY_HTTP = process.env.NEXT_PUBLIC_GATEWAY_HTTP || "http://localhost:8000";

export default function Page() {
  const { connected, onBatch } = useRealtime(WS_URL);
  const [tick, setTick] = useState(0);

  // Initialize viewRef to store images, labels, predictions, and loss data
  const viewRef = useRef<{ images: string[]; labels: (string | number)[]; preds: (string | number)[]; loss: [number, number][] }>({
    images: [],
    labels: [],
    preds: [],
    loss: [],
  });

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

  // Handling WebSocket data reception and updating `viewRef.current.loss`
  useEffect(() => {
    onBatch((batch) => {
      for (const msg of batch) {
        console.log("Batch message:", msg);  // Log the received batch data

        switch (msg.type) {
          case "images":
            viewRef.current.images = msg.payload;
            break;
          case "labels":
            viewRef.current.labels = msg.payload;
            break;
          case "preds":
            viewRef.current.preds = msg.payload;
            break;
          case "loss":
            console.log("Received loss data:", msg.payload);  // Log the received loss data
            viewRef.current.loss.push(msg.payload);  // Add the received loss data
            break;
          default:
            break; // Ignore unknown message types
        }
      }
    });
  }, [onBatch]);

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
          <ImageGrid title="Images" images={viewRef.current.images} />
          <LabelGrid title="Predictions" items={viewRef.current.preds} />
          <LabelGrid title="Ground Truth" items={viewRef.current.labels} />
          <h3 className="text-sm font-medium mb-2">Loss</h3>
            <LossChart points={viewRef.current.loss} />
        </div>

        {/* Right side: Loss chart */}
        <div>
          <section className="mt-4 ml-10">
            
          </section>
        </div>
      </div>
    </main>
  );
}
