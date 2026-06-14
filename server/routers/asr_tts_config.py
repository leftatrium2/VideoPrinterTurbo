from fastapi import APIRouter

router = APIRouter(
    prefix="/asr_tts_config",
    tags=["asr_tts配置模块"]
)


@router.get("/")
def get_asr_tts_config():
    return {"abc": "bcd"}
