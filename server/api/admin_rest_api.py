#!/usr/bin/env python3
# REST API для администрирования XVPN
# Абсолютный путь: ~/chatvpn/server/api/admin_rest_api.py

import os
import json
import time
import logging
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import uuid
from dataclasses import dataclass, asdict

# Для Flask API
try:
    from flask import Flask, request, jsonify, g
    from flask_cors import CORS
    from functools import wraps
    FLASK_AVAILABLE = True
except ImportError:
    print("Warning: Flask not available. Using mock API for testing.")
    FLASK_AVAILABLE = False

# Для аутентификации
try:
    from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("Warning: Flask-JWT-Extended not available. Using mock authentication.")

# Для баз данных
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("Warning: psycopg2 not available. Using SQLite fallback.")

# Настройка логирования
LOG_DIR = os.path.expanduser("~/chatvpn/server/api/logs")
LOG_FILE = os.path.join(LOG_DIR, "admin_api.log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AdminUser:
    """Класс для представления администратора"""
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    api_key: Optional[str] = None

@dataclass
class SystemConfig:
    """Класс для системной конфигурации"""
    id: str
    key: str
    value: Any
    description: str
    updated_at: datetime
    updated_by: str

@dataclass
class ClientStats:
    """Класс для статистики клиентов"""
    total_clients: int
    active_clients: int
    inactive_clients: int
    total_bandwidth: int
    avg_uptime: float
    top_protocols: List[Dict[str, Any]]

class AdminRESTAPI:
    """REST API для администрирования XVPN сервиса"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app = Flask(__name__) if FLASK_AVAILABLE else None
        self.setup_app()
        
        # Пути к базам данных
        self.db_path = os.path.expanduser('~/chatvpn/server/api/admin.db')
        self.init_database()
        
        # Инициализация JWT
        if JWT_AVAILABLE and self.app:
            self.jwt = JWTManager(self.app)
            self.setup_jwt()
        
        # API ключи
        self.api_keys = {}
        self.load_api_keys()
        
        # Системные настройки
        self.system_config = {}
        self.load_system_config()
        
        # Метрики
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': datetime.now()
        }
        
        logger.info("Admin REST API initialized successfully")
    
    def setup_app(self):
        """Настройка Flask приложения"""
        if not FLASK_AVAILABLE or not self.app:
            return
            
        # Конфигурация
        self.app.config['SECRET_KEY'] = self.config.get('secret_key', os.urandom(24).hex())
        self.app.config['JWT_SECRET_KEY'] = self.config.get('jwt_secret_key', os.urandom(24).hex())
        self.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
        
        # CORS
        CORS(self.app, resources={
            r"/api/*": {
                "origins": self.config.get('allowed_origins', ['*']),
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })
        
        # Регистрация обработчиков ошибок
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Endpoint not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {error}")
            return jsonify({'error': 'Internal server error'}), 500
        
        # Регистрация роутов
        self.register_routes()
    
    def setup_jwt(self):
        """Настройка JWT"""
        @self.jwt.user_identity_loader
        def user_identity_lookup(user):
            return user['username']
        
        @self.jwt.user_lookup_loader
        def user_lookup_callback(jwt_header, jwt_payload):
            username = jwt_payload["sub"]
            return self.get_user_by_username(username)
    
    def register_routes(self):
        """Регистрация API роутов"""
        if not FLASK_AVAILABLE or not self.app:
            return
            
        # Health check
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        
        # Аутентификация
        @self.app.route('/api/auth/login', methods=['POST'])
        def login():
            return self.authenticate_user()
        
        @self.app.route('/api/auth/logout', methods=['POST'])
        @jwt_required()
        def logout():
            return jsonify({'message': 'Successfully logged out'})
        
        # API ключи
        @self.app.route('/api/auth/api-key', methods=['POST'])
        @jwt_required()
        def generate_api_key():
            return self.generate_new_api_key()
        
        # Управление пользователями
        @self.app.route('/api/admin/users', methods=['GET'])
        @jwt_required()
        def get_users():
            return self.get_all_users()
        
        @self.app.route('/api/admin/users/<user_id>', methods=['GET'])
        @jwt_required()
        def get_user(user_id):
            return self.get_user_by_id(user_id)
        
        @self.app.route('/api/admin/users', methods=['POST'])
        @jwt_required()
        def create_user():
            return self.create_new_user()
        
        @self.app.route('/api/admin/users/<user_id>', methods=['PUT'])
        @jwt_required()
        def update_user(user_id):
            return self.update_user(user_id)
        
        @self.app.route('/api/admin/users/<user_id>', methods=['DELETE'])
        @jwt_required()
        def delete_user(user_id):
            return self.delete_user(user_id)
        
        # Статистика и мониторинг
        @self.app.route('/api/admin/stats', methods=['GET'])
        @jwt_required()
        def get_system_stats():
            return self.get_system_statistics()
        
        @self.app.route('/api/admin/stats/clients', methods=['GET'])
        @jwt_required()
        def get_client_stats():
            return self.get_client_statistics()
        
        @self.app.route('/api/admin/logs', methods=['GET'])
        @jwt_required()
        def get_system_logs():
            return self.get_system_logs()
        
        # Конфигурация системы
        @self.app.route('/api/admin/config', methods=['GET'])
        @jwt_required()
        def get_config():
            return self.get_system_configuration()
        
        @self.app.route('/api/admin/config', methods=['PUT'])
        @jwt_required()
        def update_config():
            return self.update_system_configuration()
        
        # Управление клиентами
        @self.app.route('/api/admin/clients', methods=['GET'])
        @jwt_required()
        def get_clients():
            return self.get_all_clients()
        
        @self.app.route('/api/admin/clients/<client_id>', methods=['GET'])
        @jwt_required()
        def get_client(client_id):
            return self.get_client_info(client_id)
        
        @self.app.route('/api/admin/clients/<client_id>/status', methods=['PUT'])
        @jwt_required()
        def update_client_status(client_id):
            return self.update_client_status(client_id)
        
        # Безопасность
        @self.app.route('/api/admin/security/audit', methods=['GET'])
        @jwt_required()
        def security_audit():
            return self.perform_security_audit()
        
        @self.app.route('/api/admin/security/sessions', methods=['GET'])
        @jwt_required()
        def get_active_sessions():
            return self.get_active_sessions()
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица пользователей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admin_users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'admin',
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        api_key TEXT UNIQUE
                    )
                ''')
                
                # Таблица настроек
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_config (
                        id TEXT PRIMARY KEY,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT NOT NULL,
                        description TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_by TEXT
                    )
                ''')
                
                # Таблица логов API
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS api_logs (
                        id TEXT PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        endpoint TEXT,
                        method TEXT,
                        user_id TEXT,
                        ip_address TEXT,
                        status_code INTEGER,
                        response_time REAL,
                        user_agent TEXT
                    )
                ''')
                
                # Таблица статистики клиентов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS client_stats (
                        id TEXT PRIMARY KEY,
                        client_id TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT,
                        bandwidth_used INTEGER,
                        uptime REAL,
                        protocol TEXT,
                        ip_address TEXT
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def authenticate_user(self) -> Tuple[Dict[str, Any], int]:
        """Аутентификация пользователя"""
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return {'error': 'Username and password required'}, 400
            
            user = self.get_user_by_username(username)
            if not user or not user.is_active:
                return {'error': 'Invalid credentials'}, 401
            
            # Проверка пароля (упрощенная)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT password_hash FROM admin_users WHERE username = ?
                ''', (username,))
                result = cursor.fetchone()
                
                if not result or result[0] != password_hash:
                    return {'error': 'Invalid credentials'}, 401
            
            # Создание JWT токена
            access_token = create_access_token(identity=username)
            
            # Обновление времени последнего входа
            self.update_last_login(username)
            
            logger.info(f"User {username} authenticated successfully")
            
            return {
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {'error': 'Authentication failed'}, 500
    
    def get_user_by_username(self, username: str) -> Optional[AdminUser]:
        """Получение пользователя по имени пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM admin_users WHERE username = ?
                ''', (username,))
                
                row = cursor.fetchone()
                if row:
                    return AdminUser(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        role=row['role'],
                        is_active=bool(row['is_active']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
                        api_key=row['api_key']
                    )
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[AdminUser]:
        """Получение пользователя по ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM admin_users WHERE id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return AdminUser(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        role=row['role'],
                        is_active=bool(row['is_active']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
                        api_key=row['api_key']
                    )
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def get_all_users(self) -> Tuple[Dict[str, Any], int]:
        """Получение всех пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, username, email, role, is_active, created_at, last_login
                    FROM admin_users
                    ORDER BY created_at DESC
                ''')
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'id': row['id'],
                        'username': row['username'],
                        'email': row['email'],
                        'role': row['role'],
                        'is_active': bool(row['is_active']),
                        'created_at': row['created_at'],
                        'last_login': row['last_login']
                    })
                
                return {'users': users}, 200
                
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return {'error': 'Failed to get users'}, 500
    
    def create_new_user(self) -> Tuple[Dict[str, Any], int]:
        """Создание нового пользователя"""
        try:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            role = data.get('role', 'admin')
            
            if not all([username, email, password]):
                return {'error': 'Username, email, and password required'}, 400
            
            # Проверка существования пользователя
            existing_user = self.get_user_by_username(username)
            if existing_user:
                return {'error': 'Username already exists'}, 409
            
            # Хеширование пароля
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Создание пользователя
            user_id = str(uuid.uuid4())
            new_user = AdminUser(
                id=user_id,
                username=username,
                email=email,
                role=role,
                is_active=True,
                created_at=datetime.now()
            )
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO admin_users 
                    (id, username, email, password_hash, role, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, username, email, password_hash, role, True, datetime.now()))
                
                conn.commit()
            
            logger.info(f"New user created: {username}")
            
            return {'message': 'User created successfully', 'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'role': role
            }}, 201
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return {'error': 'Failed to create user'}, 500
    
    def update_user(self, user_id: str) -> Tuple[Dict[str, Any], int]:
        """Обновление пользователя"""
        try:
            data = request.get_json()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверка существования пользователя
                cursor.execute('SELECT * FROM admin_users WHERE id = ?', (user_id,))
                if not cursor.fetchone():
                    return {'error': 'User not found'}, 404
                
                # Формирование запроса обновления
                update_fields = []
                update_values = []
                
                if 'email' in data:
                    update_fields.append('email = ?')
                    update_values.append(data['email'])
                
                if 'role' in data:
                    update_fields.append('role = ?')
                    update_values.append(data['role'])
                
                if 'is_active' in data:
                    update_fields.append('is_active = ?')
                    update_values.append(data['is_active'])
                
                if 'password' in data:
                    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
                    update_fields.append('password_hash = ?')
                    update_values.append(password_hash)
                
                if update_fields:
                    update_values.append(user_id)
                    cursor.execute(f'''
                        UPDATE admin_users 
                        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', update_values)
                    conn.commit()
            
            logger.info(f"User updated: {user_id}")
            
            return {'message': 'User updated successfully'}, 200
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return {'error': 'Failed to update user'}, 500
    
    def delete_user(self, user_id: str) -> Tuple[Dict[str, Any], int]:
        """Удаление пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверка существования пользователя
                cursor.execute('SELECT * FROM admin_users WHERE id = ?', (user_id,))
                if not cursor.fetchone():
                    return {'error': 'User not found'}, 404
                
                # Удаление пользователя
                cursor.execute('DELETE FROM admin_users WHERE id = ?', (user_id,))
                conn.commit()
            
            logger.info(f"User deleted: {user_id}")
            
            return {'message': 'User deleted successfully'}, 200
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return {'error': 'Failed to delete user'}, 500
    
    def generate_new_api_key(self) -> Tuple[Dict[str, Any], int]:
        """Генерация нового API ключа"""
        try:
            current_user = get_jwt_identity()
            user = self.get_user_by_username(current_user)
            
            if not user or user.role != 'admin':
                return {'error': 'Unauthorized'}, 403
            
            # Генерация API ключа
            api_key = f'xvpn_{secrets.token_urlsafe(32)}'
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE admin_users SET api_key = ? WHERE id = ?
                ''', (api_key, user.id))
                conn.commit()
            
            logger.info(f"New API key generated for user: {current_user}")
            
            return {'api_key': api_key}, 200
            
        except Exception as e:
            logger.error(f"Error generating API key: {e}")
            return {'error': 'Failed to generate API key'}, 500
    
    def get_system_statistics(self) -> Tuple[Dict[str, Any], int]:
        """Получение системной статистики"""
        try:
            stats = {
                'system': {
                    'uptime': str(datetime.now() - self.metrics['start_time']),
                    'total_requests': self.metrics['total_requests'],
                    'successful_requests': self.metrics['successful_requests'],
                    'failed_requests': self.metrics['failed_requests'],
                    'success_rate': self.metrics['successful_requests'] / max(1, self.metrics['total_requests'])
                },
                'database': {
                    'total_users': len(self.get_all_users()[0]['users']),
                    'total_configs': len(self.system_config),
                    'api_keys_count': len(self.api_keys)
                }
            }
            
            return {'stats': stats}, 200
            
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return {'error': 'Failed to get statistics'}, 500
    
    def get_client_statistics(self) -> Tuple[Dict[str, Any], int]:
        """Получение статистики клиентов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Общая статистика
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_clients,
                        SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_clients,
                        SUM(CASE WHEN status = 'inactive' THEN 1 ELSE 0 END) as inactive_clients,
                        SUM(bandwidth_used) as total_bandwidth
                    FROM client_stats
                    WHERE timestamp >= datetime('now', '-7 days')
                ''')
                
                row = cursor.fetchone()
                total_clients, active_clients, inactive_clients, total_bandwidth = row
                
                # Среднее время работы
                cursor.execute('''
                    SELECT AVG(uptime) as avg_uptime
                    FROM client_stats
                    WHERE timestamp >= datetime('now', '-7 days')
                ''')
                
                avg_uptime = cursor.fetchone()[0] or 0
                
                # Популярные протоколы
                cursor.execute('''
                    SELECT protocol, COUNT(*) as count
                    FROM client_stats
                    WHERE timestamp >= datetime('now', '-7 days')
                    GROUP BY protocol
                    ORDER BY count DESC
                    LIMIT 5
                ''')
                
                top_protocols = [{'protocol': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
                client_stats = ClientStats(
                    total_clients=total_clients or 0,
                    active_clients=active_clients or 0,
                    inactive_clients=inactive_clients or 0,
                    total_bandwidth=total_bandwidth or 0,
                    avg_uptime=avg_uptime,
                    top_protocols=top_protocols
                )
                
                return {'client_stats': asdict(client_stats)}, 200
                
        except Exception as e:
            logger.error(f"Error getting client statistics: {e}")
            return {'error': 'Failed to get client statistics'}, 500
    
    def get_system_logs(self) -> Tuple[Dict[str, Any], int]:
        """Получение системных логов"""
        try:
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM api_logs
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                logs = []
                for row in cursor.fetchall():
                    logs.append(dict(row))
                
                return {'logs': logs, 'total': len(logs)}, 200
                
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return {'error': 'Failed to get system logs'}, 500
    
    def get_system_configuration(self) -> Tuple[Dict[str, Any], int]:
        """Получение системной конфигурации"""
        try:
            config = {}
            for key, value in self.system_config.items():
                config[key] = {
                    'value': value['value'],
                    'description': value['description'],
                    'updated_at': value['updated_at'].isoformat(),
                    'updated_by': value['updated_by']
                }
            
            return {'config': config}, 200
            
        except Exception as e:
            logger.error(f"Error getting system configuration: {e}")
            return {'error': 'Failed to get system configuration'}, 500
    
    def update_system_configuration(self) -> Tuple[Dict[str, Any], int]:
        """Обновление системной конфигурации"""
        try:
            data = request.get_json()
            current_user = get_jwt_identity()
            
            for key, value in data.items():
                if key in self.system_config:
                    self.system_config[key]['value'] = value
                    self.system_config[key]['updated_at'] = datetime.now()
                    self.system_config[key]['updated_by'] = current_user
            
            # Сохранение в базу данных
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for key, config in self.system_config.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO system_config 
                        (id, key, value, description, updated_at, updated_by)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        key,
                        key,
                        json.dumps(config['value']),
                        config['description'],
                        config['updated_at'],
                        config['updated_by']
                    ))
                
                conn.commit()
            
            logger.info(f"System configuration updated by {current_user}")
            
            return {'message': 'Configuration updated successfully'}, 200
            
        except Exception as e:
            logger.error(f"Error updating system configuration: {e}")
            return {'error': 'Failed to update system configuration'}, 500
    
    def get_all_clients(self) -> Tuple[Dict[str, Any], int]:
        """Получение всех клиентов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT DISTINCT client_id, status, MAX(timestamp) as last_seen
                    FROM client_stats
                    GROUP BY client_id
                    ORDER BY last_seen DESC
                ''')
                
                clients = []
                for row in cursor.fetchall():
                    clients.append({
                        'client_id': row['client_id'],
                        'status': row['status'],
                        'last_seen': row['last_seen']
                    })
                
                return {'clients': clients}, 200
                
        except Exception as e:
            logger.error(f"Error getting all clients: {e}")
            return {'error': 'Failed to get clients'}, 500
    
    def get_client_info(self, client_id: str) -> Tuple[Dict[str, Any], int]:
        """Получение информации о клиенте"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM client_stats
                    WHERE client_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''', (client_id,))
                
                stats = []
                for row in cursor.fetchall():
                    stats.append(dict(row))
                
                return {'client_id': client_id, 'stats': stats}, 200
                
        except Exception as e:
            logger.error(f"Error getting client info: {e}")
            return {'error': 'Failed to get client info'}, 500
    
    def update_client_status(self, client_id: str) -> Tuple[Dict[str, Any], int]:
        """Обновление статуса клиента"""
        try:
            data = request.get_json()
            new_status = data.get('status')
            
            if new_status not in ['active', 'inactive', 'banned']:
                return {'error': 'Invalid status'}, 400
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO client_stats 
                    (id, client_id, status, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (str(uuid.uuid4()), client_id, new_status, datetime.now()))
                
                conn.commit()
            
            logger.info(f"Client {client_id} status updated to {new_status}")
            
            return {'message': 'Client status updated successfully'}, 200
            
        except Exception as e:
            logger.error(f"Error updating client status: {e}")
            return {'error': 'Failed to update client status'}, 500
    
    def perform_security_audit(self) -> Tuple[Dict[str, Any], int]:
        """Проверка безопасности"""
        try:
            audit_results = {
                'last_24h_failed_logins': 0,
                'active_sessions': len(self.get_active_sessions()[0]['sessions']),
                'security_issues': [],
                'recommendations': []
            }
            
            # Проверка неудачных попыток входа
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM api_logs
                    WHERE endpoint = '/api/auth/login'
                    AND status_code = 401
                    AND timestamp >= datetime('now', '-24 hours')
                ''')
                
                audit_results['last_24h_failed_logins'] = cursor.fetchone()[0]
            
            # Проверка на проблемы безопасности
            if audit_results['last_24h_failed_logins'] > 10:
                audit_results['security_issues'].append('High number of failed login attempts')
                audit_results['recommendations'].append('Enable IP locking after multiple failed attempts')
            
            if audit_results['active_sessions'] > 10:
                audit_results['security_issues'].append('High number of active sessions')
                audit_results['recommendations'].append('Review active sessions and consider session limits')
            
            return {'security_audit': audit_results}, 200
            
        except Exception as e:
            logger.error(f"Error performing security audit: {e}")
            return {'error': 'Failed to perform security audit'}, 500
    
    def get_active_sessions(self) -> Tuple[Dict[str, Any], int]:
        """Получение активных сессий"""
        try:
            sessions = []
            
            # Получение последних активных пользователей
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT username, last_login
                    FROM admin_users
                    WHERE is_active = TRUE
                    AND last_login >= datetime('now', '-1 hour')
                    ORDER BY last_login DESC
                ''')
                
                for row in cursor.fetchall():
                    sessions.append({
                        'username': row['username'],
                        'last_login': row['last_login'],
                        'status': 'active'
                    })
            
            return {'sessions': sessions, 'total': len(sessions)}, 200
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return {'error': 'Failed to get active sessions'}, 500
    
    def update_last_login(self, username: str):
        """Обновление времени последнего входа"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE admin_users SET last_login = ? WHERE username = ?
                ''', (datetime.now(), username))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
    
    def load_api_keys(self):
        """Загрузка API ключей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT username, api_key FROM admin_users WHERE api_key IS NOT NULL
                ''')
                
                for row in cursor.fetchall():
                    self.api_keys[row[1]] = row[0]
                    
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
    
    def load_system_config(self):
        """Загрузка системной конфигурации"""
        try:
            default_config = {
                'max_clients': 1000,
                'bandwidth_limit': 1000000, # 1TB
                'session_timeout': 3600, # 1 hour
                'log_retention_days': 30,
                'max_failed_login_attempts': 5,
                'enable_ip_locking': True
            }
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT key, value, description, updated_at, updated_by
                    FROM system_config
                ''')
                
                for row in cursor.fetchall():
                    key, value, description, updated_at, updated_by = row
                    self.system_config[key] = {
                        'value': json.loads(value),
                        'description': description,
                        'updated_at': datetime.fromisoformat(updated_at),
                        'updated_by': updated_by
                    }
                
                # Добавление настроек по умолчанию
                for key, value in default_config.items():
                    if key not in self.system_config:
                        self.system_config[key] = {
                            'value': value,
                            'description': f'Default {key} configuration',
                            'updated_at': datetime.now(),
                            'updated_by': 'system'
                        }
                        
        except Exception as e:
            logger.error(f"Error loading system config: {e}")
    
    def log_api_request(self, endpoint: str, method: str, user_id: str, 
                       ip_address: str, status_code: int, response_time: float):
        """Логирование API запроса"""
        try:
            log_id = str(uuid.uuid4())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO api_logs 
                    (id, endpoint, method, user_id, ip_address, status_code, response_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (log_id, endpoint, method, user_id, ip_address, status_code, response_time))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error logging API request: {e}")
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Запуск API сервера"""
        if FLASK_AVAILABLE and self.app:
            logger.info(f"Starting Admin REST API on {host}:{port}")
            self.app.run(host=host, port=port, debug=debug)
        else:
            logger.warning("Flask not available. Using mock mode.")
            print("Admin REST API is running in mock mode")
            print("Available endpoints:")
            print("  GET /api/health - Health check")
            print("  POST /api/auth/login - Login")
            print("  GET /api/admin/stats - System statistics")
            print("  GET /api/admin/config - System configuration")
            print("  Mock mode - No actual functionality available")

def create_admin_api(config: Dict[str, Any] = None) -> AdminRESTAPI:
    """Фабричная функция для создания Admin REST API"""
    if config is None:
        config = {}
    
    return AdminRESTAPI(config)

if __name__ == "__main__":
    # Пример использования
    config = {
        'secret_key': 'your-secret-key-here',
        'jwt_secret_key': 'your-jwt-secret-key-here',
        'allowed_origins': ['http://localhost:3000', 'https://admin.xvpn.com']
    }
    
    api = create_admin_api(config)
    api.run(debug=True)