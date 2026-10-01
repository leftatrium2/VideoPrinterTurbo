class AudioSeparatorBean():
    # 人声MP3 地址
    voice_path: str
    # 背景音MP3地址
    bgm_path: str

    def __str__(self) -> str:
        return f"""
        AudioSeparatorBean(
            voice_path: {self.voice_path}, 
            bgm_path: {self.bgm_path}
        )
        """
