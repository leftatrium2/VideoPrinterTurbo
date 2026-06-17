<template>
  <div class="add-task-page">

    <!-- Section 1: 下载视频 (no checkbox — always required) -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><Download /></el-icon>
          <span class="section-title">下载视频</span>
        </div>
        <HelpPopover content="填入视频播放页的URL地址，然后点击「检查链接」，如果弹出成功后，再继续往下进行，如果提示无法下载，可以在 GitHub 上面提 issue 给作者。" />
      </div>
      <div class="section-body">
        <div class="field-label">视频链接</div>
        <el-input v-model="form.task_url" placeholder="请输入抖音/Bilibili/Youtube视频链接" size="large">
          <template #append>
            <el-button :icon="Link" @click="handleCheckLink">检查链接</el-button>
          </template>
        </el-input>
      </div>
    </div>

    <!-- Section 2: 音频转文字 -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><User /></el-icon>
          <el-checkbox v-model="enabled.transcription" class="section-toggle" />
          <span class="section-title">音频转文字</span>
        </div>
        <HelpPopover content="有两种方式将视频中的语音转换为文字：「从字幕提取」适合 YouTube 等带有自动字幕的视频网站；「从ASR转换」直接提取视频中的语音并转为文字（除非是 YouTube 视频，否则建议使用 ASR 方式，避免出错）。" />
      </div>
      <div class="section-body">
        <div class="field-label">选择音频转换方式</div>
        <el-select v-model="form.transcription_mode" class="full-width">
          <el-option label="Whisper Large v3 (推荐)" value="whisper-large-v3" />
          <el-option label="从字幕提取" value="subtitle" />
          <el-option label="从ASR转换" value="asr" />
        </el-select>
      </div>
    </div>

    <!-- Section 3: LLM 改写 -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><EditPen /></el-icon>
          <el-checkbox v-model="enabled.llm" class="section-toggle" />
          <span class="section-title">LLM 改写</span>
        </div>
        <HelpPopover content="选择 LLM 改写，并将提示词填入，会将当前提取到的文字经过 LLM 改写后重新输出。" />
      </div>
      <div class="section-body">
        <div class="field-label">LLM 提示词 (Prompt)</div>
        <el-input
          v-model="form.llm_prompt"
          type="textarea"
          :rows="4"
          placeholder="请输入改写要求，例如：请将以下文案改写成幽默风趣的短视频脚本..."
        />
      </div>
    </div>

    <!-- Section 4: 输出到语音 -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><User /></el-icon>
          <el-checkbox v-model="enabled.voice_output" class="section-toggle" />
          <span class="section-title">输出到语音</span>
        </div>
        <HelpPopover content="「输出到语音」将把处理好的文字通过 TTS 方式转换为语音，并合并到新的视频中。" />
      </div>
      <div class="section-body">
        <div class="field-label">TTS 服务</div>
        <el-select v-model="form.tts_service" class="full-width">
          <el-option label="Edge TTS" value="edge-tts" />
          <el-option label="Azure TTS V1" value="azure-v1" />
          <el-option label="Azure TTS V2" value="azure-v2" />
          <el-option label="SiliconFlow TTS" value="siliconflow" />
          <el-option label="Google Gemini TTS" value="gemini" />
          <el-option label="Xiaomi MiMo TTS" value="mimo" />
        </el-select>

        <div class="voice-role-row">
          <div class="voice-role-field">
            <div class="field-label">声音角色</div>
            <el-select v-model="form.tts_voice" class="full-width">
              <el-option label="zh-CN-XiaoXiaoNeural" value="zh-CN-XiaoXiaoNeural" />
              <el-option label="zh-CN-YunXiNeural" value="zh-CN-YunXiNeural" />
              <el-option label="zh-CN-XiaoYiNeural" value="zh-CN-XiaoYiNeural" />
            </el-select>
          </div>
          <el-button class="test-voice-btn" @click="handleTestVoice">
            <el-icon><VideoPlay /></el-icon>测试
          </el-button>
        </div>

        <div class="sliders-row">
          <div class="slider-group">
            <div class="field-label">语音音量 ({{ form.tts_volume.toFixed(1) }})</div>
            <el-slider v-model="form.tts_volume" :min="1.0" :max="2.0" :step="0.1" />
          </div>
          <div class="slider-group">
            <div class="field-label">速度 ({{ form.tts_speed.toFixed(1) }})</div>
            <el-slider v-model="form.tts_speed" :min="1.0" :max="2.0" :step="0.1" />
          </div>
        </div>
      </div>
    </div>

    <!-- Section 5: 输出到字幕 -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><Tickets /></el-icon>
          <el-checkbox v-model="enabled.subtitle_output" class="section-toggle" />
          <span class="section-title">输出到字幕</span>
        </div>
        <HelpPopover content="「输出到字幕」原视频中的语音不动，只是将处理好的文本转为字幕，添加到新的视频中。" />
      </div>
      <div class="section-body">
        <div class="form-grid-2">
          <div>
            <div class="field-label">字体</div>
            <el-select v-model="form.subtitle_font" class="full-width">
              <el-option label="思源黑体 Bold" value="SourceHanSans-Bold" />
              <el-option label="思源黑体 Regular" value="SourceHanSans-Regular" />
              <el-option label="微软雅黑 Bold" value="MicrosoftYaHeiBold.ttc" />
              <el-option label="微软雅黑 Regular" value="MicrosoftYaHeiNormal.ttc" />
              <el-option label="Charm Bold" value="Charm-Bold.ttf" />
              <el-option label="Charm Regular" value="Charm-Regular.ttf" />
            </el-select>
          </div>
          <div>
            <div class="field-label">位置</div>
            <el-select v-model="form.subtitle_position" class="full-width">
              <el-option label="底部居中（推荐）" value="bottom-center" />
              <el-option label="顶部居中" value="top-center" />
              <el-option label="中间" value="center" />
              <el-option label="自定义（70，离顶部70%位置）" value="custom" />
            </el-select>
          </div>
        </div>

        <div v-if="form.subtitle_position === 'custom'" class="mt-12">
          <div class="field-label">自定义位置（离顶部百分比）</div>
          <el-input v-model="form.subtitle_position_custom" style="width: 200px" placeholder="70" />
        </div>

        <div class="color-row mt-12">
          <div class="color-group">
            <div class="field-label">字幕颜色</div>
            <div class="color-field">
              <input type="color" v-model="form.subtitle_color" class="color-swatch" />
              <span class="color-hex">{{ form.subtitle_color }}</span>
            </div>
          </div>
          <div class="color-group">
            <div class="field-label">描边颜色</div>
            <div class="color-field">
              <input type="color" v-model="form.subtitle_stroke_color" class="color-swatch" />
              <span class="color-hex">{{ form.subtitle_stroke_color }}</span>
            </div>
          </div>
        </div>

        <div class="mt-12">
          <div class="field-label">字幕大小</div>
          <el-slider v-model="form.subtitle_size" :min="30" :max="100" :step="1" show-tooltip />
        </div>
      </div>
    </div>

    <!-- Section 6: 背景音乐 -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><Bell /></el-icon>
          <el-checkbox v-model="enabled.bgm" class="section-toggle" />
          <span class="section-title">背景音乐</span>
        </div>
        <HelpPopover content="选择相关的背景音乐后，将会将此背景音乐合并到新的视频中。" />
      </div>
      <div class="section-body">
        <div class="field-label">选择 BGM 库</div>
        <el-select v-model="form.bgm_library" class="full-width">
          <el-option label="推荐轻快背景乐" value="light" />
          <el-option label="推荐舒缓背景乐" value="calm" />
          <el-option label="随机背景音乐" value="random" />
          <el-option label="无背景音乐" value="none" />
        </el-select>

        <div class="bgm-layout mt-12">
          <div class="bgm-upload">
            <el-upload
              drag
              :auto-upload="false"
              accept="audio/*"
              :on-change="handleBgmFileChange"
              :file-list="bgmFileList"
              :limit="1"
            >
              <el-icon class="upload-icon"><Document /></el-icon>
              <div class="upload-text">点击上传本地音频文件</div>
            </el-upload>
          </div>
          <div class="bgm-volume">
            <div class="field-label">背景音乐音量</div>
            <div class="volume-row">
              <span class="vol-icon">🔉</span>
              <el-slider v-model="form.bgm_volume" :min="0" :max="1" :step="0.05" class="vol-slider" />
              <span class="vol-icon">🔊</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Section 7: 视频覆盖 -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><Film /></el-icon>
          <el-checkbox v-model="enabled.video_overlay" class="section-toggle" />
          <span class="section-title">视频覆盖</span>
        </div>
        <HelpPopover content="点击「视频覆盖」复选框后，将从 Pexels 等网站获取短视频进行拼接。" />
      </div>
      <div class="section-body">
        <div class="form-grid-3">
          <div>
            <div class="field-label">视频源</div>
            <el-select v-model="form.video_source" class="full-width">
              <el-option label="Pexels" value="pexels" />
              <el-option label="Pixabay" value="pixabay" />
              <el-option label="本地文件" value="local" />
            </el-select>
          </div>
          <div>
            <div class="field-label">拼接模式</div>
            <el-select v-model="form.video_concat_mode" class="full-width">
              <el-option label="顺序拼接" value="sequential" />
              <el-option label="随机拼接（推荐）" value="random" />
            </el-select>
          </div>
          <div>
            <div class="field-label">转场模式</div>
            <el-select v-model="form.video_transition" class="full-width">
              <el-option label="无转场" value="none" />
              <el-option label="随机转场" value="random" />
              <el-option label="渐入" value="fadein" />
              <el-option label="渐出" value="fadeout" />
              <el-option label="淡入淡出" value="fadeinout" />
              <el-option label="滑动入" value="slidein" />
              <el-option label="滑动出" value="slideout" />
            </el-select>
          </div>
        </div>

        <div v-if="form.video_source === 'local'" class="upload-zone mt-12">
          <el-upload drag :auto-upload="false" accept="video/*" :on-change="handleVideoFileChange" :file-list="videoFileList" multiple>
            <el-icon class="upload-icon"><Upload /></el-icon>
            <div class="upload-text">点击上传本地视频文件</div>
            <div class="upload-hint">支持 MP4、MOV、AVI 等格式，可多选</div>
          </el-upload>
        </div>

        <div class="form-grid-3 mt-12">
          <div>
            <div class="field-label">视频比例</div>
            <el-select v-model="form.video_aspect" class="full-width">
              <el-option label="9:16 (竖屏)" value="9:16" />
              <el-option label="16:9 (横屏)" value="16:9" />
            </el-select>
          </div>
          <div>
            <div class="field-label">视频片段最大时长(秒)</div>
            <el-input v-model.number="form.video_fragment_duration" type="number" :min="2" :max="30" class="full-width" />
          </div>
          <div>
            <div class="field-label">同时生成视频数量</div>
            <el-input v-model.number="form.video_count" type="number" :min="1" :max="5" class="full-width" />
          </div>
        </div>
      </div>
    </div>

    <!-- Section 8: 发布 -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><Share /></el-icon>
          <el-checkbox v-model="enabled.publish" class="section-toggle" />
          <span class="section-title">发布</span>
        </div>
        <HelpPopover content="此功能暂未开放。" />
      </div>
      <div class="section-body">
        <div class="field-label">发布设置 (JSON 配置或描述)</div>
        <el-input
          type="textarea"
          :rows="5"
          :model-value="publishPlaceholder"
          readonly
          class="publish-textarea"
        />
      </div>
    </div>

    <!-- Submit -->
    <div class="submit-area">
      <el-button type="primary" size="large" :loading="submitting" class="submit-btn" @click="handleSubmit">
        <el-icon><Promotion /></el-icon>
        开始任务
      </el-button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { defineComponent, reactive, ref, h } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElPopover } from 'element-plus'
