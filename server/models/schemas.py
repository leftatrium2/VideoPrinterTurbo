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


class ASRConfigItem(BaseModel):
    tencent_cloud_secret_id: str = ""
    tencent_cloud_secret_key: str = ""
    xfyun_appid: str = ""
    xfyun_secret_key: str = ""
    xfyun_web_api: str = ""
    local_whisper_type: int = 0


class LLMConfigItem(BaseModel):
    base_url: str = ""
    api_key: str = ""
    provider_name: str = ""
    llm_model_name: str = ""
    memo: str = ""


class ProxyConfigItem(BaseModel):
    proxy_type: int = 0
    proxy_url: str = ""
    proxy_username: str = ""
    proxy_password: str = ""


class MaterialPexelsItem(BaseModel):
    pexels_api_key: str = ""


class MaterialPixabayItem(BaseModel):
    pixabay_api_key: str = ""
