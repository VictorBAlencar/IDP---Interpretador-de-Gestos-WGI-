import time
import threading
import math
import traceback
import platform
import pyautogui
import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import calculo_distancia as util
import cursor_movement as cursor_movement
import left_click as left_click
import right_click as right_click
import double_click as double_click
import scroll as scroll
import calibration_manager as calibration_manager

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
try:
    screen_w, screen_h = pyautogui.size()
except Exception as exc:
    print(f"Aviso: Falha ao obter tamanho da tela via PyAutoGUI: {exc}")
    screen_w, screen_h = 1920, 1080

last_click_time = 0
click_cooldown = 0.7
click_confirmation_frames = 3
drag_hold_threshold = 0.8
is_dragging = False
last_left_click_detected_time = 0
is_tracking = False
left_click_start_time = 0
mouse_down_triggered = False
wizard_active = False
left_click_candidate_frames = 0
right_click_candidate_frames = 0
double_click_candidate_frames = 0
right_click_armed = True
double_click_armed = True
mouse_action_error_logged = False

calibration_gesture = None
calibration_idx_history = []
calibration_mid_history = []
calibration_thumb_history = []

latest_frame = None

current_state = {
    "x": 0.5,
    "y": 0.5,
    "action": "move",
    "calibration": {"status": "idle", "gesture": None}
}
camera_ready_event = threading.Event()

def should_suppress_mouse_actions():
    return calibration_gesture is not None

def perform_mouse_action(action_name, *args, **kwargs):
    global mouse_action_error_logged

    try:
        getattr(pyautogui, action_name)(*args, **kwargs)
        return True
    except Exception as exc:
        if not mouse_action_error_logged:
            print(f"Aviso: PyAutoGUI nao conseguiu executar '{action_name}': {exc}")
            print("No macOS, permita Camera e Accessibility para o app/Terminal nas configuracoes de privacidade.")
            mouse_action_error_logged = True
        return False

def cancel_calibration():
    global calibration_gesture, calibration_idx_history, calibration_mid_history, calibration_thumb_history

    calibration_gesture = None
    calibration_idx_history = []
    calibration_mid_history = []
    calibration_thumb_history = []
    current_state["calibration"] = {"status": "idle", "gesture": None}

def reset_interaction_state():
    global is_dragging, last_left_click_detected_time, left_click_start_time, mouse_down_triggered
    global left_click_candidate_frames, right_click_candidate_frames, double_click_candidate_frames
    global right_click_armed, double_click_armed

    if is_dragging and mouse_down_triggered:
        perform_mouse_action("mouseUp")

    is_dragging = False
    mouse_down_triggered = False
    last_left_click_detected_time = 0
    left_click_start_time = 0
    left_click_candidate_frames = 0
    right_click_candidate_frames = 0
    double_click_candidate_frames = 0
    right_click_armed = True
    double_click_armed = True
    left_click.reset_state()
    right_click.reset_state()
    double_click.reset_state()

