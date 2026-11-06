import os
from flask import Flask, send_from_directory

# Создаем Flask приложение для раздачи HTML файла
app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    # Render передает порт через переменную окружения
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
    import subprocess
import threading

def run_bot():
    subprocess.Popen(["python", "bot.py"])

# Запускаем бота в фоне при старте сайта
threading.Thread(target=run_bot, daemon=True).start()
