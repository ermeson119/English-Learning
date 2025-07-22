import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-desenvolvimento-nao-usar-em-producao'
    
    # Configurações do PostgreSQL
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'admin')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', '1234')
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'plataforma_ingles')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'db')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
    
    # Montar a URL do banco de dados
    SQLALCHEMY_DATABASE_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Configurações de upload
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB para vídeos