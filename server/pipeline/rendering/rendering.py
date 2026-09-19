# 将处理后的视频、音频、字幕，按照以下逻辑进行混合，并最终导出
# 1. 视频部分，如果，选择了视频覆盖，那么直接使用覆盖后的多个视频，如果没有，那么使用下载的视频
# 2. 音频部分，
# 2.1. 如果选择了“输出到语音”，那么，将步骤1 视频部分的音频直接屏蔽掉，改用TTS生成的语音
# 2.2. 如果选择了“背景音乐”，那么，将bgm下载到的MP3文件，与上面的音频进行混合，同时背景音乐需要循环播放
# 3. 字幕部分
# 3.1. 如果选择了“输出到字幕”，那么按照里面的设置进行
# 3.2. 如果没有选择，那么，按照默认方式，默认如下：
#       字体：NotoSansSC-Regular.ttf
#       位置：底部居中
#       字幕颜色：白色
#       描边颜色：黑色
#       字幕大小：60
from pipeline.bean.ffmpeg_bean import FFMPEGBean


class Rendering(object):
    def __init__(self, bean: FFMPEGBean):
        self.__bean = bean
        pass

    def render(self):
        pass

    pass
