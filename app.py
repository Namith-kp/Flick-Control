import os
import cv2
import threading
import asyncio
import websockets
import time
import base64
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer, BaseHTTPRequestHandler
import mimetypes
import controller as cnt
from cvzone.HandTrackingModule import HandDetector

led_states = [0, 0, 0, 0, 0]

class MultiCameraServer:
    def __init__(self):
        # Camera sources
        self.cameras = {
            'ipcam': "http://192.168.83.168:81/stream",
            'webcam': 0,
            'usbcam': 1
        }
        self.current_camera = 'webcam'
        
        # Initialize Hand Detector
        self.detector = HandDetector(detectionCon=0.8, maxHands=1)
        
        # Video capture setup
        self.video = cv2.VideoCapture(self.cameras[self.current_camera])
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.video.set(cv2.CAP_PROP_FPS, 60)
        
        # Shared variables
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.switch_requested = None

        # LED state tracking
        self.led_states = [0, 0, 0, 0, 0]

    def switch_camera(self, camera_name):
        if camera_name in self.cameras:
            # Release existing capture
            if self.video:
                self.video.release()
            
            # Special handling for ESP32-CAM
            if camera_name == 'ipcam':
                # Attempt to reinitialize ESP32-CAM stream
                try:
                    self.video = cv2.VideoCapture(self.cameras['ipcam'])
                    self.video.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Increase buffer size
                except Exception as e:
                    print(f"Error initializing ESP32-CAM: {e}")
                    return False
            else:
                # For other cameras (webcam, USB cam)
                self.video = cv2.VideoCapture(self.cameras[camera_name])
            
            # Verify camera is opened
            if not self.video.isOpened():
                print(f"Failed to open camera: {camera_name}")
                return False
            
            # Set camera properties
            self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.video.set(cv2.CAP_PROP_FPS, 60)
            
            self.current_camera = camera_name
            print(f"Switched to camera: {camera_name}")
            return True
        
        return False

    def correct_fingers_up(self, hand):
        fingers_up = [0, 0, 0, 0, 0]  # Initialize all fingers as down
        tip_ids = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips
        lm_list = hand['lmList']
        hand_type = hand['type']  # Left or Right hand

        # Thumb: Check the x-coordinates relative to the hand type
        if hand_type == "Right":
            if lm_list[tip_ids[0]][0] < lm_list[tip_ids[0] - 1][0]:  # Thumb is open
                fingers_up[0] = 1
        else:  # Left hand
            if lm_list[tip_ids[0]][0] > lm_list[tip_ids[0] - 1][0]:  # Thumb is open
                fingers_up[0] = 1

        # Other fingers: Check y-coordinates (higher means open)
        for i in range(1, 5):
            if lm_list[tip_ids[i]][1] < lm_list[tip_ids[i] - 2][1]:
                fingers_up[i] = 1

        return fingers_up

    def capture_frames(self):
        while True:
            # Check for camera switch request
            if self.switch_requested:
                self.switch_camera(self.switch_requested)
                self.switch_requested = None

            success, frame = self.video.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)  # Flip the frame horizontally
            hands, img = self.detector.findHands(frame, flipType=False)

            if hands:
                fingers_up = self.correct_fingers_up(hands[0])   # Get correct finger states
                cnt.led(fingers_up,1)
                if fingers_up==[0,0,0,0,0]:
                    cv2.putText(frame,'Finger count:0',(20,460),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),1,cv2.LINE_AA)
                elif fingers_up==[0,1,0,0,0]:
                    cv2.putText(frame,'Finger count:1',(20,460),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),1,cv2.LINE_AA)    
                elif fingers_up==[0,1,1,0,0]:
                    cv2.putText(frame,'Finger count:2',(20,460),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),1,cv2.LINE_AA)
                elif fingers_up==[0,1,1,1,0]:
                    cv2.putText(frame,'Finger count:3',(20,460),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),1,cv2.LINE_AA)
                elif fingers_up==[0,1,1,1,1]:
                    cv2.putText(frame,'Finger count:4',(20,460),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),1,cv2.LINE_AA)
                elif fingers_up==[1,1,1,1,1]:
                    cv2.putText(frame,'Finger count:5',(20,460),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),1,cv2.LINE_AA) 

            with self.frame_lock:
                self.current_frame = frame

    class VideoFeedHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/video_feed":
                self.send_response(200)
                self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
                self.send_header('Access-Control-Allow-Origin', '*')  # Allow cross-origin
                self.end_headers()

                while True:
                    if self.server.camera_server.current_frame is None:
                        continue

                    with self.server.camera_server.frame_lock:
                        _, jpeg = cv2.imencode('.jpg', self.server.camera_server.current_frame)

                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                return

            self.send_error(404, "Not Found")

    async def websocket_handler(self, websocket):
            async def stream_video():
                while True:
                    try:
                        if self.current_frame is not None:
                            _, buffer = cv2.imencode('.jpg', self.current_frame)
                            frame_base64 = base64.b64encode(buffer).decode('utf-8')
                            
                            # Send both frame and LED states
                            await websocket.send(json.dumps({
                                'type': 'frame',
                                'data': frame_base64,
                                'camera': self.current_camera,
                                'led_states': self.led_states
                            }))
                        await asyncio.sleep(0.03)
                    except websockets.exceptions.ConnectionClosed:
                        break

            async def handle_messages():
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'switch_camera':
                            camera = data.get('camera')
                            if camera in self.cameras:
                                self.switch_requested = camera
                                print(f"Camera switch requested: {camera}")

                        elif data.get('type') == 'led_control':
                            led = int(data.get('led')) - 1
                            if 0 <= led < 5:
                                self.led_states[led] = 1 - self.led_states[led]
                                cnt.led(self.led_states, 1)  # Update the LEDs
                                print(f"LED {led + 1} toggled to {self.led_states[led]}")

                    except Exception as e:
                        print(f"Message handling error: {e}")

        
            stream_task = asyncio.create_task(stream_video())
            message_task = asyncio.create_task(handle_messages())
        
            await asyncio.gather(stream_task, message_task)
        
    
    async def start_websocket_server(self):
        server = await websockets.serve(self.websocket_handler, "0.0.0.0", 8765)
        await server.wait_closed()

    def run_static_file_server(self):
        class StaticServer(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/":
                    self.path = "/landing.html"  # Serve the landing page by default
                super().do_GET()

        os.chdir("static")  # Serve files from the 'static' directory
        server = HTTPServer(('0.0.0.0', 8080), StaticServer)
        print("Static file server started at http://localhost:8080")
        server.serve_forever()

    def start_video_feed_server(self):
        class CustomHTTPServer(HTTPServer):
            def __init__(self, *args, **kwargs):
                self.camera_server = kwargs.pop('camera_server')
                super().__init__(*args, **kwargs)

        server = CustomHTTPServer(('0.0.0.0', 8000), self.VideoFeedHandler, camera_server=self)
        print("Video feed server started at http://localhost:8000/video_feed")
        server.serve_forever()

    def run(self):
        # Start the static file server in a separate thread
        static_server_thread = threading.Thread(target=self.run_static_file_server, daemon=True)
        static_server_thread.start()

        # Start the video capture thread
        capture_thread = threading.Thread(target=self.capture_frames, daemon=True)
        capture_thread.start()

        # Start WebSocket server
        websocket_thread = threading.Thread(target=lambda: asyncio.run(self.start_websocket_server()), daemon=True)
        websocket_thread.start()

        # Start the video feed server
        try:
            self.start_video_feed_server()
        except KeyboardInterrupt:
            print("\nShutting down servers...")
        finally:
            self.video.release()
            print("Video capture released.")

# Main execution
if __name__ == "__main__":
    server = MultiCameraServer()
    server.run()