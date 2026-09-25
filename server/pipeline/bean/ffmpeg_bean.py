class FFMPEGBean(object):
    output_path: str = ""

    def __str__(self) -> str:
        return f"""
        FFMPEGBean(
        output_path: {self.output_path}
        )
        """
