import cv2

class MotionDetector:
    def __init__(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=50, detectShadows=False
        )

    def detect(self, frame):
        motion_detected = False
        render_frame = frame  # Avoid initial deep copies unless motion is verified
        
        # Calculate frame area to filter global flash artifacts (clouds/lighting changes)
        frame_area = frame.shape[0] * frame.shape[1]
        
        fg_mask = self.bg_subtractor.apply(frame)
        fg_mask = cv2.medianBlur(fg_mask, 5)
        
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Target size profile threshold rules (Human size window limits)
            if 5000 < area < (frame_area * 0.85):
                if not motion_detected:
                    render_frame = frame.copy() # Motion confirmed; make a draw copy now
                    motion_detected = True
                
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(render_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
        return motion_detected, render_frame