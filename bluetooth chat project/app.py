import os
import socket as py_socket
import uuid
import random
import logging
from flask import Flask, render_template, session, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

from database.database import DatabaseManager
from bluetooth.scanner import BluetoothScanner
from bluetooth.connection import BluetoothConnectionManager
from bluetooth.messaging import CryptographicMessaging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BlueGhost.App")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'blueghost-cyberpunk-key-' + str(uuid.uuid4())
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max file size

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize DB, Scanner, Connection Manager, and Cryptography
db = DatabaseManager(db_path='blueghost.db', uploads_dir=app.config['UPLOAD_FOLDER'])
scanner = BluetoothScanner(db_manager=db)
crypto_engine = CryptographicMessaging()

def handle_ble_status_change(status, device_info):
    """Callback triggered on BLE connection status update."""
    socketio.emit('connection_status', {
        'status': status,
        'device': device_info
    })

connection_mgr = BluetoothConnectionManager(db_manager=db, status_callback=handle_ble_status_change)

GHOST_PREFIXES = ["Ghost", "Shadow", "Penguin", "Fox", "Pixel", "Vortex", "Phantom", "Spectre", "Cipher", "Echo", "Nebula", "Cyber"]
GHOST_EMOJIS = ["👻", "🌑", "🐧", "🦊", "👾", "🌀", "💀", "👁️", "⚡", "🛰️", "🤖", "🎭"]

def generate_random_identity():
    prefix = random.choice(GHOST_PREFIXES)
    emoji = random.choice(GHOST_EMOJIS)
    num = random.randint(10, 999)
    return f"{emoji} {prefix}_{num}"

@app.before_request
def ensure_session_identity():
    if 'ghost_identity' not in session:
        session['ghost_identity'] = generate_random_identity()

@app.route('/')
def index():
    identity = session.get('ghost_identity', generate_random_identity())
    local_ip = get_local_ip()
    phone_url = f"http://{local_ip}:5000"
    return render_template('index.html', identity=identity, phone_url=phone_url, local_ip=local_ip)

@app.route('/chat')
def chat_page():
    identity = session.get('ghost_identity', generate_random_identity())
    local_ip = get_local_ip()
    phone_url = f"http://{local_ip}:5000"
    return render_template('chat.html', identity=identity, phone_url=phone_url, local_ip=local_ip)

@app.route('/qr')
def qr_page():
    local_ip = get_local_ip()
    phone_url = f"http://{local_ip}:5000"
    return render_template('qr.html', phone_url=phone_url, local_ip=local_ip)

