class BgmBean:
    # 背景音乐音量
    bgm_volume: float = 0
    # 自定义背景音乐
    # 如果这里为空，就表示选择随机背景音乐
    uploaded_bgm: str = ""

    def __str__(self) -> str:
        return f"""
        BgmBean(
            bgm_volume: {self.bgm_volume}, 
            uploaded_bgm: {self.uploaded_bgm}
        )
        """
