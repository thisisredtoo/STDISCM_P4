#!/usr/bin/env python3
"""
ML Training Dashboard Server (Python Implementation)
A real-time dashboard for visualizing ML training with 60 FPS performance
"""

import grpc
from concurrent import futures
import dashboard_pb2
import dashboard_pb2_grpc
import threading
import time
import queue
from collections import deque
import numpy as np
from PIL import Image
import io

# UI Libraries
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation

class DashboardData:
    """Thread-safe data storage for dashboard"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.images = [None] * 16  # 16 image slots
        self.predictions = [""] * 16
        self.ground_truths = [""] * 16
        self.batch_index = 0
        
        # Loss history
        self.loss_iterations = deque(maxlen=1000)
        self.loss_values = deque(maxlen=1000)
        
        # Connection status
        self.last_update_time = time.time()
        self.is_connected = False
        
        # Update flags
        self.images_updated = False
        self.loss_updated = False
    
    def update_batch(self, batch_update):
        """Update image batch data"""
        with self.lock:
            num_images = min(len(batch_update.images), 16)
            
            for i in range(num_images):
                img_data = batch_update.images[i]
                
                # Decode image from bytes
                try:
                    img_bytes = io.BytesIO(img_data.image)
                    pil_img = Image.open(img_bytes)
                    self.images[i] = pil_img
                except Exception as e:
                    print(f"Error decoding image {i}: {e}")
                    self.images[i] = None
                
                # Update labels
                if i < len(batch_update.predictions):
                    self.predictions[i] = batch_update.predictions[i]
                if i < len(batch_update.groundTruths):
                    self.ground_truths[i] = batch_update.groundTruths[i]
            
            self.batch_index = batch_update.index
            self.last_update_time = time.time()
            self.is_connected = True
            self.images_updated = True
    
    def add_loss_point(self, iteration, loss_value):
        """Add loss data point"""
        with self.lock:
            self.loss_iterations.append(iteration)
            self.loss_values.append(loss_value)
            self.last_update_time = time.time()
            self.is_connected = True
            self.loss_updated = True
    
    def get_images(self):
        """Get current images (thread-safe)"""
        with self.lock:
            return (
                [img.copy() if img else None for img in self.images],
                list(self.predictions),
                list(self.ground_truths),
                self.batch_index
            )
    
    def get_loss_data(self):
        """Get loss data (thread-safe)"""
        with self.lock:
            return list(self.loss_iterations), list(self.loss_values)
    
    def check_connection(self):
        """Check if client is still connected"""
        with self.lock:
            elapsed = time.time() - self.last_update_time
            if elapsed > 5:
                self.is_connected = False
            return self.is_connected
    
    def clear_update_flags(self):
        """Clear update flags"""
        with self.lock:
            self.images_updated = False
            self.loss_updated = False

class DashboardService(dashboard_pb2_grpc.DashboardServicer):
    """gRPC service implementation"""
    
    def __init__(self, data):
        self.data = data
    
    def SendBatchUpdate(self, request, context):
        """Handle batch update from training client"""
        try:
            self.data.update_batch(request)
            print(f"✓ Received batch update #{request.index} with {len(request.images)} images")
            return dashboard_pb2.UpdateReply(
                status=True,
                message="Batch update received",
                errorCode=0
            )
        except Exception as e:
            print(f"✗ Error processing batch: {e}")
            return dashboard_pb2.UpdateReply(
                status=False,
                message=str(e),
                errorCode=1
            )
    
    def SendLossUpdate(self, request, context):
        """Handle loss update from training client"""
        try:
            self.data.add_loss_point(request.iteration, request.lossValue)
            return dashboard_pb2.UpdateReply(
                status=True,
                message="Loss update received",
                errorCode=0
            )
        except Exception as e:
            print(f"✗ Error processing loss: {e}")
            return dashboard_pb2.UpdateReply(
                status=False,
                message=str(e),
                errorCode=1
            )

def run_grpc_server(data, port=50051):
    """Run gRPC server in background thread"""
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )
    
    dashboard_pb2_grpc.add_DashboardServicer_to_server(
        DashboardService(data), server
    )
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"✓ Dashboard server listening on port {port}")
    print("="*60)
    print("Waiting for training client to connect...")
    print("="*60)
    
    return server

class DashboardGUI:
    """Main dashboard GUI using Tkinter"""
    
    def __init__(self, data):
        self.data = data
        self.root = tk.Tk()
        self.root.title("ML Training Dashboard")
        self.root.geometry("1920x1080")
        self.root.configure(bg='#2b2b2b')
        
        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        
        # Target 60 FPS (16.67ms per frame)
        self.target_frame_time = 1.0 / 60.0
        
        self.setup_ui()
        self.update_loop()
    
    def setup_ui(self):
        """Setup the UI layout"""
        # Top status bar
        status_frame = tk.Frame(self.root, bg='#1e1e1e', height=40)
        status_frame.pack(fill=tk.X, side=tk.TOP)
        
        self.fps_label = tk.Label(
            status_frame, 
            text="FPS: 0.0", 
            bg='#1e1e1e', 
            fg='#00ff00',
            font=('Consolas', 12, 'bold')
        )
        self.fps_label.pack(side=tk.LEFT, padx=10)
        
        self.connection_label = tk.Label(
            status_frame,
            text="● Disconnected",
            bg='#1e1e1e',
            fg='#ff0000',
            font=('Consolas', 12, 'bold')
        )
        self.connection_label.pack(side=tk.LEFT, padx=10)
        
        self.batch_label = tk.Label(
            status_frame,
            text="Batch: 0",
            bg='#1e1e1e',
            fg='#ffffff',
            font=('Consolas', 12)
        )
        self.batch_label.pack(side=tk.LEFT, padx=10)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg='#2b2b2b')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side: Image grid
        left_frame = tk.Frame(content_frame, bg='#2b2b2b')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        grid_label = tk.Label(
            left_frame,
            text="Training Images (16 tiles)",
            bg='#2b2b2b',
            fg='#ffffff',
            font=('Arial', 14, 'bold')
        )
        grid_label.pack(pady=5)
        
        # Create 4x4 grid of image labels
        self.image_labels = []
        self.pred_labels = []
        self.gt_labels = []
        
        grid_frame = tk.Frame(left_frame, bg='#2b2b2b')
        grid_frame.pack()
        
        for row in range(4):
            for col in range(4):
                # Frame for each tile
                tile_frame = tk.Frame(grid_frame, bg='#1e1e1e', relief=tk.RAISED, borderwidth=2)
                tile_frame.grid(row=row, column=col, padx=5, pady=5)
                
                # Image label
                img_label = tk.Label(tile_frame, bg='#1e1e1e', text="Waiting...", 
                                   fg='#666666', width=25, height=12)
                img_label.pack()
                self.image_labels.append(img_label)
                
                # GT label
                gt_label = tk.Label(tile_frame, text="GT: -", bg='#1e1e1e', 
                                  fg='#ffffff', font=('Arial', 8))
                gt_label.pack()
                self.gt_labels.append(gt_label)
                
                # Prediction label
                pred_label = tk.Label(tile_frame, text="Pred: -", bg='#1e1e1e',
                                    fg='#ffffff', font=('Arial', 8, 'bold'))
                pred_label.pack()
                self.pred_labels.append(pred_label)
        
        # Right side: Loss plot
        right_frame = tk.Frame(content_frame, bg='#2b2b2b')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        plot_label = tk.Label(
            right_frame,
            text="Training Loss",
            bg='#2b2b2b',
            fg='#ffffff',
            font=('Arial', 14, 'bold')
        )
        plot_label.pack(pady=5)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 8), facecolor='#2b2b2b')
        self.ax = self.fig.add_subplot(111, facecolor='#1e1e1e')
        self.ax.set_xlabel('Iteration', color='#ffffff')
        self.ax.set_ylabel('Loss', color='#ffffff')
        self.ax.tick_params(colors='#ffffff')
        self.ax.spines['bottom'].set_color('#ffffff')
        self.ax.spines['top'].set_color('#ffffff')
        self.ax.spines['left'].set_color('#ffffff')
        self.ax.spines['right'].set_color('#ffffff')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_fps(self):
        """Calculate and update FPS"""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time
            self.fps_label.config(text=f"FPS: {self.fps:.1f}")
    
    def update_connection_status(self):
        """Update connection status indicator"""
        is_connected = self.data.check_connection()
        if is_connected:
            self.connection_label.config(text="● Connected", fg='#00ff00')
        else:
            self.connection_label.config(text="● Disconnected", fg='#ff0000')
    
    def update_images(self):
        """Update image grid"""
        images, predictions, ground_truths, batch_idx = self.data.get_images()
        
        self.batch_label.config(text=f"Batch: {batch_idx}")
        
        for i in range(16):
            if images[i] is not None:
                # Resize image for display
                img = images[i].copy()
                img.thumbnail((200, 200))
                
                # Convert to PhotoImage
                try:
                    from PIL import ImageTk
                    photo = ImageTk.PhotoImage(img)
                    self.image_labels[i].config(image=photo, text="")
                    self.image_labels[i].image = photo  # Keep reference
                except Exception as e:
                    self.image_labels[i].config(text="Error")
                
                # Update labels
                self.gt_labels[i].config(text=f"GT: {ground_truths[i]}")
                
                # Color code predictions
                correct = predictions[i] == ground_truths[i]
                color = '#00ff00' if correct else '#ff0000'
                self.pred_labels[i].config(
                    text=f"Pred: {predictions[i]}",
                    fg=color
                )
            else:
                self.image_labels[i].config(text="Waiting...", image='')
                self.gt_labels[i].config(text="GT: -")
                self.pred_labels[i].config(text="Pred: -")
    
    def update_loss_plot(self):
        """Update loss plot"""
        iterations, losses = self.data.get_loss_data()
        
        if len(iterations) > 0:
            self.ax.clear()
            self.ax.plot(iterations, losses, color='#00ff00', linewidth=2)
            self.ax.set_xlabel('Iteration', color='#ffffff')
            self.ax.set_ylabel('Loss', color='#ffffff')
            self.ax.tick_params(colors='#ffffff')
            self.ax.grid(True, alpha=0.3, color='#ffffff')
            self.ax.set_facecolor('#1e1e1e')
            self.canvas.draw()
    
    def update_loop(self):
        """Main update loop - called every frame"""
        frame_start = time.time()
        
        # Update FPS
        self.update_fps()
        
        # Update connection status
        self.update_connection_status()
        
        # Update images if data changed
        if self.data.images_updated:
            self.update_images()
        
        # Update loss plot if data changed
        if self.data.loss_updated:
            self.update_loss_plot()
        
        # Clear flags
        self.data.clear_update_flags()
        
        # Calculate time to next frame
        frame_time = time.time() - frame_start
        delay_ms = max(1, int((self.target_frame_time - frame_time) * 1000))
        
        # Schedule next update
        self.root.after(delay_ms, self.update_loop)
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()

def main():
    """Main entry point"""
    print("="*60)
    print("ML Training Dashboard Server (Python)")
    print("="*60)
    
    # Create shared data
    data = DashboardData()
    
    # Start gRPC server in background
    server = run_grpc_server(data)
    
    # Start GUI (blocks until window closed)
    try:
        gui = DashboardGUI(data)
        gui.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.stop(0)
        print("Dashboard server stopped")

if __name__ == "__main__":
    main()