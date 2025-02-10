from flask import Flask, render_template
from flask_socketio import SocketIO
import Adafruit_DHT
import time
import threading
import pymysql

# Flask 및 SocketIO 설정
app = Flask(__name__)
socketio = SocketIO(app)

# MySQL 연결 정보
db_config = {
    "host": "localhost",
    "user": "test",
    "password": "test",
    "database": "iotsensor"
}

# 센서 설정 (DHT22, GPIO 4번 핀)
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

# 온습도 데이터 수집 및 전송 함수
def read_sensor_data():
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        if humidity is not None and temperature is not None:
            data = {"temperature": round(temperature, 2), "humidity": round(humidity, 2)}

            # MySQL에 데이터 저장
            try:
                conn = pymysql.connect(**db_config)
                cursor = conn.cursor()
                query = "INSERT INTO sensor_data (temperature, humidity) VALUES (%s, %s)"
                cursor.execute(query,(temperature, humidity))
                conn.commit()
                cursor.close()
                conn.close()
                print("✅ 데이터 저장 성공:", temperature, humidity)
            except Exception as e:
                print("DB Error:", e)

            # 클라이언트로 데이터 전송
            socketio.emit("update_sensor", data)

        time.sleep(1)  # 1초마다 데이터 갱신

# 센서 데이터 수집 스레드 실행
threading.Thread(target=read_sensor_data, daemon=True).start()

# HTML 페이지 라우팅
@app.route("/")
def index():
    return render_template("index1.html")

# Flask 실행
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=7000, allow_unsafe_werkzeug=True)
