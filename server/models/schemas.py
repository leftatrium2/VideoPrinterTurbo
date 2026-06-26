from pydantic import BaseModel


class Task(BaseModel):
    task_url: str = ""
    is_deleted: int = 0
    status: int = 0
    task_id: int = 0


class TTSConfigItem(BaseModel):
    tts_server: int = 0
    tts_voice: str = ""
    tts_area: str = ""
    tts_apikey: str = ""
