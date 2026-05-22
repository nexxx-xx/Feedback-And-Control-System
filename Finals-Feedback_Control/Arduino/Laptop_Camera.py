import cv2

class Camera:
    def __init__(self, camera_index=0):
        print("📷 Initializing camera...")
        self.cap = cv2.VideoCapture(camera_index)
        self.is_ready = True
        
        if not self.cap.isOpened():
            print("❌ Error: Could not open webcam.")
            self.is_ready = False

    def get_frame(self):
        """Grabs video matrix frame array."""
        if not self.is_ready:
            return False, None
            
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (640, 480))
        return ret, frame

    def cleanup(self):
        if self.cap.isOpened():
            self.cap.release()
        self.is_ready = False
        print("💤 Camera subsystem safely unlinked.")