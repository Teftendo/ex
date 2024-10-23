import cv2
import numpy as np
from pymavlink import mavutil

def load_yolo_model():
    net = cv2.dnn.readNet('yolov4-tiny.weights', 'yolov4-tiny.cfg')
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    
    return net, output_layers, classes

def detect_objects(frame, net, output_layers, classes):
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (320, 320), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    
    outs = net.forward(output_layers)
    
    class_ids = []
    confidences = []
    boxes = []
    height, width, channels = frame.shape

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)
    
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    
    return boxes, confidences, class_ids, indexes

def draw_labels(frame, boxes, class_ids, indexes, classes):
    font = cv2.FONT_HERSHEY_PLAIN
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            color = (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, label, (x, y - 5), font, 1, color, 1)
    return frame

def handle_distance_and_mode(master, distance):
    if distance <= 10.0:
        print("Объект слишком близко! Переход в режим 'BRAKE'.")
        if set_mode(master, 'BRAKE'):
            print("Дрон переведен в режим BRAKE.")
        else:
            print("Не удалось установить режим BRAKE, пробуем LOITER.")
            if set_mode(master, 'LOITER'):
                print("Дрон переведен в режим LOITER.")
            else:
                print("Не удалось установить режим LOITER.")
    else:
        print(f"Расстояние до объекта: {distance} м")

def set_mode(master, mode):
    if mode not in master.mode_mapping():
        print(f'Режим {mode} не поддерживается')
        return False

    mode_id = master.mode_mapping()[mode]
    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id)
    return True
