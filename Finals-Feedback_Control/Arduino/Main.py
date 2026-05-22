import serial
import time
import cv2
import os
from datetime import datetime

# Cross-Module Subsystem Imports
from Audio import GateAudio
from Laptop_Camera import Camera
from Ai_Movement import MotionDetector

def get_timestamp():
    """Returns a uniformly formatted string of the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

def log_event(message):
    """Helper function to cleanly write events to a local text file with timestamps."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, 'gate_log.txt')
    
    with open(log_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"[{get_timestamp()}] {message}\n")

def main():
    print(f"[{get_timestamp()}] Starting Smart AI Gate Control Framework...")
    
    # Initialize Core Subsystems Safely
    try:
        audio_system = GateAudio()
        camera = Camera()
        ai = MotionDetector()
    except Exception as e:
        print(f"[{get_timestamp()}] Subsystem Initialization Error: {e}")
        return
    
    # =====================================================
    # PATH RESOLUTION FOR AVATAR
    # =====================================================
    script_dir = os.path.dirname(os.path.abspath(__file__))
    avatar_path = os.path.join(script_dir, 'avatar.png')
    avatar = cv2.imread(avatar_path)
    
    if avatar is not None:
        avatar = cv2.resize(avatar, (120, 120))
        if len(avatar.shape) == 3 and avatar.shape == 4:
            avatar = cv2.cvtColor(avatar, cv2.COLOR_BGRA2BGR)
        print(f"[{get_timestamp()}] Avatar graphic overlay successfully loaded.")
    else:
        print(f"[{get_timestamp()}] Warning: Missing 'avatar.png' at path location: {avatar_path}")

    # =====================================================
    # SERIAL INITIALIZATION (COM5)
    # =====================================================
    try:
        ser = serial.Serial('COM5', 9600, timeout=0.1)
        time.sleep(2.0)  # Await stable serial handshake state parameters
    except Exception as e:
        print(f"[{get_timestamp()}] Serial Port Link Failed: Could not connect to COM5. Details: {e}")
        camera.cleanup()
        return
    
    audio_system.play("SYSTEM_START")
    print(f"[{get_timestamp()}] Smart AI Gate System is now online and listening...")
    log_event("SYSTEM INITIALIZED: Gate keeper framework loaded successfully.")
    
    validation_mode = False
    validation_start_time = 0

    # Inactivity Tracker & Camera Warmup Setup
    program_start_time = time.time()  
    last_movement_time = time.time()
    warmup_duration = 2.0  # Ignore first 2 seconds of webcam exposure adjustments

    # =====================================================
    # MAIN EVENT LOOP
    # =====================================================
    while True:
        try:
            # Pump the text-to-speech audio engine data chunks
            audio_system.update()
            
            ret, frame = camera.get_frame()
            if not ret:
                print(f"[{get_timestamp()}] Video Feed Dropped.")
                break
                
            is_moving, processed_frame = ai.detect(frame)
            
            # EXPOSURE GRACE PERIOD vs REAL TRACKING
            if time.time() - program_start_time < warmup_duration:
                last_movement_time = time.time()
            else:
                if is_moving:
                    last_movement_time = time.time()
                    if audio_system.has_spoken_idle:
                        log_event("SYSTEM WAKE: Motion recovered. Aborted countdown profile.")
                    audio_system.has_spoken_idle = False 
            
            # Monitor inactivity time metrics
            idle_duration = time.time() - last_movement_time
            
            # 1. STAGE 1: AT 10 SECONDS OF NO MOTION
            if idle_duration > 10.0:
                if not audio_system.has_spoken_idle:
                    print(f"[{get_timestamp()}] [ALERT] No motion detected. Entered idle countdown state.")
                    log_event("ALERT: No motion detected. Counting down to standby threshold...")
                    
                    audio_system.play("IDLE_ALERT")
                    audio_system.has_spoken_idle = True
                
                # Draw the visual countdown warning overlay on the camera feed
                seconds_left = max(0, int(120.0 - idle_duration))
                cv2.putText(processed_frame, f"IDLE SHUTDOWN IN: {seconds_left}s", (15, 450), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # 2. STAGE 2: AT 120 SECONDS OF NO MOTION (SHUTDOWN)
            if idle_duration > 120.0:
                print(f"[{get_timestamp()}] Inactivity Shutdown triggered. Terminating sequence...")
                log_event("SHUTDOWN: Maximum inactivity window breached. System turning off.")
                
                audio_system.play_shutdown("SHUTDOWN")
                break
            
            # Safe Overlay Execution Array Validation Checks
            if avatar is not None and processed_frame.shape >= 120 and processed_frame.shape >= 120:
                processed_frame[0:120, 0:120] = avatar
            
            # Manage Gate Scan Validation Mode
            if validation_mode:
                cv2.putText(processed_frame, "SCANNING FACE...", (130, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                if is_moving:
                    validation_mode = False 
                    ser.write(b"AI_VERIFIED\n")
                    ser.flush()
                    print(f"[{get_timestamp()}] AI verified movement! Sent unlock command sequence.")
                    log_event("ACCESS VERIFIED: Person identified via camera array.")
                    
                elif time.time() - validation_start_time > 4.0: 
                    validation_mode = False 
                    audio_system.play("ACCESS_DENIED")
                    print(f"[{get_timestamp()}] Scan window timed out without qualifying verification.")
                    log_event("ACCESS DENIED: Face scanning period timed out.")

            # Render frame window
            cv2.imshow("AI Gatekeeper", processed_frame)
            
            # Immediate responsive check for keypresses to keep UI rendering smooth
            if cv2.waitKey(1) & 0xFF == ord('q'): 
                print(f"[{get_timestamp()}] Manual override detected. Stopping core operations...")
                log_event("MANUAL SHUTDOWN: Execution terminated via keyboard override input ('q').")
                break
            
            # Catch incoming triggers from Arduino
            if ser.in_waiting > 0:
                raw_data = ser.readline().decode('utf-8', errors='ignore').strip()
                data = raw_data.upper()
                
                if data:
                    print(f"[{get_timestamp()}] Data Received from Arduino: [{raw_data}]")
                    
                    if "TRIGGERED" in data or "SENSOR" in data:
                        if not validation_mode:
                            validation_mode = True
                            validation_start_time = time.time()
                            print(f"[{get_timestamp()}] Gate Sensor Tripped! Starting 4-second camera validation countdown...")
                            log_event("HARDWARE TRIGGER: Proximity/beam sensor broken. Scan sequence engaged.")
                    
                    else:
                        matched = False
                        for key in audio_system.tts_phrases:
                            if key in data:
                                audio_system.play(key)
                                
                                # Show Entry vs Exit explicitly in the terminal output
                                if key == "ENTER":
                                    print(f"[{get_timestamp()}] ACTION REGISTERED: User Entered through gate.")
                                elif key == "EXIT":
                                    print(f"[{get_timestamp()}] ACTION REGISTERED: User Exited through gate.")
                                else:
                                    print(f"[{get_timestamp()}] Audio Event Triggered: Found keyword match '{key}'")
                                
                                log_event(f"ARDUINO AUDIO EVENT: Executed speech output for '{key}'.")
                                matched = True
                                break
                        
                        if not matched:
                            print(f"[{get_timestamp()}] Warning: Received '{raw_data}' but no tracking keywords matched.")
                            log_event(f"UNKNOWN SERIAL INPUT: Received unmapped data stream: '{raw_data}'")
                        
        except serial.SerialException as ser_err:
            print(f"[{get_timestamp()}] Connection Error: Arduino link lost! Details: {ser_err}")
            log_event(f"CRITICAL ERROR: Serial connection dropped abruptly: {ser_err}")
            break
            
        except Exception as loop_err:
            print(f"[{get_timestamp()}] Warning: Main loop processing error: {loop_err}")

    # Clean Environment Up
    print(f"[{get_timestamp()}] Cleaning environment allocation data structures...")
    camera.cleanup()
    
    try:
        ser.close()
    except Exception:
        pass  
        
    cv2.destroyAllWindows()
    print(f"[{get_timestamp()}] Complete shutdown accomplished safely.")

if __name__ == '__main__':
    main()