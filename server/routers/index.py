from fastapi import APIRouter

from middleware.i18n_middleware import get_current_lang

router = APIRouter()


@router.get("/")
async def root():
    lang = get_current_lang()
    return {"message": f"{lang}"}
