// hooks/useRealtime.ts
import { useEffect, useState } from "react";

export const useRealtime = (wsUrl: string) => {
  const [connected, setConnected] = useState(false);
  const [batchData, setBatchData] = useState<any[]>([]); // Adjust type based on actual data

  useEffect(() => {
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log("WebSocket connected!");
      setConnected(true);
    };

    socket.onmessage = (event) => {
      const newData = JSON.parse(event.data);
      setBatchData((prevData) => [...prevData, newData]);
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    socket.onclose = () => {
      console.log("WebSocket connection closed");
      setConnected(false);
    };

    // Cleanup on component unmount
    return () => {
      socket.close();
    };
  }, [wsUrl]);

  // Return relevant data and status
  return { connected, onBatch: (callback: (batch: any[]) => void) => callback(batchData) };
};