import type { UploadFile } from 'element-plus'
import {
  Download, User, EditPen, Tickets, Bell, Film, Share, Promotion,
  QuestionFilled, Upload, Document, Link, VideoPlay,
} from '@element-plus/icons-vue'
import { addTask } from '@/services/api'

const router = useRouter()

/* -------- inline helper component for help popovers -------- */
const HelpPopover = defineComponent({
  props: { content: { type: String, required: true } },
  setup(props) {
    return () => h(ElPopover, { trigger: 'click', placement: 'bottom-end', width: 320 }, {
      reference: () => h('span', { class: 'help-link' }, [
        h(QuestionFilled, { style: { fontSize: '13px', marginRight: '3px' } }),
        '使用说明',
      ]),
      default: () => h('p', { style: { lineHeight: '1.7', fontSize: '13px' } }, props.content),
    })
  },
})

/* -------- section enable flags -------- */
const enabled = reactive({
  transcription: true,
  llm: false,
  voice_output: true,
  subtitle_output: false,
  bgm: true,
  video_overlay: true,
  publish: false,
})

/* -------- form state -------- */
const form = reactive({
  task_url: '',
  transcription_mode: 'whisper-large-v3',
  llm_prompt: '',
  tts_service: 'edge-tts',
  tts_voice: 'zh-CN-XiaoXiaoNeural',
  tts_volume: 1.0,
  tts_speed: 1.0,
  subtitle_font: 'SourceHanSans-Bold',
  subtitle_position: 'bottom-center',
  subtitle_position_custom: '70',
  subtitle_color: '#ffffff',
  subtitle_stroke_color: '#000000',
  subtitle_size: 60,
  bgm_library: 'light',
  bgm_volume: 0.5,
  video_source: 'pexels',
  video_concat_mode: 'sequential',
  video_transition: 'fadeinout',
  video_aspect: '9:16',
  video_fragment_duration: 10,
  video_count: 1,
})

