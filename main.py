from flask import Flask, Response, jsonify, render_template
import cv2
from pymavlink import mavutil
from functions import load_yolo_model, detect_objects, draw_labels, handle_distance_and_mode
from log import log_distance_data
import time

app = Flask(__name__)

log_data = []

connection_string = 'tcp:127.0.0.1:5762'
baud_rate = 57600
print(f"Подключение к дрону по порту: {connection_string} на скорости {baud_rate}")
master = mavutil.mavlink_connection(connection_string, baud=baud_rate)
master.wait_heartbeat()
print(f"Получен heartbeat от системы (system {master.target_system} component {master.target_component})")

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Не удалось открыть видеопоток")
    exit()

net, output_layers, classes = load_yolo_model()

def generate_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        boxes, confidences, class_ids, indexes = detect_objects(frame, net, output_layers, classes)
        frame = draw_labels(frame, boxes, class_ids, indexes, classes)

        msg = master.recv_match(type='DISTANCE_SENSOR', blocking=False)
        if msg:
            distance = msg.current_distance / 100.0 
            log_distance_data(distance)
            log_data.append(f"Расстояние до объекта: {distance} м")
            handle_distance_and_mode(master, distance)
        else:
            log_distance_data()
            log_data.append("Данные с дальномера не получены.")
            print("Данные с дальномера не получены.")

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/logs')
def get_logs():
    return jsonify(log_data[-20:], ensure_ascii=False)

@app.route('/logs_stream')
def logs_stream():
    def generate_logs():
        last_log_size = len(log_data)
        while True:
            if len(log_data) > last_log_size:
                new_logs = log_data[last_log_size:]
                for log in new_logs:
                    yield f"data: {log}\n\n"
                last_log_size = len(log_data)
            time.sleep(1) 

    return Response(generate_logs(), mimetype='text/event-stream')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    
    cap.release()
    master.close()