def detect_gesture(frame, landmark_list, processed):
    import cv2  
    global last_click_time, is_dragging, last_left_click_detected_time
    global left_click_start_time, mouse_down_triggered
    global calibration_gesture, calibration_idx_history, calibration_mid_history, calibration_thumb_history
    global current_state
    global wizard_active
    global left_click_candidate_frames, right_click_candidate_frames, double_click_candidate_frames
    global right_click_armed, double_click_armed

    current_time = time.time()
    action = "move"

    if len(landmark_list) >= 21:
        hand_landmarks = processed.multi_hand_landmarks[0]
        palm_center = cursor_movement.get_palm_center(hand_landmarks)
        
        if calibration_gesture:
            idx_angle = util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8])
            mid_angle = util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12])
            thumb_dist = util.get_distance(landmark_list, 4, 5)
            
            calibration_idx_history.append(idx_angle)
            calibration_mid_history.append(mid_angle)
            calibration_thumb_history.append(thumb_dist)
            
            # Record for ~1.5 seconds (45 frames) to get a stable average
            if len(calibration_idx_history) >= 45:
                completed_gesture = calibration_gesture
                calibrated = calibration_manager.auto_calibrate(completed_gesture, calibration_idx_history, calibration_mid_history, calibration_thumb_history)
                calibration_gesture = None
                current_state["action"] = "calibrated" if calibrated else "calibration_failed"
                current_state["calibration"] = {
                    "status": "saved" if calibrated else "failed",
                    "gesture": completed_gesture
                }
            else:
                current_state["action"] = "calibrating"
                current_state["calibration"] = {"status": "recording", "gesture": calibration_gesture}
                cv2.putText(frame, f"Calibrating...", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            return
     
        x, y = cursor_movement.get_normalized_position(palm_center, landmark_list)
        
        if x is not None and y is not None:
            current_state["x"], current_state["y"] = x, y
            if not should_suppress_mouse_actions():
                perform_mouse_action("moveTo", int(x * screen_w), int(y * screen_h))

        thumb_index_dist = util.get_distance(landmark_list, 4, 5)
        
        is_scrolling, scroll_amount = scroll.detect_scroll(landmark_list)
        raw_is_db = double_click.is_double_click(landmark_list, thumb_index_dist)
        raw_is_rc = right_click.is_right_click(landmark_list, thumb_index_dist)
        raw_is_lc = left_click.is_left_click(landmark_list, thumb_index_dist, is_dragging)

        if is_scrolling:
            raw_is_db = False
            raw_is_rc = False
            raw_is_lc = False

        if is_dragging:
            is_lc = raw_is_lc
        else:
            if raw_is_lc:
                left_click_candidate_frames += 1
            else:
                left_click_candidate_frames = 0
            is_lc = left_click_candidate_frames >= click_confirmation_frames

        if raw_is_rc:
            right_click_candidate_frames += 1
        else:
            right_click_candidate_frames = 0
            right_click_armed = True

        if raw_is_db:
            double_click_candidate_frames += 1
        else:
            double_click_candidate_frames = 0
            double_click_armed = True

        is_rc = right_click_candidate_frames >= click_confirmation_frames
        is_db = double_click_candidate_frames >= click_confirmation_frames

        if is_scrolling:
            action = "scroll"
            if scroll_amount != 0 and not should_suppress_mouse_actions():
                perform_mouse_action("scroll", scroll_amount)
        elif is_db:
            action = "double_click"
        elif is_rc:
            action = "right_click"
        elif is_lc:
            last_left_click_detected_time = current_time
            if not is_dragging:
                is_dragging = True
                left_click_candidate_frames = 0
                left_click_start_time = current_time
                mouse_down_triggered = False
                action = "left_click_intent"
            else:
                if current_time - left_click_start_time > drag_hold_threshold and not mouse_down_triggered:
                    if not should_suppress_mouse_actions():
                        perform_mouse_action("mouseDown")
                    mouse_down_triggered = True
                action = "drag" if mouse_down_triggered else "holding_click"
        else:
            if is_dragging:
                if current_time - last_left_click_detected_time > 0.2:
                    is_dragging = False
                    if mouse_down_triggered:
                        action = "release_drag"
                        if not should_suppress_mouse_actions():
                            perform_mouse_action("mouseUp")
                        mouse_down_triggered = False
                    else:
                        action = "left_click"
                        if not should_suppress_mouse_actions():
                            perform_mouse_action("click")
                    last_click_time = current_time
                    left_click_candidate_frames = 0
                else:
                    action = "drag" if mouse_down_triggered else "holding_click"

        if not is_dragging and current_time - last_click_time > click_cooldown:
            if action == "right_click" and right_click_armed:
                if not should_suppress_mouse_actions():
                    perform_mouse_action("click", button='right')
                right_click_armed = False
                last_click_time = current_time
            elif action == "double_click" and double_click_armed:
                if not should_suppress_mouse_actions():
                    perform_mouse_action("doubleClick")
                double_click_armed = False
                last_click_time = current_time

        current_state["action"] = action
        
        cv2.putText(frame, f"Action: {action}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if cursor_movement.is_frozen(landmark_list):
            cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
            
    else:
        left_click_candidate_frames = 0
        right_click_candidate_frames = 0
        double_click_candidate_frames = 0
        right_click_armed = True
        double_click_armed = True
        left_click.reset_state()
        right_click.reset_state()
        double_click.reset_state()
        if is_dragging:
            is_dragging = False
            if mouse_down_triggered:
                if not should_suppress_mouse_actions():
                    perform_mouse_action("mouseUp")
                mouse_down_triggered = False

def _tracking_loop(headless):
    global is_tracking
    import cv2
    import mediapipe as mp
    mpHands = mp.solutions.hands
    draw = mp.solutions.drawing_utils
    system_name = platform.system()
    if system_name == 'Linux':
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not cap.isOpened():
            print("Aviso: Falha ao usar V4L2. Tentando backend padrão do OpenCV...")
            cap = cv2.VideoCapture(0)
    elif system_name == 'Darwin':
        avfoundation = getattr(cv2, "CAP_AVFOUNDATION", 0)
        cap = cv2.VideoCapture(0, avfoundation)
        if not cap.isOpened():
            print("Aviso: Falha ao usar AVFoundation. Tentando backend padrao do OpenCV...")
            cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Erro: Nao foi possivel abrir a camera.")
        is_tracking = False
        camera_ready_event.set()
        return

    hands = mpHands.Hands(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.85,
        min_tracking_confidence=0.85,
        max_num_hands=1
    )
    
    camera_ready_event.set()

    try:
        while cap.isOpened() and is_tracking:
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            processed = hands.process(rgb_frame)

            landmark_list = []
            if processed.multi_hand_landmarks:
                for lm in processed.multi_hand_landmarks[0].landmark:
                    landmark_list.append((lm.x, lm.y))
                draw.draw_landmarks(frame, processed.multi_hand_landmarks[0], mpHands.HAND_CONNECTIONS)

            detect_gesture(frame, landmark_list, processed)

            global latest_frame
            small_frame = cv2.resize(frame, (320, 240))
            ret_enc, buffer = cv2.imencode('.jpg', small_frame)
            if ret_enc:
                latest_frame = buffer.tobytes()

            if not headless:
                cv2.imshow('WGI Engine', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'): break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        is_tracking = False

class WGIServer(BaseHTTPRequestHandler):
    def do_POST(self):
        message = "Ação não reconhecida."
        if self.path == '/start_tracking': 
            started = start_tracking(headless=True)
            message = "Camera active and tracking!" if started else "Could not start camera."
        elif self.path == '/stop_tracking': 
            stop_tracking()
            message = "Successfully stopped camera."
        elif self.path == '/config':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                new_config = json.loads(post_data.decode('utf-8'))
                calibration_manager.config.update(new_config)
                calibration_manager.config = calibration_manager.sanitize_config(calibration_manager.config)
                calibration_manager.save_config(calibration_manager.config)
                message = "Configuração atualizada com sucesso!"
        elif self.path == '/start_calibration':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                global calibration_gesture, calibration_idx_history, calibration_mid_history, calibration_thumb_history
                gesture = data.get("gesture")
                if not is_tracking:
                    cancel_calibration()
                    current_state["action"] = "calibration_failed"
                    current_state["calibration"] = {"status": "failed", "gesture": gesture}
                    message = "Start camera before calibration."
                elif gesture not in calibration_manager.DEFAULT_CONFIG:
                    cancel_calibration()
                    current_state["action"] = "calibration_failed"
                    current_state["calibration"] = {"status": "failed", "gesture": gesture}
                    message = "Calibration gesture not recognized."
                else:
                    reset_interaction_state()
                    calibration_gesture = gesture
                    calibration_idx_history = []
                    calibration_mid_history = []
                    calibration_thumb_history = []
                    current_state["calibration"] = {"status": "recording", "gesture": calibration_gesture}
                    message = f"Calibrating {calibration_gesture}..."
        elif self.path == '/set_wizard_mode':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                global wizard_active
                requested_active = data.get("active", False)
                if not requested_active:
                    cancel_calibration()
                reset_interaction_state()
                wizard_active = requested_active
                message = f"Wizard mode set to {wizard_active}"
        self.send_response(200); self.send_header('Access-Control-Allow-Origin', '*'); self.end_headers()
        self.wfile.write(json.dumps({"message": message}).encode())

    def do_GET(self):
        if self.path == '/state':
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Access-Control-Allow-Origin', '*'); self.end_headers()
            state_data = current_state.copy()
            state_data["is_tracking"] = is_tracking
            self.wfile.write(json.dumps(state_data).encode())
            if current_state["action"] not in ["move", "drag", "holding_click"]: current_state["action"] = "move"
        elif self.path == '/config':
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Access-Control-Allow-Origin', '*'); self.end_headers()
            self.wfile.write(json.dumps(calibration_manager.config).encode())
        elif self.path.startswith('/video_feed'):
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                while is_tracking:
                    if latest_frame is not None:
                        self.wfile.write(b'--frame\r\n')
                        self.send_header('Content-Type', 'image/jpeg')
                        self.send_header('Content-Length', str(len(latest_frame)))
                        self.end_headers()
                        self.wfile.write(latest_frame)
                        self.wfile.write(b'\r\n')
                    time.sleep(0.06)
            except Exception:
                pass
        elif self.path == '/':
            self.send_response(200); self.send_header('Content-Type', 'text/plain'); self.send_header('Access-Control-Allow-Origin', '*'); self.end_headers()
            self.wfile.write(b"WGI Server is running! Available endpoints: GET /state, POST /start_tracking, POST /stop_tracking")
        else:
            self.send_error(404, "Endpoint not found")

def start_tracking(headless):
    global is_tracking
    if not is_tracking:
        cancel_calibration()
        reset_interaction_state()
        camera_ready_event.clear()
        is_tracking = True
        threading.Thread(target=_tracking_loop, args=(headless,), daemon=True).start()
        camera_ready_event.wait(timeout=10.0)
    return is_tracking

def stop_tracking():
    global is_tracking
    cancel_calibration()
    reset_interaction_state()
    is_tracking = False
    current_state["action"] = "move"

def find_free_port(start_port=8765, max_port=8800):
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Nenhuma porta livre encontrada entre {start_port} e {max_port}.")

if __name__ == '__main__':
    port = find_free_port()
    server = ThreadingHTTPServer(('127.0.0.1', port), WGIServer)
    print(f"WGI Server Running on {port}...")
    server.serve_forever()
