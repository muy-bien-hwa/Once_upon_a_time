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

    # 구글 로그인 (3단계, F-06) — 값은 .env에만 (구글 콘솔에서 발급)
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    # 로그인 쿠키(JWT)에 서명할 비밀 문자열
    jwt_secret: SecretStr = SecretStr("")
    # 로그인 후 돌아갈 화면 주소 (개발은 프론트 5173, 배포는 같은 주소라 "/")
    frontend_origin: str = "http://localhost:5173"
    # 구글이 로그인 끝나고 돌아올 우리 서버 주소 (구글 콘솔에 등록한 것과 글자까지 같아야 함)
    # 개발에서 127.0.0.1로 두면 쿠키가 localhost 화면에 안 붙음 → localhost로 통일
    backend_origin: str = "http://localhost:8000"
    # 쿠키를 https에서만 보낼지 (개발 false, 배포 true)
    cookie_secure: bool = False

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
