from flask import Flask, request, jsonify, Response #flask и его компоненты
import os #для работы с файлами
import json
import jwt #для работы с JWT токенами
import datetime
from functools import wraps #для создания декораторов

#flask-приложение
app = Flask(__name__)

# Конфигурация
app.config["SECRET_KEY"] = "your_secret_key_here"
app.config["JWT_ALGORITHM"] = "HS256"

# Файлы данных
TASKS_FILE = 'tasks.json' #для хранения задач
USERS_FILE = 'users.json' #для хранения пользователей

#функция чтения данных из JSON-файла
def read_json(file_path):
    if not os.path.exists(file_path): #если файл не существует
        return []                     #вернуть пустой список
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)       #иначе загрузить данные
    except (json.JSONDecodeError, FileNotFoundError):
        return []

#Запись данных в JSON-файл
def write_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

#Обновление задач по id
def update_task_by_id(task_id, update_data):
    tasks = read_json(TASKS_FILE)           #считать все задачи
    for task in tasks:      
        if task["id"] == task_id:           
            task.update(update_data)        #обновить данные задачи
            write_json(tasks, TASKS_FILE)   #сохранить изменения
            return True
    return False

#Генерация JWT-токена
def generate_token(user_id):
    payload = {
        "sub": str(user_id), #id пользователя
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30) #срок действия
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"])

#Декоратор для проверки токена
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        data = request.get_json()   #получить данные из запроса
        token = data.get('token')   #получить токен
        
        if not token:               #если токена нет
            return jsonify({"error": "Token is missing"}), 401
        
        try:                        #пытаемся декодировать
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=[app.config["JWT_ALGORITHM"]])
            user_id = data["sub"]   #получаем id пользователя
        except:
            return jsonify({"error": "Invalid token"}), 401
        #если все ок, вызвать функцию с user_id
        return f(user_id, *args, **kwargs)
    return decorated

#регистрация нового пользователя
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    users = read_json(USERS_FILE)
    #проверка наличия обязательных полей
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password are required"}), 400
    #проверить, что пользователь новый
    if any(user['username'] == data['username'] for user in users):
        return jsonify({"error": "Username already exists"}), 400
    #создать нового пользователя
    new_user = {
        "id": len(users) + 1,
        "username": data['username'],
        "password": data['password']
    }
    
    users.append(new_user)  #добавление
    write_json(users, USERS_FILE) #сохранение
    
    return jsonify({"message": "User registered successfully"}), 201

#Аутентификация пользователя
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    users = read_json(USERS_FILE)
    #проверка обязательных полей
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password are required"}), 400
    #пользователь с совпадающим логином и паролем
    user = next((u for u in users if u['username'] == data['username'] and u['password'] == data['password']), None)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    #создание токена для данного пользователя
    token = generate_token(user['id'])
    return jsonify({"token": token})

#Получение всех задач
@app.route('/tasks', methods=['GET'])
@token_required #теперь требуется аутентификация
def get_all_tasks(user_id):
    tasks = read_json(TASKS_FILE)
    return jsonify(tasks) 

#получение задачи по её id
@app.route('/tasks/<int:task_id>', methods=['GET'])
@token_required
def get_task(user_id, task_id):
    tasks = read_json(TASKS_FILE)
    #ищем задачу по id и проверяем, что она принадлежит пользователю
    task = next((t for t in tasks if t['id'] == task_id and t.get('user_id') == user_id), None)
    
    if task:
        return Response( #формируем ответ
            json.dumps(task, ensure_ascii=False),
            mimetype='application/json'
        )
    return jsonify({"error": "Task not found"}), 404 #ошибка иначе

#создание новой задачи
@app.route('/tasks', methods=['POST'])
@token_required
def create_task(user_id):
    tasks = read_json(TASKS_FILE)
    #поле title для создания обязательно
    if not request.json or 'title' not in request.json:
        return jsonify({"error": "Title is required"}), 400
    #для создания id
    max_id = max(task['id'] for task in tasks) if tasks else 0
    #создание новой задачи
    new_task = {
        "id": max_id + 1,
        "user_id": user_id,
        "title": request.json['title'],
        "done": request.json.get('done', False)
    }
    
    tasks.append(new_task)
    write_json(tasks, TASKS_FILE)
    
    return jsonify(new_task), 201

#обновление задачи
@app.route('/tasks/<int:task_id>', methods=['PUT'])
@token_required
def update_task(user_id, task_id):
    tasks = read_json(TASKS_FILE)
    #найти задачу по id и проверить, что она принадлежит пользователю
    task = next((t for t in tasks if t['id'] == task_id and t.get('user_id') == user_id), None)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    if not request.json:
        return jsonify({"error": "No data provided"}), 400
    #обновить поля задачи
    task['title'] = request.json.get('title', task['title'])
    task['done'] = request.json.get('done', task['done'])
    
    write_json(tasks, TASKS_FILE)
    return jsonify(task)

#удаление задачи
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(user_id, task_id):
    tasks = read_json(TASKS_FILE)
    task = next((t for t in tasks if t['id'] == task_id and t.get('user_id') == user_id), None)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    tasks.remove(task)
    write_json(tasks, TASKS_FILE)
    return jsonify({"result": "Task deleted"})

# Фильтрация задач по выполнению
@app.route("/tasks/filtered", methods=["GET"])
@token_required
def get_filtered_task(user_id):
    tasks = read_json(TASKS_FILE)
    data = []

    for task in tasks:
        if task["done"]:
            data.append(task)
    return jsonify(data)

# Сортировка задач по title
@app.route("/tasks/sorted", methods=["GET"])
@token_required
def get_sorted_task(user_id):
    tasks = read_json(TASKS_FILE)
    #сортировка
    sorted_tasks = sorted(tasks, key=lambda x: x["title"].lower())
    
    return jsonify(sorted_tasks)

# Метод для экспорта данных в формат JSON
@app.route("/tasks/export/json", methods=["GET"])
@token_required
def export_json(user_id):
    tasks = read_json(TASKS_FILE)
    return jsonify(tasks)

# Метод для экспорта данных в формат CSV
@app.route("/tasks/export/csv", methods=["GET"])
@token_required
def export_csv(user_id):
    tasks = read_json(TASKS_FILE)
    csv_data = ",".join(tasks[0].keys()) + "\n"
    for item in tasks:
        csv_data += ",".join(map(str, item.values())) + "\n"
    return csv_data

def update_task_by_id(task_id, new_data):
    tasks = read_json(TASKS_FILE)
    for task in tasks:
        if task["id"] == task_id:
            task.update(new_data)
            break
    write_json(tasks, TASKS_FILE)

# комментирование
@app.route("/tasks/<int:task_id>/comment", methods=["PUT"])
@token_required
def add_comment(user_id, task_id):
    tasks = read_json(TASKS_FILE) #считать задачу
    #найти задачу
    task = next((t for t in tasks if t["id"] == task_id), None)
    
    if not task:
        return {"error": "Task not found"}, 404
    #получить текст комментария
    comment_text = request.json.get("text")
    if not comment_text:
        return {"error": "Comment text is required"}, 400
    #если поля комментария нет, создать его
    if "comments" not in task:
        task["comments"] = []
    #добавить комментарий
    task["comments"].append({
        "text": comment_text
    })
    
    write_json(tasks, TASKS_FILE)
    
    return {"message": "Comment added successfully"}, 200  
#запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
