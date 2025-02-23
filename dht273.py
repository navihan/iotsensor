import eventlet
# Eventlet 서버 실행을 위한 코드
eventlet.monkey_patch()

from flask import Flask, Response, request, jsonify, render_template
from flask_socketio import SocketIO
import time
import threading
import random
import pandas as pd
from sqlalchemy import create_engine
from io import BytesIO
from datetime import datetime
import pymysql
import Adafruit_DHT
import json
from flask_cors import CORS

app = Flask(__name__)
#socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")  # CORS 허용
socketio = SocketIO(app, async_mode="eventlet")  

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'localhost',
    'user': 'test',
    'password': 'test',
    'database': 'iotsensor',
    'cursorclass': pymysql.cursors.DictCursor
}

# SQLAlchemy 엔진 생성
DB_URI = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
engine = create_engine(DB_URI)

# 📌 DHT 센서 설정
DHT_SENSOR = Adafruit_DHT.DHT22  # DHT11을 사용하면 DHT11으로 변경
DHT_PIN = 4  # GPIO 4번 핀에 연결됨

# 전역 변수 (데이터 입력 ON/OFF 상태)
data_insert_enabled = False

# 센서 상태를 저장할 변수
sensor_state = "off"  # 초기 상태는 off

@app.route("/")
def index():
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('index73.html', today=today)

# 🔥 센서 상태를 변경하는 함수
def update_sensor_state(state):
    global sensor_state
    sensor_state = state
    print(f"센서 상태 변경: {state}")

def insert_sensor_data(temperature, humidity, co2level, o2level):
    """ 센서 데이터를 데이터베이스에 삽입 """
    connection = pymysql.connect(**DB_CONFIG)
    with connection.cursor() as cursor:
        query = """
            INSERT INTO sensor_data (timestamp, temperature, humidity,co2level, o2level) 
            VALUES (NOW(), %s, %s, %s, %s)
        """
        cursor.execute(query, (temperature, humidity,co2level, o2level))
        connection.commit()
        data = {"temperature": round(temperature, 1),"humidity": round(humidity, 1),"co2level": round(co2level, 1),"o2level": round(o2level, 1),"state":"on"}
        socketio.emit("update_data",data)  # 클라이언트로 메시지 전송   
        print(f"📡 데이터 전송: {data}")
    connection.close()

def collect_sensor_data():
    """ 1초 간격으로 센서 데이터를 수집하여 DB에 저장하는 함수 """
    while True:
        if sensor_state == "on":  # 센서 상태가 "on"일 때만 데이터 전송
            try:
                #temperature = round(random.uniform(20.0, 30.0), 2)  # 랜덤 온도 생성
                #humidity = round(random.uniform(40.0, 60.0), 2)  # 랜덤 습도 생성
                co2level = random.randint(400, 1000)  # 400ppm ~ 1000ppm
                o2level = random.uniform(20.5, 21.5)  # 20.5% ~ 21.5% O2
                humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
                if humidity is not None and temperature is not None:
                    insert_sensor_data(temperature, humidity, co2level, o2level)
                    print(f"Inserted: Temp={temperature}, Humidity={humidity}, co2level={co2level},o2level={o2level}")
                else:
                    print("temperature,humidity data error")            
            except Exception as e:
                    print(f"Error inserting sensor data: {e}")
        time.sleep(3)  # 1초마다 실행


# 클라이언트가 접속하면 현재 상태 전송
@socketio.on("connect")
def handle_connect():
    print("📡 클라이언트 연결됨")
    # 연결된 클라이언트에게 현재 상태 전달
    socketio.emit("sensor_state", {"state": sensor_state})

# 센서 상태 ON/OFF 전환
@socketio.on("toggle_sensor")
def toggle_sensor():
    global sensor_state
    new_state = "off" if sensor_state == "on" else "on"
    update_sensor_state(new_state)
    print(f"🔄 센서 상태 변경: {new_state}")
    socketio.emit("sensor_state", {"state": new_state})  # 모든 클라이언트에 상태 업데이트  


# 백그라운드에서 센서 데이터 전송 스레드 실행
#thread = threading.Thread(target=collect_sensor_data)
#thread.daemon = True
#thread.start()


@app.route('/download_excel')
def download_excel():

    # 오늘 날짜 기본값 설정
    today = datetime.now().strftime('%Y-%m-%d')

    # 시작일 (YYYY-MM-DD 형식 입력 시 00:00:00으로 설정)
    start_date = request.args.get('start_date', today)
    start_datetime = f"{start_date} 00:00:00"

    # 종료일 (YYYY-MM-DD 형식 입력 시 23:59:59으로 설정)
    end_date = request.args.get('end_date', today)
    end_datetime = f"{end_date} 23:59:59"
    
    if not start_date or not end_date:
        return "Missing date parameters", 400
    
    connection = pymysql.connect(**DB_CONFIG)
    query = f"""
        SELECT timestamp, temperature, humidity, co2level, o2level 
        FROM sensor_data 
        WHERE timestamp BETWEEN '{start_datetime}' AND '{end_datetime}'
        ORDER BY timestamp DESC
    """
    df = pd.read_sql(query, engine)
    connection.close()
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sensor Data')
    
    output.seek(0)
    download_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"sensor_data_{download_date}.xlsx"
    
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
# 최신 1분 데이터를 DB에서 가져오는 함수
def get_sensor_data():
    try:
        with app.app_context():
            connection = pymysql.connect(**DB_CONFIG)
            cursor = connection.cursor()
            query = '''   
                SELECT 
                DATE_FORMAT(timestamp, '%Y-%m-%d %H:%i') as time_group,
                AVG(temperature) as temperature,
                AVG(humidity) as humidity,
                AVG(co2level) as co2level,
                AVG(o2level) as o2level
                FROM sensor_data
                WHERE timestamp >= NOW() - INTERVAL 1 HOUR
                GROUP BY time_group
                ORDER BY time_group ASC;
                '''
            cursor.execute(query)

            rows = cursor.fetchall()
            cursor.close()
            connection.close()

        # 결과를 JSON 형태로 변환
        result = [{'time_group': row['time_group'], 'temperature':row['temperature'], 'humidity':row['humidity'], 'co2level':row['co2level'], 'o2level':row['o2level']} for row in rows]
        print(rows)
        print(result)
        return result

    except Exception as e:
        return str(e)

# 실시간 데이터 제공 API (Ajax 요청 처리)
#@app.route('/get_data', methods=['GET'])
#def get_data():
    eventlet.sleep(5)  # 비동기 대기 (실제 데이터 처리를 비동기적으로 하기 위한 시간 지연)
    data = get_sensor_data()  # 데이터를 가져옴
    print(data)
    return jsonify(data)

@socketio.on('request_data')
def send_data():
    """웹소켓을 통해 1초마다 센서 데이터를 전송"""
    while True:
        data = get_sensor_data()
        socketio.emit('sensor_data', data)
        time.sleep(3)  # 1초 간격 전송


if __name__ == "__main__":
    eventlet.spawn(collect_sensor_data)
    socketio.run(app, host="0.0.0.0", port=7000, debug=True,allow_unsafe_werkzeug=True)