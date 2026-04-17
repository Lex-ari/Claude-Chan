#!/usr/bin/env python3
"""
Expression Display - Visual personality display for Claude
Shows current expression/emotion in a separate GUI window
"""
import tkinter as tk
from PIL import Image, ImageTk
import socket
import threading
import json
import os

class ExpressionDisplay:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.expressions_dir = os.path.dirname(__file__)

        # Create main window
        self.root = tk.Tk()
        self.root.title("Claude's Expression")
        self.root.geometry("200x200")
        self.root.configure(bg='#1a1a1a')

        # Make window stay on top
        self.root.attributes('-topmost', True)

        # Create image label
        self.image_label = tk.Label(
            self.root,
            bg='#1a1a1a'
        )
        self.image_label.pack(expand=True)

        # Load default image
        self.load_expression('neutral')

        # Start server thread
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()

    def start_server(self):
        """Listen for incoming expression updates"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(5)

            while True:
                try:
                    conn, addr = s.accept()
                    with conn:
                        data = conn.recv(1024).decode('utf-8')
                        if data:
                            self.handle_message(data)
                except Exception as e:
                    print(f"Server error: {e}")

    def handle_message(self, data):
        """Process incoming expression message"""
        try:
            msg = json.loads(data)
            image_name = msg.get('image', 'neutral')

            # Update UI from main thread
            self.root.after(0, self.load_expression, image_name)
        except json.JSONDecodeError:
            # Simple text message - treat as image name
            self.root.after(0, self.load_expression, data.strip())

    def load_expression(self, image_name):
        """Load and display an expression image"""
        # Try different image formats
        for ext in ['.png', '.jpg', '.jpeg', '.gif']:
            image_path = os.path.join(self.expressions_dir, f"{image_name}{ext}")
            if os.path.exists(image_path):
                try:
                    img = Image.open(image_path)
                    # Resize to fit window (max 380x380)
                    img.thumbnail((180,180), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.image_label.config(image=photo, text="")
                    self.image_label.image = photo  # Keep a reference
                    return True
                except Exception as e:
                    print(f"Error loading {image_path}: {e}")

        # Fallback: show text if image not found
        self.image_label.config(text=f"[{image_name} not found]", fg='#888888', image='')
        return False

    def run(self):
        """Start the GUI event loop"""
        self.root.mainloop()

if __name__ == '__main__':
    app = ExpressionDisplay()
    print("Expression Display started. Listening on localhost:9876")
    print("Send JSON messages like: {\"image\": \"thinking\"}")
    app.run()
