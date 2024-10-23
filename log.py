import time
import os

def log_distance_data(distance=None):
    log_file = "log.txt"

    if not os.path.exists(log_file):
        with open(log_file, "w") as file:
            file.write("Лог данных с дальномера\n")
        
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    with open(log_file, "a") as file:
        if distance is not None:
            file.write(f"{current_time}: Расстояние до объекта = {distance} м\n")
        else:
            file.write(f"{current_time}: Данные с дальномера не получены\n")
            
            
