<div align="center">
<h1 align="center">VideoPrinterTurbo<img src="doc/VideoPrinterTurbo.png"></h1>
<br>
<h3>English | <a href="README-cn.md">简体中文</a></h3>
<br>


### A sister project to MoneyPrinterTurbo
### MoneyPrinterTurbo generates videos; VideoPrinterTurbo helps you create derivative videos
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

Click the thumbnail to watch the demo on YouTube.

#### With translated subtitles:

[![Watch the demo](doc/thumbnails.webp)](https://www.youtube.com/watch?v=AiSW3_SyaKs)

Click the thumbnail to watch the demo on YouTube.

+ AI video redubbing

#### With translated subtitles and new dubbing:

[![Watch the demo](doc/thumbnails.webp)](https://www.youtube.com/watch?v=08dmRF8JVaI)

Click the thumbnail to watch the demo on YouTube.

+ Full video footage replacement

#### With translated subtitles, new dubbing, and replacement footage:

[![Watch the demo](doc/thumbnails_2.webp)](https://www.youtube.com/watch?v=321RVhF8ok8)

Click the thumbnail to watch the demo on YouTube.

+ And more…
  + Explore other possibilities. If you have a new idea, please open an issue.

### Tutorials

+ How to configure VideoPrinterTurbo
+ Start your first task

### Deployment Instructions

+ Direct deployment
+ Docker deployment

### Future Plans

+ Future development will be guided by user feedback. If you have other needs, please open an issue.

### Acknowledgments

+ https://github.com/yt-dlp/yt-dlp
+ https://github.com/openai/whisper
+ https://github.com/streichgeorg/python-audio-separator
