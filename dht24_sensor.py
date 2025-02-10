from flask import Flask, render_template
from flask_socketio import SocketIO
import pymysql
import Adafruit_DHT
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # WebSocket 설정

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

# 전역 변수 (데이터 입력 ON/OFF 상태)
data_insert_enabled = False

# 📌 HTML 페이지 렌더링
@app.route("/")
def index():
    return render_template("index4.html")

# 📌 데이터 입력 ON/OFF 토글 API
@app.route("/toggle", methods=["POST"])
def toggle_data_insert():
    global data_insert_enabled
    data_insert_enabled = not data_insert_enabled
    return {"status": "ON" if data_insert_enabled else "OFF"}

# 📌 센서 데이터 읽기 및 DB 저장 (1초마다 실행)
def read_sensor_data():
    global data_insert_enabled
    while True:
        if data_insert_enabled:
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            if humidity is not None and temperature is not None:
                # DB에 데이터 저장
                query = "INSERT INTO sensor_data (temperature, humidity) VALUES (%s, %s)"
                cursor.execute(query, (temperature, humidity))
                db.commit()

                # WebSocket을 통해 클라이언트에 데이터 전송
                socketio.emit("update_data", {
                    "temperature": temperature,
                    "humidity": humidity
                })
        time.sleep(1)  # 1초마다 실행

# 백그라운드에서 센서 데이터 읽기 시작
sensor_thread = threading.Thread(target=read_sensor_data, daemon=True)
sensor_thread.start()

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=7000)