@app.route('/api/host_info')
def host_info():
    local_ip = get_local_ip()
    return jsonify({
        'local_ip': local_ip,
        'phone_url': f"http://{local_ip}:5000"
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle image and file upload endpoint."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    allowed_exts = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'zip', 'txt', 'docx'}
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if ext not in allowed_exts:
        return jsonify({'error': 'File format not allowed'}), 400

    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    saved_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(saved_path)
    file_size = os.path.getsize(saved_path)

    relative_url = f"/uploads/{unique_filename}"
    return jsonify({
        'file_path': relative_url,
        'file_name': filename,
        'file_size': file_size
    })

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Active connected sessions tracking
connected_ghosts = {}  # sid -> {'ghost_name': ..., 'address': ...}

@socketio.on('connect')
def on_client_connect():
    identity = session.get('ghost_identity', generate_random_identity())
    session['ghost_identity'] = identity
    connected_ghosts[request.sid] = {
        'ghost_name': identity,
        'address': f"NET:{request.remote_addr}",
        'ble_name': f"Mobile Node ({request.remote_addr})",
        'rssi': -55,
        'distance': 0.8,
        'status': 'available',
        'avatar': identity.split()[0] if identity else '👻'
    }
    logger.info(f"Client connected with identity: {identity} from {request.remote_addr}")
    emit('identity_assigned', {'identity': identity})

@socketio.on('disconnect')
def on_client_disconnect():
    if request.sid in connected_ghosts:
        ghost_info = connected_ghosts.pop(request.sid)
        logger.info(f"Client disconnected: {ghost_info['ghost_name']}")

def get_merged_devices(scanned_res, current_sid):
    my_ghost = session.get('ghost_identity', '')
    scanned_devices = scanned_res.get('devices', [])
    
    # Add other connected network/mobile ghosts to the scan list
    merged = list(scanned_devices)
    for sid, info in connected_ghosts.items():
        if sid != current_sid and info['ghost_name'] != my_ghost:
            # Check if not already in list
            if not any(d['ghost_name'] == info['ghost_name'] for d in merged):
                merged.insert(0, info)

    return merged

@socketio.on('start_scan')
def on_start_scan():
    logger.info("Scanning for Bluetooth devices...")
    res = scanner.scan_sync(duration=2.5)
    devices = get_merged_devices(res, request.sid)
    emit('scan_results', {
        'devices': devices,
        'ble_error': res.get('ble_error')
    })

@socketio.on('connect_device')
def on_connect_device(data):
    address = data.get('address')
    device_info = data.get('device')
    logger.info(f"Connecting to device: {device_info}")
    
    success = connection_mgr.connect(device_info)
    status_data = connection_mgr.get_status()
    emit('connection_status', {
        'status': status_data['status'],
        'device': status_data['connected_device'],
        'success': success
    })

@socketio.on('disconnect_device')
def on_disconnect_device():
    logger.info("Disconnecting current Bluetooth device...")
    connection_mgr.disconnect()
    emit('connection_status', {
        'status': 'disconnected',
        'device': None
    })

@socketio.on('send_message')
def on_send_message(data):
    sender_ghost = session.get('ghost_identity', 'Ghost')
    receiver_ghost = data.get('receiver_ghost')
    content = data.get('content', '')
    msg_type = data.get('msg_type', 'text')
    file_path = data.get('file_path')
    file_name = data.get('file_name')
    file_size = data.get('file_size', 0)
    self_destruct = data.get('self_destruct_seconds', 0)

    msg_id = uuid.uuid4().hex

    # Payload AES encryption step
    raw_payload = {
        'msg_id': msg_id,
        'sender_ghost': sender_ghost,
        'receiver_ghost': receiver_ghost,
        'content': content,
        'msg_type': msg_type,
        'file_path': file_path,
        'file_name': file_name,
        'file_size': file_size,
        'self_destruct_seconds': self_destruct
    }
    encrypted_envelope = crypto_engine.encrypt_payload(raw_payload)
    decrypted_payload = crypto_engine.decrypt_payload(encrypted_envelope)

    # Save to SQLite database
    saved_msg = db.save_message(
        msg_id=decrypted_payload['msg_id'],
        sender_ghost=decrypted_payload['sender_ghost'],
        receiver_ghost=decrypted_payload['receiver_ghost'],
        content=decrypted_payload['content'],
        msg_type=decrypted_payload['msg_type'],
        file_path=decrypted_payload['file_path'],
        file_name=decrypted_payload['file_name'],
        file_size=decrypted_payload['file_size'],
        self_destruct_seconds=decrypted_payload['self_destruct_seconds']
    )

    # Emit message to sender confirmation and broadcast to recipient
    emit('message_sent_confirm', saved_msg)
    emit('new_message', saved_msg, broadcast=True)

@socketio.on('get_history')
def on_get_history(data):
    my_ghost = session.get('ghost_identity', 'Ghost')
    target_ghost = data.get('target_ghost')
    if target_ghost:
        messages = db.get_chat_history(my_ghost, target_ghost)
        emit('chat_history', {'messages': messages})

@socketio.on('typing')
def on_typing(data):
    my_ghost = session.get('ghost_identity', 'Ghost')
    receiver_ghost = data.get('receiver_ghost')
    emit('user_typing', {
        'sender_ghost': my_ghost,
        'receiver_ghost': receiver_ghost
    }, broadcast=True)

@socketio.on('mark_read')
def on_mark_read(data):
    sender_ghost = data.get('sender_ghost')
    my_ghost = session.get('ghost_identity', 'Ghost')
    if sender_ghost:
        db.mark_messages_read(sender_ghost, my_ghost)

def auto_scan_background_task():
    """Periodic background scanner task every 5s."""
    while True:
        try:
            socketio.sleep(5)
            res = scanner.scan_sync(duration=2.0)
            devices = res.get('devices', [])
            
            # Append connected ghosts
            for sid, info in list(connected_ghosts.items()):
                if not any(d['ghost_name'] == info['ghost_name'] for d in devices):
                    devices.insert(0, info)

            socketio.emit('scan_results', {
                'devices': devices,
                'ble_error': res.get('ble_error')
            })
        except Exception as e:
            logger.error(f"Background scanner loop error: {e}")

# Start background scanner loop when running
socketio.start_background_task(target=auto_scan_background_task)

def get_local_ip():
    try:
        s = py_socket.socket(py_socket.AF_INET, py_socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("\n" + "="*60)
    print(" BlueGhost - Anonymous Offline Bluetooth & Network Chat")
    print("="*60)
    print(f" Local Access:   http://127.0.0.1:5000")
    print(f" Phone Access:   http://{local_ip}:5000")
    print(" Open the Phone Access URL on your mobile browser (same Wi-Fi/Hotspot)")
    print("="*60 + "\n")
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
