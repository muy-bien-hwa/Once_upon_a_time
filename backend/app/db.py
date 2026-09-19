from sqlalchemy import create_engine

from app.config import settings

# pool_pre_ping: 오래 쉬어서 끊긴 연결을 쓰기 전에 확인하고 새로 연결
engine = create_engine(settings.database_url, pool_pre_ping=True)
