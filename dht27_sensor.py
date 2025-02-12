from flask import Flask, render_template
from flask_socketio import SocketIO
import time
import threading
import random
import pymysql
import Adafruit_DHT
import json
import eventlet
from flask_cors import CORS

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")  # CORS 허용


# MySQL 연결 설정
db = pymysql.connect(
    host="localhost",
    user="test",
    password="test",
    database="iotsensor"
)
cursor = db.cursor()

# 📌 DHT 센서 설정
DHT_SENSOR = Adafruit_DHT.DHT22  # DHT11을 사용하면 DHT11으로 변경
DHT_PIN = 4  # GPIO 4번 핀에 연결됨

@app.route("/")
def index():
    return render_template("index7.html")

def send_data():
    while True:
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            if humidity is not None and temperature is not None:
                # DB에 데이터 저장
                query = "INSERT INTO sensor_data (temperature, humidity) VALUES (%s, %s)"
                cursor.execute(query, (temperature, humidity))
                db.commit()
            data = {"temperature": round(temperature, 1),"humidity": round(humidity, 1)}
            socketio.emit("update_data",data)  # 클라이언트로 메시지 전송   
            print(f"📡 데이터 전송: {data}")

            time.sleep(4)    

# 백그라운드에서 센서 데이터 전송 스레드 실행
thread = threading.Thread(target=send_data)
thread.daemon = True
thread.start()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=7000, debug=True)