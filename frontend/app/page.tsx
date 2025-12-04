"use client";
import React, { useEffect, useRef, useState } from "react";
import ImageGrid from "./components/ImageGrid";
import LabelGrid from "./components/LabelGrid";
import LossChart from "./components/LossChart";
import { useRealtime } from "./hooks/useRealtime";
import { pushLoss } from "./components/utils";
import FPSMeter from "./components/FPSMeter";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
const GATEWAY_HTTP = process.env.NEXT_PUBLIC_GATEWAY_HTTP || "http://localhost:8000";

export default function Page() {
  const { connected, onBatch } = useRealtime(WS_URL);
  const [tick, setTick] = useState(0);
  const viewRef = useRef<{ images: string[]; labels: (string|number)[]; preds: (string|number)[]; loss: [number, number][] }>({ images: [], labels: [], preds: [], loss: [] });

  // rAF ticker to drive paints and FPS
  useEffect(() => {
    let raf: number;
    const loop = () => { setTick(t => (t + 1) & 0xffff); raf = requestAnimationFrame(loop); };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => onBatch((batch) => {
    for (const msg of batch) {
      switch (msg.type) {
        case "images": viewRef.current.images = msg.payload; break;
        case "labels": viewRef.current.labels = msg.payload; break;
        case "preds":  viewRef.current.preds = msg.payload; break;
        case "loss":   pushLoss(viewRef.current.loss, msg.payload); break;
        default: break; // ignore unknown types
      }
    }
  }), [onBatch]);

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
        <span className={"text-xs px-2 py-1 rounded " + (connected ? "bg-green-600" : "bg-red-600")}>{connected ? "connected" : "disconnected"}</span>
        <div className="ml-auto flex gap-2">
          <button onClick={() => postRPC({ type: "pause" })} className="px-3 py-1 rounded bg-neutral-800">Pause</button>
          <button onClick={() => postRPC({ type: "resume" })} className="px-3 py-1 rounded bg-neutral-800">Resume</button>
          <button onClick={() => postRPC({ type: "delay", ms: 300 })} className="px-3 py-1 rounded bg-neutral-800">Delay 300ms</button>
          <button onClick={() => postRPC({ type: "delay", ms: 0 })} className="px-3 py-1 rounded bg-neutral-800">No delay</button>
        </div>
        <FPSMeter key={tick} />
      </header>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <ImageGrid title="Images" images={viewRef.current.images} />
          <LabelGrid title="Ground Truth" items={viewRef.current.labels} />
        </div>
        <div>
          <LabelGrid title="Predictions" items={viewRef.current.preds} />
          <section className="mt-4">
            <h3 className="text-sm font-medium mb-2">Loss</h3>
            <LossChart points={viewRef.current.loss} />
          </section>
        </div>
      </div>
    </main>
  );
}