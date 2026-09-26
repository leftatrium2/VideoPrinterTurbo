import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AddTask from './AddTask.vue'

const route = vi.hoisted(() => ({ query: {} as Record<string, string> }))

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))

vi.mock('element-plus', () => ({
  ElMessage: { error: vi.fn(), success: vi.fn(), warning: vi.fn() },
  ElPopover: { template: '<div><slot name="reference" /><slot /></div>' },
}))

vi.mock('@element-plus/icons-vue', () => ({
  Download: {}, User: {}, EditPen: {}, Tickets: {}, Bell: {}, Film: {}, Share: {}, Promotion: {},
  QuestionFilled: {}, Upload: {}, Document: {}, Link: {}, VideoPlay: {}, VideoPause: {}, Close: {},
}))

const apiMocks = vi.hoisted(() => ({
  addTask: vi.fn(), updateTask: vi.fn(), checkTaskUrl: vi.fn(), getTaskDetail: vi.fn(),
  getTtsVoicePreview: vi.fn(), ttsPreviewUrl: vi.fn(), uploadBgm: vi.fn(), uploadMaterial: vi.fn(),
  uploadTaskVideo: vi.fn(), getAsrLang: vi.fn(),
  getTaskConfig: vi.fn(),
}))

vi.mock('@/services/api', () => ({ ...apiMocks }))

const ElInputStub = defineComponent({
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: '<div><input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" /><slot name="append" /><slot /></div>',
})

const ElCheckboxStub = defineComponent({
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
})

const stubs = {
  'el-select': true, 'el-option': true, 'el-input': ElInputStub, 'el-checkbox': ElCheckboxStub,
  'el-button': { template: '<button><slot /></button>' }, 'el-slider': true, 'el-upload': true, 'el-icon': true,
}

describe('AddTask', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    route.query = {}
    apiMocks.getTaskConfig.mockResolvedValue({
    asr: [], tts: [], subtitle: [], bgm: [],
    material: { source: [], splicing: [], transition: [], ratio: [] },
    })
    apiMocks.checkTaskUrl.mockResolvedValue({ code: 0, msg: 'success', data: {} })
  })

  it.each(['top-center', 'center', 'bottom-center', 'custom'])('saves subtitle position %s when editing', async (position) => {
    route.query = { task_id: 'task-123' }
    apiMocks.getTaskDetail.mockResolvedValue({
      task_url: 'https://example.com/video',
      tts_speed: 1, tts_volume: 1,
      subtitle_position: 'bottom-center', subtitle_font_color: 0xffffff,
      subtitle_border_color: 0, video_material_keyword: '',
    })
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()

    const select = wrapper.findAllComponents({ name: 'el-select' })
      .find((item) => item.attributes('modelvalue') === 'bottom-center')!
    select.vm.$emit('update:modelValue', position)
    await flushPromises()
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()

    expect(apiMocks.updateTask).toHaveBeenCalledWith(expect.objectContaining({
      task_id: 'task-123', subtitle_position: position === 'custom' ? '70' : position,
    }))
  })

  it('does not expose a publish section when creating a task', async () => {
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()

    expect(wrapper.text()).not.toContain('addTask.publish')
    expect(wrapper.text()).not.toContain('addTask.publishSettings')
  })

  it('uses the checked proxy setting when checking a link', async () => {
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()

    await wrapper.findAll('input')[0].setValue('https://example.com/video')
    await wrapper.findAll('input')[1].setValue(true)
    await wrapper.findAll('button')[0].trigger('click')

    expect(apiMocks.checkTaskUrl).toHaveBeenCalledWith('https://example.com/video', true)
  })
})
