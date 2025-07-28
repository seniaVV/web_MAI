import socket
import json
import datetime
import sys

student_name = "Korkina Ksenia Vladimirovna"
student_group = "M3O-107BV-24"

def write_to_log(action, message=None):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("client_log.txt", "a", encoding='utf-8') as log_file:
        if action == "connect":
            log_file.write(f"[{current_time}] Подключение к серверу {server_address}:{server_port}\n")
        elif action == "send":
            log_file.write(f"[{current_time}] Отправлено сообщение: {message}\n")
        elif action == "receive":
            log_file.write(f"[{current_time}] Получено сообщение: {message}\n")
        elif action == "disconnect":
            log_file.write(f"[{current_time}] Отключение от сервера\n")

sys.stdout.reconfigure(encoding='utf-8')

try:
    with open("client_config.json", "r", encoding='utf-8') as config_file:
        config = json.load(config_file)
        server_address = config["server_address"]
        server_port = config["server_port"]

except Exception as e:
    print(f"Ошибка чтения конфигурационного файла: {e}")
    exit()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.settimeout(8)

try:
    client_socket.connect((server_address, server_port))
    write_to_log("connect")
    
    message = f"{student_name} {student_group}" 
    client_socket.send(message.encode())
    write_to_log("send", message)
    
    response = client_socket.recv(1024).decode('utf-8')
    if not response:
        write_to_log("disconnect", "Сервер закрыл соединение")
    else:
        write_to_log("receive", response)
    
finally:
    client_socket.close()
    write_to_log("disconnect")
    print("Клиент завершил работу")