const submitting = ref(false)
const bgmFileList = ref<UploadFile[]>([])
const videoFileList = ref<UploadFile[]>([])

const publishPlaceholder = `{ 'platform': 'douyin', 'auto_publish': true, ... }`

function handleCheckLink() {
  if (!form.task_url.trim()) { ElMessage.warning('请先输入视频链接'); return }
  ElMessage.info('功能开发中')
}

function handleTestVoice() { ElMessage.info('功能开发中') }

function handleBgmFileChange(file: UploadFile) { bgmFileList.value = [file] }
function handleVideoFileChange(file: UploadFile) { videoFileList.value = [...videoFileList.value, file] }

async function handleSubmit() {
  if (!form.task_url.trim()) { ElMessage.warning('请输入视频链接'); return }
  try {
    submitting.value = true
    await addTask({
      task_url: form.task_url,
      transcription_mode: enabled.transcription ? form.transcription_mode : undefined,
      llm_enabled: enabled.llm,
      llm_prompt: enabled.llm ? form.llm_prompt : undefined,
      output_mode: enabled.voice_output ? 'voice' : enabled.subtitle_output ? 'subtitle' : undefined,
      tts_service: enabled.voice_output ? form.tts_service : undefined,
      tts_voice: enabled.voice_output ? form.tts_voice : undefined,
      tts_speed: enabled.voice_output ? form.tts_speed : undefined,
      tts_volume: enabled.voice_output ? form.tts_volume : undefined,
      subtitle_font: enabled.subtitle_output ? form.subtitle_font : undefined,
      subtitle_position: enabled.subtitle_output ? form.subtitle_position : undefined,
      subtitle_position_custom: (enabled.subtitle_output && form.subtitle_position === 'custom') ? form.subtitle_position_custom : undefined,
      subtitle_color: enabled.subtitle_output ? form.subtitle_color : undefined,
      subtitle_stroke_color: enabled.subtitle_output ? form.subtitle_stroke_color : undefined,
      subtitle_size: enabled.subtitle_output ? form.subtitle_size : undefined,
      bgm_type: enabled.bgm ? form.bgm_library : 'none',
      bgm_volume: enabled.bgm ? form.bgm_volume : undefined,
      video_source: enabled.video_overlay ? form.video_source : undefined,
      video_concat_mode: enabled.video_overlay ? form.video_concat_mode : undefined,
      video_transition: enabled.video_overlay ? form.video_transition : undefined,
      video_aspect: form.video_aspect,
      video_fragment_duration: form.video_fragment_duration,
      video_count: form.video_count,
    })
    ElMessage.success('任务已创建')
    router.push('/tasks')
  } catch {
    ElMessage.error('创建失败，请重试')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.add-task-page {
  padding: 20px;
  max-width: 860px;
}

/* ─── Section cards ─── */
.section-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: var(--shadow-card);
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 13px 20px;
  border-bottom: 1px solid var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-icon { font-size: 15px; color: var(--color-primary); }

.section-toggle { margin: 0; }

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* help popover trigger — applies to inline component render output */
:deep(.help-link) {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  flex-shrink: 0;
  transition: color 0.2s;
}
:deep(.help-link:hover) { color: var(--color-primary); }

.section-body { padding: 16px 20px 20px; }

/* ─── Field labels ─── */
.field-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-regular);
  margin-bottom: 6px;
}

