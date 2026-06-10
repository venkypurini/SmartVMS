import os
import glob
import numpy as np
from database.db_manager import get_db_connection

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    import face_recognition
    HAS_FACE_REC = True
except ImportError:
    HAS_FACE_REC = False

VISITOR_IMG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "visitor_images"))

class FaceRecognizer:
    _known_encodings = {}  # visitor_id -> face_encoding
    _loaded = False

    @staticmethod
    def initialize():
        """Pre-load face encodings of all registered visitors who have photos."""
        os.makedirs(VISITOR_IMG_DIR, exist_ok=True)
        if not HAS_FACE_REC:
            print("[FaceRec] face_recognition library not found. Running in Fallback/Simulated matching mode.")
            return False

        if FaceRecognizer._loaded:
            return True

        print("[FaceRec] Indexing and encoding visitor faces...")
        conn = get_db_connection()
        cursor = conn.cursor()
        # status is in the visits table, not visitors
        # Load photos for all visitors who have at least one non-rejected visit
        cursor.execute("""
            SELECT DISTINCT v.id, v.photo_path
            FROM visitors v
            JOIN visits vt ON vt.visitor_id = v.id
            WHERE v.photo_path IS NOT NULL
              AND vt.approval_status != 'rejected'
              AND vt.status != 'completed'
        """)
        rows = cursor.fetchall()
        conn.close()

        count = 0
        for row in rows:
            v_id = row['id']
            photo_path = row['photo_path']
            if photo_path and os.path.exists(photo_path):
                try:
                    image = face_recognition.load_image_file(photo_path)
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        FaceRecognizer._known_encodings[v_id] = encodings[0]
                        count += 1
                except Exception as e:
                    print(f"[FaceRec] Error encoding visitor {v_id} ({photo_path}): {e}")

        FaceRecognizer._loaded = True
        print(f"[FaceRec] Pre-loaded {count} visitor face encodings.")
        return True

    @staticmethod
    def reload_visitor_encoding(visitor_id, photo_path):
        """Update or insert a visitor's face encoding in the cache."""
        if not HAS_FACE_REC or not photo_path or not os.path.exists(photo_path):
            return False
        try:
            image = face_recognition.load_image_file(photo_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                FaceRecognizer._known_encodings[visitor_id] = encodings[0]
                return True
        except Exception as e:
            print(f"[FaceRec] Error encoding visitor {visitor_id}: {e}")
        return False

    @staticmethod
    def remove_visitor_encoding(visitor_id):
        """Remove a visitor's encoding from the cache."""
        if visitor_id in FaceRecognizer._known_encodings:
            del FaceRecognizer._known_encodings[visitor_id]

    @staticmethod
    def detect_faces(frame):
        """
        Detect face bounding boxes in a frame.
        Returns list of bounding boxes in format: (top, right, bottom, left)
        """
        if not HAS_OPENCV:
            return []

        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        
        if HAS_FACE_REC:
            # face_recognition takes RGB
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_small_frame)
            # Scale back up
            return [(top*2, right*2, bottom*2, left*2) for (top, right, bottom, left) in face_locations]
        else:
            # Fallback to OpenCV Haar Cascades (takes Grayscale)
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            # Load cascade from cv2 data folder
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if face_cascade.empty():
                return []
                
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            # Convert (x, y, w, h) to (top, right, bottom, left) and scale up
            face_locations = []
            for (x, y, w, h) in faces:
                top = y * 2
                left = x * 2
                bottom = (y + h) * 2
                right = (x + w) * 2
                face_locations.append((top, right, bottom, left))
            return face_locations

    @staticmethod
    def recognize_face(frame):
        """
        Recognize a face in a frame against loaded visitor encodings.
        Returns visitor_id if matched, otherwise None.
        """
        if not HAS_FACE_REC:
            # Fallback/Simulation mode — no real face_recognition library available
            # In simulation, if OpenCV detects a face, find the first visitor with
            # an approved or pending visit (status lives in visits, NOT visitors)
            faces = FaceRecognizer.detect_faces(frame)
            if faces:
                conn = get_db_connection()
                cursor = conn.cursor()
                # Pick the most recently registered visitor who is pending/approved
                cursor.execute("""
                    SELECT v.id
                    FROM visitors v
                    JOIN visits vt ON vt.visitor_id = v.id
                    WHERE vt.approval_status IN ('pending', 'approved')
                      AND vt.status != 'completed'
                    ORDER BY vt.id DESC
                    LIMIT 1;
                """)
                row = cursor.fetchone()
                conn.close()
                if row:
                    print(f"[FaceRec-Sim] Face detected! Simulated match with visitor ID: {row['id']}")
                    return row['id']
            return None

        # Real Face Recognition match
        # Convert the frame to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find all face locations and encodings in the frame
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding in face_encodings:
            # See if the face is a match for any of the known faces
            if not FaceRecognizer._known_encodings:
                continue
                
            known_ids = list(FaceRecognizer._known_encodings.keys())
            known_encs = list(FaceRecognizer._known_encodings.values())
            
            matches = face_recognition.compare_faces(known_encs, face_encoding, tolerance=0.55)
            face_distances = face_recognition.face_distance(known_encs, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    matched_id = known_ids[best_match_index]
                    print(f"[FaceRec] Match found! Visitor ID: {matched_id} (distance: {face_distances[best_match_index]:.3f})")
                    return matched_id

        return None

    @staticmethod
    def save_visitor_photo(frame, visitor_id, bounding_box=None):
        """
        Crop face from frame (optional) and save it to visitor_images.
        Returns the absolute file path where the image was saved.
        """
        os.makedirs(VISITOR_IMG_DIR, exist_ok=True)
        filename = f"{visitor_id}.jpg"
        filepath = os.path.join(VISITOR_IMG_DIR, filename)

        if not HAS_OPENCV:
            # Write a dummy placeholder file if opencv is not loaded
            with open(filepath, "wb") as f:
                f.write(b"dummy image data")
            return filepath

        try:
            if bounding_box:
                top, right, bottom, left = bounding_box
                # Add padding to crop
                h, w, _ = frame.shape
                pad_y = int((bottom - top) * 0.15)
                pad_x = int((right - left) * 0.15)
                
                crop_top = max(0, top - pad_y)
                crop_bottom = min(h, bottom + pad_y)
                crop_left = max(0, left - pad_x)
                crop_right = min(w, right + pad_x)
                
                crop_frame = frame[crop_top:crop_bottom, crop_left:crop_right]
                cv2.imwrite(filepath, crop_frame)
            else:
                cv2.imwrite(filepath, frame)
                
            print(f"[FaceRec] Saved photo for {visitor_id} at {filepath}")
            return filepath
        except Exception as e:
            print(f"[FaceRec] Error saving photo: {e}")
            return None
