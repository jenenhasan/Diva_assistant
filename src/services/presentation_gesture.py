import cv2
import threading
import time
import numpy as np
import pyautogui
import mediapipe as mp


class PresentationGestureService:
    """
    Pure service for presentation control using hand gestures.
    Detects swipe gestures to navigate slides (left/right arrows).
    No dialog, no speak/listen.
    """
    
    def __init__(self, cooldown: float = 0.8, show_camera: bool = True, 
                 min_detection_confidence: float = 0.75, swipe_threshold: float = 0.25):
        """
        Initialize the presentation gesture service.
        
        Args:
            cooldown: Minimum time between gesture triggers (seconds)
            show_camera: Whether to show the camera feed window
            min_detection_confidence: Minimum confidence for hand detection
            swipe_threshold: Minimum finger movement to trigger swipe (normalized)
        """
        # MediaPipe Setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=min_detection_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Configuration
        self._cooldown = cooldown
        self._show_camera = show_camera
        self._swipe_threshold = swipe_threshold
        
        # State variables
        self._running = False
        self._thread = None
        self._last_gesture_time = 0
        self._prev_x = None
        self._prev_y = None
        self._prev_action = None
        
        # Callback for gesture events
        self._gesture_callback = None
        
        # Available gestures
        self.GESTURE_NEXT = "next-slide"
        self.GESTURE_PREV = "prev-slide"
    
    def set_gesture_callback(self, callback):
        """
        Set a callback function to be called when a gesture is detected.
        
        Args:
            callback: Function that receives (gesture_name: str)
        """
        self._gesture_callback = callback
    
    def is_running(self) -> bool:
        """Return True if gesture tracking is active."""
        return self._running
    
    def start(self) -> dict:
        """Start gesture tracking in a background thread."""
        if self._running:
            return {"success": False, "error": "Gesture tracking already running"}
        
        self._running = True
        self._thread = threading.Thread(target=self._detect_gestures, daemon=True)
        self._thread.start()
        return {"success": True, "message": "Presentation gesture tracking started"}
    
    def stop(self) -> dict:
        """Stop gesture tracking."""
        if not self._running:
            return {"success": False, "error": "Gesture tracking not running"}
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        return {"success": True, "message": "Presentation gesture tracking stopped"}
    
    def _handle_gesture(self, gesture: str):
        """Execute the action for a detected gesture."""
        if gesture == self.GESTURE_NEXT:
            pyautogui.press("right")
        elif gesture == self.GESTURE_PREV:
            pyautogui.press("left")
        
        # Call external callback if set
        if self._gesture_callback:
            self._gesture_callback(gesture)
    
    def _detect_gestures(self):
        """Main gesture detection loop (runs in background thread)."""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            self._running = False
            return
        
        while self._running:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Flip horizontally for mirror view
            frame = cv2.flip(frame, 1)
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(image_rgb)
            
            gesture = None
            current_time = time.time()
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    if self._show_camera:
                        self.mp_drawing.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                        )
                    
                    # Get index finger tip position
                    index = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    current_x = index.x
                    
                    # Detect horizontal swipes
                    if self._prev_x is not None:
                        delta_x = current_x - self._prev_x
                        
                        # Swipe right -> next slide
                        if delta_x > self._swipe_threshold:
                            gesture = self.GESTURE_NEXT
                        # Swipe left -> previous slide
                        elif delta_x < -self._swipe_threshold:
                            gesture = self.GESTURE_PREV
                    
                    self._prev_x = current_x
                    
                    # Trigger gesture with cooldown
                    if gesture and (gesture != self._prev_action or 
                                    current_time - self._last_gesture_time > self._cooldown):
                        self._last_gesture_time = current_time
                        self._prev_action = gesture
                        self._handle_gesture(gesture)
            else:
                # Reset position tracking when hand leaves frame
                self._prev_x = None
                self._prev_y = None
            
            # Show camera feed if enabled
            if self._show_camera:
                # Add instructions on frame
                cv2.putText(frame, "Swipe RIGHT -> Next Slide", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, "Swipe LEFT -> Previous Slide", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, "Press 'q' to quit", (10, 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                cv2.imshow("Presentation Gesture Control", frame)
                if cv2.waitKey(10) & 0xFF == ord("q"):
                    break
        
        cap.release()
        if self._show_camera:
            cv2.destroyAllWindows()
    
    def __del__(self):
        """Clean up resources."""
        if self._running:
            self.stop()


if __name__ == "__main__":
    # Test the service
    print("Testing PresentationGestureService...")
    print("Controls: Swipe RIGHT -> Next Slide | Swipe LEFT -> Previous Slide")
    print("Press 'q' in the camera window or Ctrl+C to stop.")
    
    # Optional callback
    def on_gesture(gesture):
        print(f"Gesture detected: {gesture}")
    
    service = PresentationGestureService(show_camera=True)
    service.set_gesture_callback(on_gesture)
    
    print("\nStarting gesture tracking...")
    service.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping gesture tracking...")
    finally:
        service.stop()
        print("Done")