<div align="center">
<h1 align="center">VideoPrinterTurbo<img src="doc/VideoPrinterTurbo.png"></h1>
<br>
<h3> <a href="README.md">English</a> | 简体中文</h3>
<br>
</div>


###  MoneyPrinterTurbo 姊妹篇
###  MoneyPrinterTurbo生成视频，VideoPrinterTurbo用来做二创
```
VideoPrinterTurbo 使用须知与免责声明

VideoPrinterTurbo 仅提供视频处理与辅助创作功能，不授予任何第三方内容的使用权。用户应确保素材及其使用方式合法，取得必要授权，并遵守相关平台规则；二次创作、注明来源或非商业使用不当然免除侵权责任。本工具按现状提供，不保证输出内容的准确性、合法性或适用性，用户应在发布前自行审核。因用户违法或侵权行为产生的责任由其依法承担。本声明不排除或限制开发者及提供方依法不得免除的责任。
```

### VideoPrinterTurbo 能做什么？

+ 视频下载

  + VideoPrinterTurbo 基于yt-dlp，可以支持大多数的视频网站视频下载
  
    具体参照：https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
  
  + 对于无法下载的视频，VideoPrinterTurbo 提供方便的插件方式

+ 视频 AI 翻译

  + 调用链：下载->ASR->LLM改写->字幕配置->输出成品
#### 原视频：

[![Watch the demo](doc/thumbnails.webp)](https://www.youtube.com/watch?v=E7YiKBeOneo&t=1s)

#### 增加翻译字幕后：

[![Watch the demo](doc/thumbnails.webp)](https://www.youtube.com/watch?v=AiSW3_SyaKs)

+ 视频 AI 重配音

#### 增加翻译字幕并重新配音：
[![Watch the demo](doc/thumbnails.webp)](https://www.youtube.com/watch?v=08dmRF8JVaI)

+ 视频全覆盖
#### 增加翻译字幕、重新配音并修改视频：
[![Watch the demo](doc/thumbnails_2.webp)](https://www.youtube.com/watch?v=321RVhF8ok8)

+ 其他……
  + 等待你发掘，有新的想法，请给我提交一下issue


### 配置要求
+ 硬件要求


| 项目 | 最低配置 | 推荐配置        | 理想配置        |
| ---- | -------- | --------------- | --------------- |
| CPU  | 4 核     | 6 到 8 核       | 8 核及以上      |
| RAM  | 8 GB     | 16 GB            | 16 GB 及以上    |
| GPU  | 非必须   | 12 GB 显存及以上 | 16 GB 显存及以上 |


+ 软件要求
  + Windows11 或者 macOS 11.0 或者更高版本，以及各主流linux发行版本
  + Python 3.11
    + [windows] https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    + [mac homebrew] brew install python@3.11
  + Node.js 24
    + [windows] https://nodejs.org/dist/v24.21.0/node-v24.21.0-x64.msi
    + [mac homebrew] brew install node
  + uv 0.12
    + pip install uv
  + yt-dlp
    + pip install yt-dlp
  + ffmpeg ffprobe >=v7
    + 只是用了ffmpeg以及ffprobe命令行方式，没有用太复杂的功能或者自定义的滤镜
    + [windows] https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z
    + [mac homebrew] brew install ffmpeg

### 部署说明

+ 直接部署

  + 如果是windows，请在完成“软件要求”中的相关软件后，直接运行根目录中的start.bat
  + 如果是mac或者linux系统，请在完成“软件要求”中的相关软件后，直接运行根目录中的start.sh
  + 关于 start.bat 或者 start.sh 中的参数：

    + 参数列表
```
    start.xxx --help
      usage: -c [-h] [--mode {auto,cpu,cuda,mac}] [--check] [--reinstall] [--host HOST] [--backend-port BACKEND_PORT] [--frontend-port FRONTEND_PORT]

      Initialize and start VideoPrinterTurbo locally.

      options:
        -h, --help            show this help message and exit
        --mode {auto,cpu,cuda,mac}
        --check               Check prerequisites without installing or starting services.
        --reinstall           Run dependency installation again.
        --host HOST           IPv4 address for both services and the browser API URL (default: 127.0.0.1).
        --backend-port BACKEND_PORT
        --frontend-port FRONTEND_PORT
---------------------------------------------------------------------------------------
        --mode {auto,cpu,cuda,mac}
          auto 让启动脚本自己选择
          cpu 使用CPU方式启动
          cuda 在安装了NVIDIA CUDA的机器上面运行
          mac 在安装有 apple silicon 的系统上面运行
        --host HOST
          如果不使用此选项，那么默认绑定的ip地址是127.0.0.1
          在网络环境下面使用此软件的时候，必须绑定可访问的ip地址才可以，比如：
             我的服务器地址是：192.168.0.101，那么就可以使用 start.xxx --host 192.168.0.101，然后，然后在网络中其他机器中使用：
             http://192.168.0.101:5173，即可打开界面
          【备注：如果是本地部署运行，本地访问，无需在意这个选项】
        --backend-port
          后台的端口，默认是8080，如果需要修改，使用此选项
        --frontend-port
          前天的端口，默认是5173，如果需要修改，使用此选项
```
+ Docker方式
  + 【后续提供】

### 教程 

+ 如何配置 VideoPrinterTurbo
	+ 
+ 开始第一个任务

### 后续计划
+ 有其他的需求，给我提交一下issue


### 感谢

+ https://github.com/yt-dlp/yt-dlp
+ https://github.com/openai/whisper
+ https://github.com/streichgeorg/python-audio-separator

