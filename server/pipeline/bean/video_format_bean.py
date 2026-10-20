class VideoFormatBean:
    """一个视频的一种可下载格式；码率单位为 kbps，大小单位为字节。"""

    url: str  # 原始视频页面 URL（非媒体直链），用于后续 download() 重新解析下载
    format_id: str  # YouTube 内部格式 ID（如 '231'），yt-dlp 用它来指定下载哪种流
    title: str = ''  # 视频标题
    duration: float | None = None  # 视频时长，单位为秒（如 2799 ≈ 46分39秒）
    uploader: str = ''  # 频道/上传者名称
    thumbnail: str = ''  # 最高分辨率缩略图地址
    ext: str = ''  # 容器格式（如 'mp4'、'webm'）
    width: int | None = None  # 视频宽度，单位为像素（如 854）
    height: int | None = None  # 视频高度，单位为像素（如 480 表示 480p）
    resolution: str = ''  # 分辨率字符串（如 '854x480'），纯音频时为 'audio only'
    fps: float | None = None  # 帧率，每秒帧数（如 30.0）
    vcodec: str = 'none'  # 视频编码（如 'avc1.4D401F' 即 H.264 Main Profile Level 3.1；'none' 表示无视频轨道）
    acodec: str = 'none'  # 音频编码（如 'mp4a.40.2' 即 AAC；'none' 表示无音频轨道——YouTube DASH 流中视频和音频通常是分离的）
    vbr: float | None = None  # 视频码率，单位为 kbps（如 710.387）
    abr: float | None = None  # 音频码率，单位为 kbps；纯视频流时为 0
    tbr: float | None = None  # 总码率（视频+音频），单位为 kbps；纯视频流时等于 vbr
    filesize: int | None = None  # 精确文件大小，单位为字节；DASH 流通常不返回此值
    filesize_approx: int | None = None  # 估算文件大小，单位为字节；YouTube 可能不提供
    format_note: str = ''  # 格式备注标签（如 '1080p'、'premium'），YouTube 可能不提供
    proxy: str | None = None  # 访问该视频使用的代理地址（如 'http://127.0.0.1:7890'）

    def _get_str(self):
        return f"""
        VideoFormatBean(
            url={self.url},
            format_id={self.format_id},
            title={self.title},
            duration={self.duration},
            uploader={self.uploader},
            thumbnail={self.thumbnail},
            ext={self.ext},
            width={self.width},
            height={self.height},
            resolution={self.resolution},
            fps={self.fps},
            vcodec={self.vcodec},
            acodec={self.acodec},
            vbr={self.vbr},
            abr={self.abr},
            tbr={self.tbr},
            filesize={self.filesize},
            filesize_approx={self.filesize_approx},
            format_note={self.format_note},
            proxy={self.proxy},
        )
"""

    def __repr__(self) -> str:
        return self._get_str()

    def __str__(self) -> str:
        return self._get_str()
