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
    aliyun_cloud_api_key: str = ""
    aliyun_cloud_model: str = ""
    azure_subscription_key: str = ""
    azure_region: str = ""
    openai_api_key: str = ""
    openai_model: str = ""
    openai_base_url: str = ""
    volcengine_appid: str = ""
    volcengine_access_token: str = ""


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


class TaskItem(BaseModel):
    task_id: str = ""
    task_url: str = ""
    # Is a proxy used for the downloader?
    is_download_proxy: bool = False
    ### 1. Audio to Text
    is_from_asr_or_subtitle: bool = False
    # Audio conversion method
    audio_rewrite_type: int = 0
    # Subtitle language
    subtitle_lang: int = 0
    ### 2. LLM Rewrite
    is_llm: bool = False
    # LLM Prompt
    llm_prompt: str = ""
    ### 3. Output to Speech
    is_rewrite_to_tts: bool = False
    # TTS service
    tts_server: str = ""
    # Voice role
    tts_voice: str = ""
    # Speech volume (1.0)
    tts_volume: float = 1.0
    # Speed (1.0)
    tts_speed: float = 1.0
    ### 4. Output to Subtitle
    is_rewrite_to_subtitle: bool = False
    # Font
    subtitle_font: str = ""
    # Position
    subtitle_position: str = ""
    # Subtitle font color
    subtitle_font_color: int = 0
    # Border color
    subtitle_border_color: int = 0
    # Subtitle size
    # 5. Background Music - Custom BGM
    is_bgm: bool = False
    # Select BGM library
    uploaded_bgm: dict = {}
    # BGM volume
    bgm_volume: float = 1.0
    # Subtitle size
    subtitle_size: int = 60
    ### 6. Video Overlay - Local files (multiple)
    is_video_material: bool = False
    # Video source
    video_material_type: str = ""
    uploaded_video_material: list = []
    # Splicing mode
    video_material_splicing_mode: int = 0
    # Transition mode
    video_material_transition_mode: int = 0
    # Video aspect ratio
    video_material_Video_ratio: int = 0
    # Max duration per video clip (seconds)
    video_material_max_duration: int = 10
    # Number of videos to generate
    video_material_generate_count: int = 1
    ### 7. Publish
    is_publish: bool = False
