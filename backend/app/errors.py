from fastapi import HTTPException


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    """에러 응답 모양: {"detail": {"code": ..., "message": ...}} (D-57)

    화면에는 message만 보여주고, code는 프론트 코드에서 에러 종류를 나눌 때 씀
    사용 예: raise api_error(404, "STORY_NOT_FOUND", "없는 스토리예요")
    """
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})
