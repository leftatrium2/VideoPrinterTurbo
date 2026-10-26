from abc import ABC, abstractmethod


class LipSyncBase(ABC):
    """开源模型和云服务共用的对口型接口。

    模型路径、设备、服务地址和凭据等配置由具体实现的构造函数接收。
    """

    @abstractmethod
    def lip_sync(self, video_path: str, audio_path: str, output_path: str) -> str:
        """使用最终配音驱动视频口型，返回生成视频的本地路径。

        Args:
            video_path: 待处理人物视频的本地路径。
            audio_path: 已确定时间线的最终配音，不包含 BGM。
            output_path: 输出视频的本地路径，与输入视频路径不同。

        实现约定：
            - 输入视频与配音使用相同时间起点，配音覆盖完整视频时间线。
            - 保持视频时长与时间线，不通过循环、变速或截断适配配音。
            - 输出音轨使用传入的最终配音，避免混入原视频人声。
            - 云服务实现负责上传、等待任务完成和下载；成功前不返回。
            - 校验输出文件存在、非空且可解码后返回；失败时抛出异常。
            - 保留输入文件，不覆盖或删除原视频和配音。
            - 具体实现可显式提供时间线扩展选项。RemoteLipSync 的 timeline="audio"
              以音频长度生成结果，允许循环/提前结束画面；默认 strict 及其他实现
              继续遵循上述保留原视频时间线的约定。
        """
        pass
