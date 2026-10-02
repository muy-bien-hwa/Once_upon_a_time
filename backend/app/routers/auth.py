"""구글 로그인 (docs 07 인증, F-06)

흐름: 로그인 버튼 → /auth/google/login → 구글 로그인 화면 → /auth/google/callback
     → 우리 DB에서 유저 찾기·만들기 → 로그인 표를 쿠키에 담아 화면으로 돌려보냄
"""

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from app.config import settings
from app.deps import DbSession
from app.errors import api_error
from app.security import COOKIE_DAYS, COOKIE_NAME, create_token
from app.services import users as user_service

router = APIRouter(prefix="/auth", tags=["auth"])

# 구글 콘솔의 "승인된 리디렉션 URI"와 글자까지 똑같아야 함
CALLBACK_URL = f"{settings.backend_origin}/auth/google/callback"

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret.get_secret_value(),
    # 구글이 알려주는 주소 목록 (엔드포인트를 직접 적지 않아도 됨)
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/google/login")
async def google_login(request: Request):
    """구글 로그인 화면으로 보냄"""
    return await oauth.google.authorize_redirect(request, CALLBACK_URL)


@router.get("/google/callback")
async def google_callback(request: Request, db: DbSession):
    """구글에서 돌아온 사람을 확인하고 로그인 쿠키를 발급"""
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        # 사용자가 취소했거나 값이 어긋난 경우
        raise api_error(401, "AUTH_FAILED", "구글 로그인에 실패했어요") from None

    google_user_id = (token.get("userinfo") or {}).get("sub")
    if not google_user_id:
        raise api_error(401, "AUTH_FAILED", "구글 로그인에 실패했어요")

    user = user_service.get_or_create_google_user(db, google_user_id)
    response = RedirectResponse(settings.frontend_origin or "/")
    _set_login_cookie(response, user.id)
    return response


@router.post("/logout")
def logout(response: Response):
    """로그인 쿠키 지우기"""
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "ok"}


def _set_login_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE_NAME,
        create_token(user_id),
        max_age=COOKIE_DAYS * 24 * 60 * 60,
        # 자바스크립트가 못 읽게 → 쿠키를 훔쳐가는 공격 방지
        httponly=True,
        # 배포(https)에서만 보내도록 (개발은 false)
        secure=settings.cookie_secure,
        # 다른 사이트에서 우리 API를 몰래 부르지 못하게
        samesite="lax",
        path="/",
    )
