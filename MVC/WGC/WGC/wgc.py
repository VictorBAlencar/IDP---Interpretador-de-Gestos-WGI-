import cv2
import mediapipe as mp
import time
import threading
import calculo_distancia as util
import cursor_movement
import left_click
import right_click
import double_click
import screenshot
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

mpHands = mp.solutions.hands
hands = mpHands.Hands(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.85,
    min_tracking_confidence=0.85,
    max_num_hands=1
)

last_click_time = 0
click_cooldown = 0.5 
is_dragging = False
drag_start_time = 0
last_left_click_detected_time = 0
is_tracking = False

# Estado global para o navegador puxar (polling)
current_state = {"x": 0.5, "y": 0.5, "action": "move"}

def detect_gesture(frame, landmark_list, processed):
    global last_click_time, is_dragging, drag_start_time, last_left_click_detected_time
    global current_state

    current_time = time.time()
    action = "move"

    if len(landmark_list) >= 21:
        hand_landmarks = processed.multi_hand_landmarks[0]
        palm_center = cursor_movement.get_palm_center(hand_landmarks)
        thumb_index_dist = util.get_distance([landmark_list[4], landmark_list[5]])

        x, y = cursor_movement.get_normalized_position(palm_center)
        if x is not None and y is not None:
            current_state["x"] = x
            current_state["y"] = y

        left_clicking = left_click.is_left_click(landmark_list, thumb_index_dist, is_dragging)
        if left_clicking:
            last_left_click_detected_time = current_time
            if not is_dragging:
                is_dragging = True
                drag_start_time = current_time
                action = "left_click"
            else:
                action = "drag"
        else:
            if is_dragging:
                if current_time - last_left_click_detected_time > 0.2:
                    is_dragging = False
                    action = "release_drag"
                    last_click_time = current_time
                else:
                    action = "drag"

            right_clicking = right_click.is_right_click(landmark_list, thumb_index_dist)
            double_clicking = double_click.is_double_click(landmark_list, thumb_index_dist)
            screenshotting = screenshot.is_screenshot(landmark_list)

            if not is_dragging and current_time - last_click_time > click_cooldown:
                if right_clicking:
                    action = "right_click"
                    last_click_time = current_time
                elif double_clicking:
                    action = "double_click"
                    last_click_time = current_time
                elif screenshotting:
                    action = "screenshot"
                    last_click_time = current_time

        if action != "move":
            current_state["action"] = action
            
        cv2.putText(frame, action, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    else:
        if is_dragging and current_time - last_left_click_detected_time > 0.2:
            is_dragging = False
            current_state["action"] = "release_drag"
            last_click_time = current_time

def _tracking_loop(headless):
    global is_tracking
    draw = mp.solutions.drawing_utils
    # cv2.CAP_DSHOW acelera a inicialização da câmera no Windows pulando a busca de backends
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    try:
        while cap.isOpened() and is_tracking:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed = hands.process(frameRGB)

            landmark_list = []
            if processed.multi_hand_landmarks:
                hand_landmarks = processed.multi_hand_landmarks[0] 
                draw.draw_landmarks(frame, hand_landmarks, mpHands.HAND_CONNECTIONS)
                for lm in hand_landmarks.landmark:
                    landmark_list.append((lm.x, lm.y))

            detect_gesture(frame, landmark_list, processed)

            if not headless:
                cv2.imshow('Frame', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        is_tracking = False

def start_tracking(headless=True):
    global is_tracking
    if not is_tracking:
        is_tracking = True
        threading.Thread(target=_tracking_loop, args=(headless,), daemon=True).start()

def stop_tracking():
    global is_tracking
    is_tracking = False

class WGCServer(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/start_tracking':
            start_tracking(headless=True)
            msg = "Câmera iniciada via Servidor Local!"
        elif self.path == '/stop_tracking':
            stop_tracking()
            msg = "Câmera parada."
        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"message": msg}).encode('utf-8'))

    def do_GET(self):
        global current_state
        if self.path == '/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(current_state).encode('utf-8'))
            
            # Após o navegador ler que algo além de 'move' aconteceu, reseta, para não clicar duplo ou arrastar por engano
            if current_state["action"] not in ["move", "drag"]:
                current_state["action"] = "move"
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Oculta os logs de requisição no console

if __name__ == '__main__':
    porta = 5000
    server = HTTPServer(('127.0.0.1', porta), WGCServer)
    print(f"Servidor WGC rodando na porta {porta}...")
    print("Aguardando comandos da extensão... Pressione Ctrl+C para fechar.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        stop_tracking()
        server.server_close()
        print("Servidor encerrado.")