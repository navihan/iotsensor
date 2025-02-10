import time
import Adafruit_DHT
import pymysql

# DHT22 센서 설정
SENSOR = Adafruit_DHT.DHT22
PIN = 4  # GPIO 핀 번호 (센서를 연결한 핀 번호에 맞게 수정)

# MariaDB 연결 설정
DB_CONFIG = {
    "host": 'localhost',
    "user": 'test',
    "password": 'test',
    "database": 'iotsensor'
}

def insert_data(temperature, humidity):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = "INSERT INTO sensor_data (temperature, humidity, timestamp) VALUES (%s, %s, NOW())"
        cursor.execute(query, (temperature, humidity))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Data Inserted: Temp={temperature:.2f}°C, Humidity={humidity:.2f}%")
    except IOExcept:
        print(f"Error")

def main():
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(SENSOR, PIN)
        if humidity is not None and temperature is not None:
            insert_data(temperature, humidity)
        else:
            print("Failed to retrieve data from sensor")
        time.sleep(1)  # 1초 간격으로 데이터 읽기

if __name__ == "__main__":
    main()