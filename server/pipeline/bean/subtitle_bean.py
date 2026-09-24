class SubtitleBean(object):
    subtitle_lang: int = 0
    subtitle_font: str = ""
    subtitle_font_color: int = 0
    subtitle_border_color: int = 0
    subtitle_position: str = ""
    subtitle_size: int = 60

    def __str__(self) -> str:
        return f"""
        SubtitleBean(
            subtitle_lang: {self.subtitle_lang}, 
            subtitle_font: {self.subtitle_font}, 
            subtitle_font_color: {self.subtitle_font_color}, 
            subtitle_border_color: {self.subtitle_border_color}, 
            subtitle_position: {self.subtitle_position}, 
            subtitle_size: {self.subtitle_size}
        )
        """
