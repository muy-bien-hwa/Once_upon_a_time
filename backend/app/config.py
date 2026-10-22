from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


def tidy_url(raw: str) -> str:
    """배포 화면에 붙여넣다 섞여 들어오는 것들을 털어 냄

    따옴표로 감싸거나, Neon 콘솔의 `psql '...'` 명령을 통째로 복사하거나,
    줄이 접혀 줄바꿈이 끼는 일이 흔함 (주소에는 원래 공백이 없음)
    """
    value = "".join(raw.split())
    if value.lower().startswith("psql"):
        value = value[4:]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # 설정 항목 : 타입(타입 검사 위해) = 기본값
    # 개발 PC: 조각으로 적음 / 운영(Neon·Render): 한 줄짜리 DATABASE_URL을 그대로 붙여넣음
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: SecretStr = SecretStr("")
    db_name: str = "relay"
    # 한 줄 접속 문자열이 있으면 위 조각들보다 **먼저** 씀 → DB를 옮길 때 이 한 줄만 바꾸면 됨
    db_url: SecretStr | None = Field(default=None, validation_alias="DATABASE_URL")

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
    # 여기가 배포 서버인지 (배포 설정에만 "production") → 자기 점검·API 문서 공개 여부를 가름
    app_env: str = Field(default="development", validation_alias="APP_ENV")

    # 신고가 몇 건 쌓이면 자동으로 접히는지 (D-49·D-93, .env로 조절)
    reports_to_fold: int = 5

    # 문장 추천 정렬 점수 설정값 (docs 04-ranking-score, D-37)
    sentence_rank_b: float = 1.0
    sentence_rank_h: float = 48.0
    sentence_rank_j0: float = 0.3

    # 포럼 Hot 정렬 설정값 (같은 공식, 새 글 가산점이 24시간마다 절반 / 흔들기 없음)
    forum_rank_b: float = 1.0
    forum_rank_h: float = 24.0
    forum_rank_j0: float = 0.0

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @field_validator("db_url", mode="after")
    @classmethod
    def _tidy_db_url(cls, value: SecretStr | None) -> SecretStr | None:
        """비어 있으면 없는 것으로 (설정칸만 만들고 값을 안 넣은 경우)"""
        if value is None:
            return None
        cleaned = tidy_url(value.get_secret_value())
        return SecretStr(cleaned) if cleaned else None

    @property
    def database_url(self) -> URL:
        if self.db_url is not None:
            try:
                # psycopg(3)로 붙도록 드라이버만 바꿔 끼움 (sslmode 같은 뒷부분은 그대로 둠)
                return make_url(self.db_url.get_secret_value()).set(drivername="postgresql+psycopg")
            except ArgumentError:
                # 값 자체는 비밀번호가 들어 있으니 절대 출력하지 않음
                raise RuntimeError(
                    "DATABASE_URL을 읽을 수 없어요. "
                    "`postgresql://이름:비밀번호@주소/DB이름?sslmode=require` 한 줄이어야 합니다 "
                    "(따옴표·`psql`·줄바꿈 없이 통째로)"
                ) from None

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
