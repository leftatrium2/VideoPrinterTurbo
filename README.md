<div align="center">
<h1 align="center">VideoPrinterTurbo<img src="doc/VideoPrinterTurbo.png"></h1>
<br>
<h3>English | <a href="README_cn.md">简体中文</a></h3>
<br>
</div>
*** 🎉 Version 1.0.1 is officially released! Batch downloads now support up to 100 links. Paste links one at a time or upload a text file.*** 

### Latest version

[[macOS]](https://github.com/leftatrium2/VideoPrinterTurbo/releases/download/v1.0.1/VideoPrinterTurbo-1.0.1-macos-arm64.zip) Apple Silicon version

*** After unzip, run directly. ***

[[windows]](https://github.com/leftatrium2/VideoPrinterTurbo/releases/download/v1.0.1/VideoPrinterTurbo-1.0.1-windows-x64.exe)

*** run directly ***

*** Built with love in my spare time. If you find it useful, a free ⭐ would mean a lot! If something doesn’t work, please open an issue and let me know.* **


### A free video downloader with AI subtitle translation, dubbing, and video repurposing features.
```
VideoPrinterTurbo Usage Notice and Disclaimer

VideoPrinterTurbo provides only video processing and assisted content creation features. It does not grant any rights to use third-party content. Users must ensure that their source materials and how they use them are lawful, obtain any necessary permissions, and comply with the rules of the relevant platforms. Creating derivative works, crediting the source, or using content for non-commercial purposes does not automatically exempt users from liability for infringement. This tool is provided as is, without any guarantee of the accuracy, legality, or suitability of its output. Users must review the output themselves before publishing it. Users bear liability under applicable law for their own unlawful or infringing conduct. This disclaimer does not exclude or limit any liability of the developers or providers that cannot legally be excluded or limited.
```

### What can VideoPrinterTurbo do?

+ Video downloading

  + VideoPrinterTurbo uses yt-dlp to download videos from most video websites.

    See the supported sites list: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

  + For videos that cannot be downloaded, VideoPrinterTurbo offers a convenient plugin mechanism.

+ AI video translation

  + Pipeline: Download → ASR → LLM rewriting → Subtitle configuration → Final output

#### Original video:

[![Watch the demo](doc/thumbnails.webp)](https://www.youtube.com/watch?v=E7YiKBeOneo&t=1s)

#### With translated subtitles:

[![Watch the demo](doc/thumbnails.webp)](https://www.youtube.com/watch?v=AiSW3_SyaKs)

+ AI video redubbing

#### With translated subtitles and new dubbing:

[![Watch the demo](doc/thumbnails.webp)](https://www.youtube.com/watch?v=08dmRF8JVaI)

+ Full video footage replacement

#### With translated subtitles, new dubbing, and replacement footage:

[![Watch the demo](doc/thumbnails_2.webp)](https://www.youtube.com/watch?v=321RVhF8ok8)

+ And more…
  + Explore other possibilities. If you have a new idea, please open an issue.

### System Requirements

+ Hardware requirements

| Component | Minimum | Recommended | Ideal |
| --------- | ------- | ----------- | ----- |
| CPU | 4 cores | 6–8 cores | 8 cores or more |
| RAM | 12 GB | 16 GB | 16 GB or more |
| GPU | Optional | 12 GB VRAM or more | 16 GB VRAM or more |

+ Software requirements
  + Windows 10 or later (64-bit, x64 architecture)
  + macOS 24 or later (Apple Silicon)

+ How to use
  + Download the latest release package for your operating system.
  + On Windows, run `VideoPrinterTurbo-x.x.x-windows-x64.exe` directly.
  + On macOS, extract `VideoPrinterTurbo-x.x.x-macos-arm64.zip`, then run `VideoPrinterTurbo`.

### Quick Start

+ Download a video
  + Find the video's playback page, for example: https://www.youtube.com/watch?v=E7YiKBeOneo&t=6s
  + Copy the URL, open VideoPrinterTurbo, click **Add Task**, and paste the URL into **Video URL**.
  + ![Enter a video URL](doc/en/quick_start_1.png)
  + Click **Start Task**.
  + Open **Task List**, refresh, and wait for the task to finish. The red box highlights the downloaded video.
  + ![Find the downloaded video](doc/en/quick_start_2.png)

+ Download a video through a proxy
  + Configure the proxy.
  + ![Configure the proxy](doc/en/quick_start_proxy_config.png)
  + Enable **Use Proxy for Download**, then click **Start Task**. The remaining steps are the same as above.
  + ![Enable proxy downloading](doc/en/quick_start_3.png)

+ Download a video and add translated subtitles
  + Use this workflow to add translated subtitles to a video.
  + Step 1: Configure ASR.
  + ![Configure ASR](doc/en/quick_start_asr_config.png)
  + Step 2: Configure the LLM.
  + ![Configure the LLM](doc/en/quick_start_llm_config.png)
  + Step 3: Add a task as follows.
  + 3.1 Enter the video URL.
  + ![Enter the video URL](doc/en/quick_start_subtitle_1.png)
  + 3.2 Select **Audio to Text**.
  + ![Select audio transcription](doc/en/quick_start_subtitle_2.png)
  + 3.3 Select **LLM Rewriting**.
  + ![Select LLM rewriting](doc/en/quick_start_subtitle_3.png)
  + 3.4 Select **Output to Subtitles**.
  + ![Select subtitle output](doc/en/quick_start_subtitle_4.png)
  + Click **Start Task**.
  + Wait for the task to finish in **Task List**. The processed video file is available at the **Local Path**.

### Tutorials

+ How to configure VideoPrinterTurbo
  + ASR configuration
    + What is ASR?
      + **ASR (Automatic Speech Recognition)** uses artificial intelligence and machine learning to automatically convert human speech into written text or commands.
      + VideoPrinterTurbo uses ASR to transcribe speech from videos, preparing the text for subsequent LLM and TTS processing.
    + How do I configure it?
      + **Note:** You only need to configure one service among the ASR configuration tabs. Select that service when creating a task; you do not need to configure every service.
    + What is **Whisper (Local ASR)**, and how do I configure it?
      + Whisper is an open-source speech recognition and transcription model from OpenAI. **Whisper (Local ASR)** means downloading the Whisper model directly to your local machine.
      + OpenAI Whisper (CPU)
        + Uses the official `whisper-large-v3-turbo` model.
        + CPU processing is slow and is provided for compatibility. It is not recommended for production workloads.
        + Model files require more than 5 GB of disk space.
      + MLX Whisper (recommended for Apple Silicon)
        + Uses `mlx-community/whisper-large-v3-mlx`.
        + Model files require more than 5 GB of disk space.
        + An M-series Pro processor is recommended.
        + At least 16 GB of unified memory is recommended.
      + Faster Whisper (recommended for NVIDIA GPUs)
        + Uses `Systran/faster-whisper-large-v3`.
        + At least 12 GB of VRAM and an RTX 3080 or better are recommended.
        + At least 5 GB of disk space is recommended for the model files.
      + ![Local ASR configuration](doc/en/asr_config_1.png)
    + What is **Whisper (Remote ASR)**, and how do I configure it?
      + **Whisper (Remote ASR)** refers to a self-hosted Whisper service running on a server. This project supports deployment with vLLM or whisper.cpp.
      + Enter the address of your deployed service. For example, if whisper.cpp runs on server `192.168.0.1` at port `8004`, enter `http://192.168.0.1:8004/inference`.
      + ![Remote ASR configuration](doc/en/asr_config_2.png)
    + What is **Tencent Cloud ASR**, and how do I configure it?
      + Enter the ID and key provided by the cloud provider.
      + ![Tencent Cloud ASR configuration](doc/en/asr_config_3.png)
      + Configure the other cloud services in the same way as Tencent Cloud ASR.
  + LLM configuration
    + The LLM rewrites subtitle files and determines the content used in subsequent output, including AI-generated speech (TTS).
    + This project uses an OpenAI-compatible API format. The Claude API format is not supported.
    + The following example uses the official DeepSeek API.
    + ![LLM configuration](doc/en/llm_config.png)
  + Stock media configuration
    + What is stock media used for?
      + For some derivative video workflows, such as quickly creating content similar to a short video you made with MoneyPrinterTurbo, you can use the stock media feature.
      + When adding a task, enable video footage replacement and enter video keywords. VideoPrinterTurbo searches the configured sites for matching stock media and uses it to replace the original video footage.
      + **Note:** If you leave the keywords blank, VideoPrinterTurbo uses the LLM (which must be configured) to extract a fixed number of keywords from the current subtitle file. These keywords may be inaccurate.
    + How do I configure it?
      + This project supports API keys for Pexels and Pixabay.
      + Apply for an API key on the corresponding website.
    + ![Stock media configuration](doc/en/material_config.png)
  + TTS configuration
    + What is TTS?
      + **TTS (Text-to-Speech)**, also known as speech synthesis, converts written text into natural, audible human speech.
      + You can think of it as the reverse of ASR. In VideoPrinterTurbo, TTS converts subtitles extracted by ASR and processed by the LLM back into speech, which is then merged into the final video.
    + How do I configure it?
      + Choose the service you want under **TTS Server**. Azure TTS V2 is recommended for its speed and fluency. When setting up Azure TTS V2, choose the **service region** closest to you and enter it correctly in the configuration.
    + ![TTS configuration](doc/en/tts_config_1.png)
  + Proxy configuration
    + HTTP and SOCKS5 proxies are supported.
    + **Note:** Once a proxy is configured, you can enable it when adding a task. When enabled, all network operations use the configured proxy service.
    + ![Proxy configuration](doc/en/proxy_config.png)

+ Start your first task
  + After completing the configuration, start with the simplest task: downloading a video.
  + Click **Add Task**.
  + Enter a link in the video download section, for example: https://www.youtube.com/watch?v=mUw27wG7uFA
  + ![Enter a video URL](doc/en/add_task_1.png)
  + Click **Check Link** to check whether the link is available. **Note:** If the video requires a proxy to download, enable the proxy option before checking the link as well.
  + ![Check the video link](doc/en/add_task_2.png)
  + Once the check passes, click **Start Task** at the bottom to start downloading.
  + ![Start the download task](doc/en/add_task_3.png)
  + Wait for the task to finish. When its status shows that it is completed, the local path points to the downloaded video.

### Future Plans

+ If you have other needs, please open an issue.

### Acknowledgments

+ https://github.com/yt-dlp/yt-dlp
+ https://github.com/openai/whisper
+ https://github.com/streichgeorg/python-audio-separator
