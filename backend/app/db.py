from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# pool_pre_ping: 오래 쉬어서 끊긴 연결을 쓰기 전에 확인하고 새로 연결
# timezone=utc: DB가 돌려주는 시각을 UTC로 고정 (응답 시간 기준, D-57)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"options": "-c timezone=utc"},
)

# 요청 하나에서 쓰는 DB 작업 묶음(세션)을 만드는 틀
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
