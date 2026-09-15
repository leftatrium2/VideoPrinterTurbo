from dataclasses import dataclass


class VideoOverlayItem:
    url: str = ""
    file_path: str = ""
    duration: int = 0
    aspect: int = 0
    provider: str = ""


class VideoOverlayBean:
    # 视频素材类型
    # local: 本地上传
    # pexels: https://www.pexels.com/zh-cn/
    # pixabay: https://pixabay.com/
    video_material_type: str = ""
    # 如果是local，那么存上传的素材地址
    uploaded_video_material: str = ""
    # 拼接模式
    video_material_splicing_mode: int = 0
    # 转场模式
    video_material_transition_mode: int = 0
    # 视频比例
    video_material_video_ratio: int = 0
    # 视频片段最大时长(秒)
    video_material_max_duration: int = 0
    # 同时生成视频数量
    video_material_generate_count: int = 0
    # 视频关键词（英文，可选）
    video_material_keyword: str = ""
    # 下载后得到的素材
    video_materials: list[VideoOverlayItem] = []
