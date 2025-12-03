"use client";
import { useEffect, useRef, useState } from "react";

/**
 * WebSocket hook with jittered backoff, heartbeat, and rAF-based batch flush.
 * Usage: const { connected, onBatch } = useRealtime(process.env.NEXT_PUBLIC_WS_URL!);
 */
export function useRealtime(url: string) {
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const queueRef = useRef<any[]>([]);
  const listenersRef = useRef<((m: any[]) => void)[]>([]);
  const rafRef = useRef(0 as number | 0);
  const hbRef = useRef<{ timer?: any; watchdog?: any }>({});

  const flush = () => {
    if (!queueRef.current.length) { rafRef.current = 0; return; }
    const batch = queueRef.current.splice(0, queueRef.current.length);
    for (const cb of listenersRef.current) cb(batch);
    rafRef.current = requestAnimationFrame(flush);
  };

  const startHeartbeat = () => {
    clearInterval(hbRef.current.timer); clearTimeout(hbRef.current.watchdog);
    hbRef.current.timer = setInterval(() => {
      try { socketRef.current?.send(JSON.stringify({ type: "ping" })); } catch {}
      clearTimeout(hbRef.current.watchdog);
      hbRef.current.watchdog = setTimeout(() => socketRef.current?.close(), 5000);
    }, 10000);
  };

  useEffect(() => {
    let tries = 0, cancelled = false;
    const connect = () => {
      const ws = new WebSocket(url);
      socketRef.current = ws;
      ws.onopen = () => { tries = 0; setConnected(true); startHeartbeat(); };
      ws.onmessage = (e) => {
        let msg: any;
        try { msg = JSON.parse(e.data); } catch { return; }
        if (msg?.type === "pong") { clearTimeout(hbRef.current.watchdog); return; }
        queueRef.current.push(msg);
        if (!rafRef.current) rafRef.current = requestAnimationFrame(flush);
      };
      ws.onclose = () => {
        setConnected(false);
        clearInterval(hbRef.current.timer); clearTimeout(hbRef.current.watchdog);
        if (cancelled) return;
        const base = Math.min(10000, 500 * Math.pow(2, tries++));
        const jitter = base * (0.8 + Math.random() * 0.4);
        setTimeout(connect, jitter);
      };
      ws.onerror = () => ws.close();
    };
    connect();
    return () => { cancelled = true; socketRef.current?.close(); };
  }, [url]);

  const onBatch = (cb: (msgs: any[]) => void) => {
    listenersRef.current.push(cb);
    return () => { listenersRef.current = listenersRef.current.filter(x => x !== cb); };
  };

  return { connected, onBatch };
}