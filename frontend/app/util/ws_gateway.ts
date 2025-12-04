import WebSocket from "ws";

// Declare socket in a higher scope
let socket: WebSocket | null = null;

// WebSocket client setup to communicate with the training server
export const connectToServer = () => {
  socket = new WebSocket("ws://localhost:8000/ws"); // Your training server WebSocket URL

  // On successful connection
  socket.onopen = () => {
    console.log("WebSocket connected!");
  };

  // Handling incoming messages from the server
  socket.onmessage = (event) => {
    // Check if the data is a string and parse it, or handle the buffer case
    const newData = typeof event.data === "string" ? JSON.parse(event.data) : null;
    if (newData) {
      updateDashboard(newData); // A function to update the dashboard with the new data
    } else {
      console.error("Received invalid data:", event.data);
    }
  };

  // Handling WebSocket errors
  socket.onerror = (error) => {
    console.error("WebSocket error:", error);
    alert("Error connecting to the server. Retrying...");
    reconnectToServer(); // Retry connection if there is an error
  };

  // Handling WebSocket closure
  socket.onclose = () => {
    console.log("Connection closed. Attempting to reconnect...");
    reconnectToServer(); // Attempt to reconnect after the connection closes
  };
};

// Reconnection logic in case of failure
export const reconnectToServer = () => {
  setTimeout(() => {
    console.log("Attempting to reconnect...");
    connectToServer(); // Try to reconnect after a delay
  }, 5000); // Reconnect after 5 seconds
};

// Simulating network failure for testing fault tolerance
export const simulateNetworkFailure = () => {
  if (socket) {
    socket.close(); // Close the WebSocket connection to simulate a failure
    console.log("Simulating network failure...");
    setTimeout(() => {
      connectToServer(); // Attempt reconnection after 5 seconds
    }, 5000);
  } else {
    console.error("No WebSocket connection to close.");
  }
};

// Function to update the dashboard with the new data from the training process
export const updateDashboard = (data: any) => {
  // Logic to update the dashboard with new training data (e.g., loss, images, etc.)
  console.log("New Data: ", data);
  // You can use state management or props to update your components based on the data received
};

// Initial connection to the training server
connectToServer();