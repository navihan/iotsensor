from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # CORS 허용

@app.route("/")
def index():
    return render_template("index5.html")

@socketio.on("message")
def handle_message(msg):
    print(f"📥 클라이언트로부터 메시지 수신: {msg}")
    socketio.send(f"서버 응답: {msg}")  # 클라이언트로 메시지 전송

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=7000, debug=True)