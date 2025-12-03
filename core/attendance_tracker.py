import time
import winsound
import threading
from core.voice_handler import VoiceSystem  

class AttendanceTracker:
    def __init__(self, db_manager, face_handler):
        self.db_manager = db_manager
        self.face_handler = face_handler
        
        # Initialize Voice
        self.voice = VoiceSystem()
        
        # Timers
        self.last_log_time = {}        
        self.last_attendance_time = {} 
        self.last_unknown_alert_time = 0 
    
    def process_recognized_face(self, person_id, person_name):
        """
        1. Log Face: 90s gap
        2. Update Attendance: 5s gap (with Voice Feedback)
        """
        current_ts = time.time()
        
        # --- PART 1: RAW LOGGING ---
        if person_id not in self.last_log_time or \
           (current_ts - self.last_log_time[person_id] > 90.0):
            
            self.db_manager.log_raw_detection(person_id, person_name)
            self.last_log_time[person_id] = current_ts

        # --- PART 2: ATTENDANCE LOGIC & VOICE ---
        if person_id not in self.last_attendance_time or \
           (current_ts - self.last_attendance_time[person_id] > 5.0):
            
            # Perform DB Sync
            msg = self.db_manager.sync_daily_attendance(person_id)
            self.last_attendance_time[person_id] = current_ts
            
            # --- VOICE FEEDBACK -------------------------------------------
            
            if "LOGIN" in msg:
             
                self.voice.speak(f"Welcome, {person_name}. Login Successful.")
                
            elif "LOGOUT UPDATE" in msg:
              
                self.voice.speak(f"Goodbye, {person_name}. Logout Updated.")
                
            elif "Shift Ongoing" in msg:
              
                # For now, we stay silent for ongoing shifts.
                pass
            
            return True, f"{person_name}: {msg}"

        return True, None

    def process_unknown_person(self, snapshot_path, face_encoding):
        """
        Log unknown person to DB and Alert Admin
        """
        # 1. Log to DB
        result = self.db_manager.log_unknown_person(snapshot_path, face_encoding)
        
        # 2. Alert Logic (Cooldown: 15s)
        current_ts = time.time()
        if current_ts - self.last_unknown_alert_time > 15.0:
            self.last_unknown_alert_time = current_ts
            
            # Run alert in background to avoid freezing video
            threading.Thread(target=self._trigger_unknown_alert, daemon=True).start()
            
        return result

    def _trigger_unknown_alert(self):
        """Play beep and speak warning"""
        try:
            # Beep: Frequency 1000Hz, Duration 500ms
            winsound.Beep(1000, 500) 
            self.voice.speak("Unknown person detected.")
        except Exception as e:
            print(f"Alert Error: {e}")