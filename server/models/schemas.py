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


class TaskItem(BaseModel):
    task_url: str = ""
    ### 1. 音频转文字
    is_from_asr_or_subtitle: bool = False
    # 选择音频转换方式
    audio_rewrite_type: int = 0
    ### 2. LLM 改写
    is_llm: bool = False
    # LLM 提示词 (Prompt)
    llm_prompt: str = ""
    ### 3. 输出到语音
    is_rewrite_to_tts: bool = False
    # TTS 服务
    tts_server: str = ""
    # 声音角色
    tts_voice: str = ""
    # 语音音量 (1.0)
    tts_volume: float = 1.0
    # 速度 (1.0)
    tts_speed: float = 1.0
    ### 4. 输出到字幕
    is_rewrite_to_subtitle: bool = False
    # 字体
    subtitle_font: str = ""
    # 位置
    subtitle_position: str = ""
    # 字幕颜色
    subtitle_font_color: int = 0
    # 描边颜色
    subtitle_border_color: int = 0
    # 字幕大小
    # 5. 背景音乐 - 自定义背景音乐
    is_bgm: bool = False
    # 选择 BGM 库
    uploaded_bgm: dict = {}
    # 背景音乐音量
    bgm_volume: float = 1.0
    # 字幕大小
    subtitle_size: int = 60
    ### 6. 视频覆盖 - 本地文件（多文件）
    is_video_material: bool = False
    # 视频源
    video_material_type: str = ""
    uploaded_video_material: list = []
    # 拼接模式
    video_material_splicing_mode: int = 0
    # 转场模式
    video_material_transition_mode: int = 0
    # 视频比例
    video_material_Video_ratio: int = 0
    # 视频片段最大时长(秒)
    video_material_max_duration: int = 10
    # 同时生成视频数量
    video_material_generate_count: int = 1
    ### 7. 发布
    is_publish: bool = False
