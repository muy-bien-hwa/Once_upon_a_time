from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # 설정 항목 : 타입(타입 검사 위해) = 기본값
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: SecretStr
    db_name: str = "relay"

    # 2단계 가짜 로그인: 이 id의 유저로 로그인한 것처럼 동작. 비우면 로그인 안 한 상태
    # 3단계(구글 로그인)에서 삭제 (운영 서버에 남으면 누구나 이 유저가 됨)
    dev_user_id: int | None = None

    # 문장 추천 정렬 점수 설정값 (docs 04-ranking-score, D-37)
    sentence_rank_b: float = 1.0
    sentence_rank_h: float = 48.0
    sentence_rank_j0: float = 0.3

    @property
    def database_url(self) -> URL:
        # URL.create가 비밀번호의 특수문자(@, :, / 등)를 알아서 처리함
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


settings = Settings()