.full-width { width: 100%; }

.mt-12 { margin-top: 12px; }

/* ─── 输出到语音 ─── */
.voice-role-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin-top: 12px;
}

.voice-role-field { flex: 1; }

.test-voice-btn {
  flex-shrink: 0;
  margin-bottom: 0;
}

.sliders-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 14px;
}

.slider-group {}

/* ─── 输出到字幕 ─── */
.form-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.color-row {
  display: flex;
  gap: 32px;
}

.color-group {}

.color-field {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
}

.color-swatch {
  width: 32px;
  height: 32px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 2px;
  cursor: pointer;
}

.color-hex {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-family: 'Courier New', monospace;
}

/* ─── 背景音乐 ─── */
.bgm-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

.bgm-upload {
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  overflow: hidden;
}

.bgm-volume {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-top: 4px;
}

.volume-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

.vol-icon { font-size: 16px; flex-shrink: 0; }
.vol-slider { flex: 1; }

.upload-icon {
  font-size: 36px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.upload-text {
  font-size: 13px;
  color: var(--color-text-regular);
}

/* ─── 视频覆盖 ─── */
.form-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.upload-zone {
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  overflow: hidden;
}

.upload-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

/* ─── 发布 ─── */
.publish-textarea {
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

/* ─── Submit ─── */
.submit-area {
  display: flex;
  justify-content: center;
  padding: 24px 0 48px;
}

.submit-btn {
  min-width: 220px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1px;
}

/* ─── Element Plus overrides ─── */
:deep(.el-form-item) { margin-bottom: 0; }
:deep(.el-select) { width: 100%; }
:deep(.el-upload-dragger) { padding: 20px 16px; }
:deep(.el-upload-dragger .el-icon--upload) { margin: 0; }
</style>
