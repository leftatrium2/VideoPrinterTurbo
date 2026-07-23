# crawler request timeout (s)
REQUEST_TIME_OUT = 10  # Request timeout set to 10s
# downloader codec type
DOWNLOADER_CODEC_VIDEO_TYPE = 1
DOWNLOADER_CODEC_AUDIO_TYPE = 2
DOWNLOADER_CODEC_MUXER_TYPE = 3
# Configuration section
# Audio to Text
# Do not extract
TASK_CONFIG_ASR_FROM_NONE = 0
# Extract from subtitles
TASK_CONFIG_ASR_FROM_SUBTITLE = 1
# Local whisper
TASK_CONFIG_ASR_FROM_FASTER_WHISPER = 2
# Tencent Cloud ASR
TASK_CONFIG_ASR_FROM_TENCENT_CLOUD = 3
# XFYun ASR
TASK_CONFIG_ASR_FROM_XF_YUN = 4
# Aliyun ASR
TASK_CONFIG_ASR_FROM_ALIYUN = 5
# azure ASR
TASK_CONFIG_ASR_FROM_AZURE = 6
# bytedance ASR
TASK_CONFIG_ASR_FROM_BYTEDANCE = 7
# openai asr
TASK_CONFIG_ASR_FROM_OPENAI = 8
# Local whisper config
TASK_CONFIG_ASR_MLX_WHISPER = 1
TASK_CONFIG_ASR_FASTER_WHISPER = 2
TASK_CONFIG_ASR_OPENAI_WHISPER = 3
# tts engine server list
TTS_LIST_AZURE_TTS_V1 = 1
TTS_LIST_AZURE_TTS_V2 = 2
TTS_LIST_SILICON_FLOW_TTS = 3
TTS_LIST_GOOGLE_GEMINI_TTS = 4
# tts voice preview
TTS_CONFIG_PREVIEW = {
    "zh": "你好，这是一段试听音频",
    "en": "Hello, this is a sample audio file"
}
# tts whisper language list
TTS_WHISPER_LANGUAGES = [
    {"name": "英语", "value": "en"},
    {"name": "中文", "value": "zh"},
    {"name": "德语", "value": "de"},
    {"name": "西班牙语", "value": "es"},
    {"name": "俄语", "value": "ru"},
    {"name": "韩语", "value": "ko"},
    {"name": "法语", "value": "fr"},
    {"name": "日语", "value": "ja"},
    {"name": "葡萄牙语", "value": "pt"},
    {"name": "土耳其语", "value": "tr"},
    {"name": "波兰语", "value": "pl"},
    {"name": "加泰罗尼亚语", "value": "ca"},
    {"name": "荷兰语", "value": "nl"},
    {"name": "阿拉伯语", "value": "ar"},
    {"name": "瑞典语", "value": "sv"},
    {"name": "意大利语", "value": "it"},
    {"name": "印度尼西亚语", "value": "id"},
    {"name": "印地语", "value": "hi"},
    {"name": "芬兰语", "value": "fi"},
    {"name": "越南语", "value": "vi"},
    {"name": "希伯来语", "value": "he"},
    {"name": "乌克兰语", "value": "uk"},
    {"name": "希腊语", "value": "el"},
    {"name": "马来语", "value": "ms"},
    {"name": "捷克语", "value": "cs"},
    {"name": "罗马尼亚语", "value": "ro"},
    {"name": "丹麦语", "value": "da"},
    {"name": "匈牙利语", "value": "hu"},
    {"name": "泰米尔语", "value": "ta"},
    {"name": "挪威语", "value": "no"},
    {"name": "泰语", "value": "th"},
    {"name": "乌尔都语", "value": "ur"},
    {"name": "克罗地亚语", "value": "hr"},
    {"name": "保加利亚语", "value": "bg"},
    {"name": "立陶宛语", "value": "lt"},
    {"name": "拉丁语", "value": "la"},
    {"name": "毛利语", "value": "mi"},
    {"name": "马拉雅拉姆语", "value": "ml"},
    {"name": "威尔士语", "value": "cy"},
    {"name": "斯洛伐克语", "value": "sk"},
    {"name": "泰卢固语", "value": "te"},
    {"name": "波斯语", "value": "fa"},
    {"name": "拉脱维亚语", "value": "lv"},
    {"name": "孟加拉语", "value": "bn"},
    {"name": "塞尔维亚语", "value": "sr"},
    {"name": "阿塞拜疆语", "value": "az"},
    {"name": "斯洛文尼亚语", "value": "sl"},
    {"name": "卡纳达语", "value": "kn"},
    {"name": "爱沙尼亚语", "value": "et"},
    {"name": "马其顿语", "value": "mk"},
    {"name": "布列塔尼语", "value": "br"},
    {"name": "巴斯克语", "value": "eu"},
    {"name": "冰岛语", "value": "is"},
    {"name": "亚美尼亚语", "value": "hy"},
    {"name": "尼泊尔语", "value": "ne"},
    {"name": "蒙古语", "value": "mn"},
    {"name": "波斯尼亚语", "value": "bs"},
    {"name": "哈萨克语", "value": "kk"},
    {"name": "阿尔巴尼亚语", "value": "sq"},
    {"name": "斯瓦希里语", "value": "sw"},
    {"name": "加利西亚语", "value": "gl"},
    {"name": "马拉地语", "value": "mr"},
    {"name": "旁遮普语", "value": "pa"},
    {"name": "僧伽罗语", "value": "si"},
    {"name": "高棉语", "value": "km"},
    {"name": "修纳语", "value": "sn"},
    {"name": "约鲁巴语", "value": "yo"},
    {"name": "索马里语", "value": "so"},
    {"name": "南非荷兰语", "value": "af"},
    {"name": "奥克语", "value": "oc"},
    {"name": "格鲁吉亚语", "value": "ka"},
    {"name": "白俄罗斯语", "value": "be"},
    {"name": "塔吉克语", "value": "tg"},
    {"name": "信德语", "value": "sd"},
    {"name": "古吉拉特语", "value": "gu"},
    {"name": "阿姆哈拉语", "value": "am"},
    {"name": "意第绪语", "value": "yi"},
    {"name": "老挝语", "value": "lo"},
    {"name": "乌兹别克语", "value": "uz"},
    {"name": "法罗语", "value": "fo"},
    {"name": "海地克里奥尔语", "value": "ht"},
    {"name": "普什图语", "value": "ps"},
    {"name": "土库曼语", "value": "tk"},
    {"name": "新挪威语", "value": "nn"},
    {"name": "马耳他语", "value": "mt"},
    {"name": "梵语", "value": "sa"},
    {"name": "卢森堡语", "value": "lb"},
    {"name": "缅甸语", "value": "my"},
    {"name": "藏语", "value": "bo"},
    {"name": "他加禄语", "value": "tl"},
    {"name": "马尔加什语", "value": "mg"},
    {"name": "阿萨姆语", "value": "as"},
    {"name": "塔塔尔语", "value": "tt"},
    {"name": "夏威夷语", "value": "haw"},
    {"name": "林加拉语", "value": "ln"},
    {"name": "豪萨语", "value": "ha"},
    {"name": "巴什基尔语", "value": "ba"},
    {"name": "爪哇语", "value": "jw"},
    {"name": "巽他语", "value": "su"},
    {"name": "粤语", "value": "yue"}
]
# proxy server type
PROXY_CONFIG_TYPE_UNKNOWN = 0
PROXY_CONFIG_TYPE_HTTPS = 1
PROXY_CONFIG_TYPE_SOCKS5 = 2
# Video overlay - Video source
VIDEO_MATERIAL_FROM_LOCAL = "local"
VIDEO_MATERIAL_FROM_PEXELS = "pexels"
VIDEO_MATERIAL_FROM_PIXABAY = "pixabay"
# Video overlay - Splicing mode
VIDEO_MATERIAL_RANDOM_SPLICING = 1
VIDEO_MATERIAL_SEQUENTIAL_SPLICING = 2
# Video overlay - Transition mode
VIDEO_MATERIAL_TRANSITION_NO = 1
VIDEO_MATERIAL_TRANSITION_RANDOM = 2
VIDEO_MATERIAL_TRANSITION_GRADUAL_ENTRY = 3
VIDEO_MATERIAL_TRANSITION_GRADUAL_EXIT = 4
VIDEO_MATERIAL_TRANSITION_FADE_IN_OR_FADE_OUT = 5
VIDEO_MATERIAL_TRANSITION_SLIDE_IN = 6
VIDEO_MATERIAL_TRANSITION_SLIDE_OUT = 7
# Video overlay - Video aspect ratio
VIDEO_MATERIAL_SCREEN_RATIO_9_16 = 1
VIDEO_MATERIAL_SCREEN_RATIO_16_9 = 2
# Video overlay - Max clip duration (seconds)
# Video overlay - Number of videos to generate
# error code for successful
GLOBAL_SUCC = 0
# global error code 1000-1099
GLOBAL_ERR_UNKNOWN = 1000
GLOBAL_ERR_PARAMETER_EMPTY = 1001
GLOBAL_ERR_PATH_NOT_FOUND = 1002
GLOBAL_ERR_YT_DLP_NOT_INSTALLED = 1003
# task module
TASK_ERR_UNKNOWN = 1100
TASK_ERR_CHECK_URL = 1101
TASK_ERR_TASK_ID_EMPTY = 1102
TASK_ERR_TASK_NOT_FOUND = 1103
TASK_CONFIG_ERR_CONFIG_FILE = 1110
TASK_CONFIG_ERR_INVALID_FILE_FORMAT = 1111
TASK_CONFIG_ERR_FILE_SIZE_LIMIT_EXCEEDED = 1112
# config module
TTS_CONFIG_ERR_UNKNOWN = 1200
TTS_CONFIG_ERR_ENGINE_NOT_FOUND = 1201
TTS_CONFIG_ERR_VOICE_NOT_FOUND = 1202
TTS_CONFIG_ERR_VOICE_TEXT_NOT_FOUND = 1203
TTS_CONFIG_ERR_PREVIEW_FILE_EMPTY = 1204
TTS_CONFIG_ERR_PREVIEW_FILE_NOT_EXISTS = 1205
TTS_CONFIG_ERR_MATERIAL_PARAM = 1206
