import os
import subprocess
import threading
from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

def run_bot():
    subprocess.Popen(["python", "bot.py"])

if __name__ == '__main__':
    # Запускаем бота в фоне
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Запускаем сайт
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
