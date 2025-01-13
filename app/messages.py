import hashlib
import base64
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from cryptography.fernet import Fernet
from .models import Message
from . import db

messages_bp = Blueprint('messages', __name__)

def derive_key(user_key: str) -> str:
    """Derive a 32-byte base64 key from a user-provided key."""
    sha256_hash = hashlib.sha256(user_key.encode()).digest()
    return base64.urlsafe_b64encode(sha256_hash[:32])

@messages_bp.route('/add', methods=['POST'])
@jwt_required()
def add_message():
    data = request.get_json()
    user_key = data['key'] 
    message_content = data['message']

    derived_key = derive_key(user_key)
    cipher = Fernet(derived_key)

    encrypted_message = cipher.encrypt(message_content.encode('utf-8'))

    user_id = get_jwt_identity()
    new_message = Message(content=encrypted_message, user_id=user_id)
    db.session.add(new_message)
    db.session.commit()

    return jsonify({'message': 'Message encrypted and added successfully'})

@messages_bp.route('/get', methods=['POST'])
@jwt_required()
def get_messages():
    data = request.get_json()
    user_key = data['key']  

    derived_key = derive_key(user_key)  
    cipher = Fernet(derived_key)

    user_id = get_jwt_identity()  
    messages = Message.query.filter_by(user_id=user_id).all()  

    decrypted_messages = []
    for message in messages:
        try:
            decrypted_content = cipher.decrypt(message.content).decode('utf-8')
            decrypted_messages.append(decrypted_content)
        except Exception:
            continue

    if len(decrypted_messages) == 0:
        return jsonify({'message': 'No messages found with this key^^'})

    return jsonify({'messages': decrypted_messages})
