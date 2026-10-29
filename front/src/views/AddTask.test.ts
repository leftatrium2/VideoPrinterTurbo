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
  'el-select': defineComponent({ name: 'el-select', props: ['modelValue'], emits: ['update:modelValue'], template: '<div :modelvalue="modelValue"><slot /></div>' }), 'el-option': true, 'el-input': ElInputStub, 'el-checkbox': ElCheckboxStub,
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
    apiMocks.checkTaskUrl.mockResolvedValue({ code: 0, msg: 'success', data: [] })
    apiMocks.getAsrLang.mockResolvedValue({ code: 0, msg: 'success', data: [
      { lang: 'Auto', value: '0' }, { lang: 'English', value: 'en' },
    ] })
  })

  it.each([false, true])('submits the selected dubbing strategy when editing=%s', async (editing) => {
    apiMocks.getTaskConfig.mockResolvedValue({
      asr: [], tts: [], subtitle: [], bgm: [],
      tts_dubbing_strategy: [{ name: 'None', value: 0 }, { name: 'Timeline first', value: 1 }, { name: 'Natural first', value: 2 }],
      material: { source: [], splicing: [], transition: [], ratio: [] },
    })
    if (editing) {
      route.query = { task_id: 'task-dubbing' }
      apiMocks.getTaskDetail.mockResolvedValue({
        task_url: 'https://example.com/video', audio_rewrite_type: 0,
        tts_dubbing_strategy: 2, tts_volume: 1, tts_speed: 1, bgm_volume: 0.5,
        subtitle_font_color: 0xffffff, subtitle_border_color: 0, video_material_keyword: '',
      })
    }
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()
    const field = wrapper.get('.dubbing-strategy-field')
    const select = field.findComponent({ name: 'el-select' })
    expect(select.attributes('modelvalue')).toBe(editing ? '2' : '0')
    expect(field.findAll('el-option-stub').map(option => [option.attributes('label'), option.attributes('value')]))
      .toEqual([['None', '0'], ['Timeline first', '1'], ['Natural first', '2']])
    select.vm.$emit('update:modelValue', 1)
    await wrapper.findAll('input')[0].setValue('https://example.com/video')
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()
    expect(editing ? apiMocks.updateTask : apiMocks.addTask).toHaveBeenLastCalledWith(expect.objectContaining({
      tts_dubbing_strategy: 1,
      ...(editing ? { task_id: 'task-dubbing' } : {}),
    }))
    wrapper.unmount()
  })

  it.each([false, true])('submits lip sync enabled=%s with the first returned service', async (enabled) => {
    apiMocks.getTaskConfig.mockResolvedValue({
      asr: [], tts: [], subtitle: [], bgm: [],
      lip_sync: [{ name: 'Remote service', value: 7 }, { name: 'Other service', value: 9 }],
      material: { source: [], splicing: [], transition: [], ratio: [] },
    })
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()
    const section = wrapper.get('.lip-sync-section')
    expect(section.findComponent({ name: 'el-select' }).attributes('modelvalue')).toBe('7')
    expect(section.findAll('el-option-stub').map(option => [option.attributes('label'), option.attributes('value')]))
      .toEqual([['Remote service', '7'], ['Other service', '9']])
    await wrapper.findAll('input')[0].setValue('https://example.com/video')
    await section.get('input').setValue(enabled)
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()
    expect(apiMocks.addTask).toHaveBeenLastCalledWith(expect.objectContaining({ is_lip_sync: enabled, lip_sync_type: 7 }))
    wrapper.unmount()
  })

  it.each([9, 99])('restores saved lip sync service %s if available, otherwise selects the first', async (saved) => {
    route.query = { task_id: 'task-lip-sync' }
    apiMocks.getTaskConfig.mockResolvedValue({
      asr: [], tts: [], subtitle: [], bgm: [],
      lip_sync: [{ name: 'Remote service', value: 7 }, { name: 'Other service', value: 9 }],
      material: { source: [], splicing: [], transition: [], ratio: [] },
    })
    apiMocks.getTaskDetail.mockResolvedValue({
      task_url: 'https://example.com/video', audio_rewrite_type: 0,
      is_lip_sync: 1, lip_sync_type: saved, tts_volume: 1, tts_speed: 1, bgm_volume: 0.5,
      subtitle_font_color: 0xffffff, subtitle_border_color: 0, video_material_keyword: '',
    })
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()
    expect(wrapper.get('.lip-sync-section').get<HTMLInputElement>('input').element.checked).toBe(true)
    const select = wrapper.get('.lip-sync-section').findComponent({ name: 'el-select' })
    expect(select.attributes('modelvalue')).toBe(saved === 9 ? '9' : '7')
    select.vm.$emit('update:modelValue', 9)
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()
    expect(apiMocks.updateTask).toHaveBeenLastCalledWith(expect.objectContaining({
      task_id: 'task-lip-sync', is_lip_sync: true, lip_sync_type: 9,
    }))
    wrapper.unmount()
  })

  it('blocks enabled lip sync when the service list is empty', async () => {
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()
    expect(wrapper.get('.lip-sync-section').findAll('el-option-stub')).toHaveLength(0)
    await wrapper.get('.lip-sync-section').get('input').setValue(true)
    await wrapper.findAll('input')[0].setValue('https://example.com/video')
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()
    expect(apiMocks.addTask).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('loads resolution labels and submits the selected format ID', async () => {
    apiMocks.checkTaskUrl.mockResolvedValue({ code: 0, msg: 'success', data: [
      { '144p 分辨率': '269' }, { '1080p 分辨率': '270' },
    ] })
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()
    const select = wrapper.findAllComponents({ name: 'el-select' }).find(item => item.classes().includes('resolution-select'))!
    expect(select.attributes('modelvalue')).toBe('')
    await wrapper.findAll('input')[0].setValue('https://example.com/video')
    await wrapper.findAll('button').find(button => button.text() === 'addTask.checkLink')!.trigger('click')
    await flushPromises()
    expect(apiMocks.checkTaskUrl).toHaveBeenCalledWith('https://example.com/video', false)
    expect(wrapper.findAll('el-option-stub').some(option => option.attributes('label') === '1080p 分辨率' && option.attributes('value') === '270')).toBe(true)
    select.vm.$emit('update:modelValue', '270')
    await wrapper.findAll('input[type="checkbox"]')[0].setValue(true)
    expect(select.attributes('modelvalue')).toBe('270')
    expect(wrapper.findAll('el-option-stub').some(option => option.attributes('value') === '270')).toBe(true)
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()
    expect(apiMocks.addTask).toHaveBeenLastCalledWith(expect.objectContaining({ format_id: '270', is_use_proxy: true }))
    await wrapper.findAll('input')[0].setValue('https://example.com/other')
    expect(select.attributes('modelvalue')).toBe('')
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()
    expect(apiMocks.addTask).toHaveBeenLastCalledWith(expect.objectContaining({ format_id: '' }))
  })

  it('ignores video information returned for a previous URL', async () => {
    let resolve!: (value: unknown) => void
    apiMocks.checkTaskUrl.mockReturnValue(new Promise(done => { resolve = done }))
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()
    await wrapper.findAll('input')[0].setValue('https://example.com/first')
    await wrapper.findAll('button').find(button => button.text() === 'addTask.checkLink')!.trigger('click')
    await wrapper.findAll('input')[0].setValue('https://example.com/second')
    resolve({ code: 0, msg: 'success', data: [{ '1080p 分辨率': '270' }] })
    await flushPromises()
    expect(wrapper.findAll('el-option-stub').some(option => option.attributes('value') === '270')).toBe(false)
    wrapper.unmount()
  })

  it('keeps automatic resolution when video information fails', async () => {
    apiMocks.checkTaskUrl.mockResolvedValue({ code: 1101, msg: 'failed', data: null })
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()
    await wrapper.findAll('input')[0].setValue('https://example.com/video')
    await wrapper.findAll('button').find(button => button.text() === 'addTask.checkLink')!.trigger('click')
    await flushPromises()
    expect(wrapper.getComponent('.resolution-select').attributes('modelvalue')).toBe('')
    const { ElMessage } = await import('element-plus')
    expect(ElMessage.error).toHaveBeenCalledWith('addTask.checkLinkFailed')
    wrapper.unmount()
  })

  it.each([true, false])('submits audio separation as boolean %s when creating', async (selected) => {
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()
    const separator = wrapper.findAllComponents({ name: 'el-select' })
      .find(item => item.attributes('modelvalue') === 'false')!
    expect(separator.exists()).toBe(true)
    separator.vm.$emit('update:modelValue', selected)
    await wrapper.findAll('input')[0].setValue('https://example.com/video')
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()
    expect(apiMocks.addTask).toHaveBeenCalledWith(expect.objectContaining({
      is_need_audio_separator: selected,
    }))
  })

  it.each([0, 1, false, true, undefined])('restores audio separation %s and allows changing it when editing', async (saved) => {
    route.query = { task_id: 'task-separator' }
    apiMocks.getTaskDetail.mockResolvedValue({
      task_url: 'https://example.com/video', audio_rewrite_type: 0,
      is_need_audio_separator: saved, tts_volume: 1, tts_speed: 1,
      subtitle_font_color: 0xffffff, subtitle_border_color: 0, video_material_keyword: '',
    })
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()
    const separator = wrapper.findAllComponents({ name: 'el-select' })
      .find(item => item.attributes('modelvalue') === String(!!saved))!
    expect(separator.exists()).toBe(true)
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()
    expect(apiMocks.updateTask).toHaveBeenLastCalledWith(expect.objectContaining({
      task_id: 'task-separator', is_need_audio_separator: !!saved,
    }))
    separator.vm.$emit('update:modelValue', !saved)
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()
    expect(apiMocks.updateTask).toHaveBeenLastCalledWith(expect.objectContaining({
      task_id: 'task-separator', is_need_audio_separator: !saved,
    }))
  })

  it.each([1, 2, 3])('loads and submits string language values for mode %s', async (mode) => {
    apiMocks.getTaskConfig.mockResolvedValue({
      asr: [{ name: 'Mode', value: mode }], tts: [], subtitle: [], bgm: [],
      material: { source: [], splicing: [], transition: [], ratio: [] },
    })
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()
    expect(apiMocks.getAsrLang).toHaveBeenCalledExactlyOnceWith(mode)
    const language = wrapper.findAllComponents({ name: 'el-select' })
      .find(item => item.attributes('modelvalue') === '0')!
    language.vm.$emit('update:modelValue', 'en')
    await wrapper.findAll('input')[0].setValue('https://example.com/video')
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()
    expect(apiMocks.addTask).toHaveBeenCalledWith(expect.objectContaining({
      audio_rewrite_type: mode, subtitle_lang: 'en',
    }))
  })

  it.each([1, 2, 3])('restores and updates a saved language for mode %s', async (mode) => {
    route.query = { task_id: 'task-language' }
    apiMocks.getTaskDetail.mockResolvedValue({
      task_url: 'https://example.com/video', audio_rewrite_type: mode,
      tts_volume: 1, tts_speed: 1,
      subtitle_lang: 'en', is_from_asr_or_subtitle: 1,
      subtitle_font_color: 0xffffff, subtitle_border_color: 0, video_material_keyword: '',
    })
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()
    expect(apiMocks.getAsrLang).toHaveBeenCalledExactlyOnceWith(mode)
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()
    expect(apiMocks.updateTask).toHaveBeenCalledWith(expect.objectContaining({
      task_id: 'task-language', audio_rewrite_type: mode, subtitle_lang: 'en',
    }))
  })

  it('ignores an outdated language response after switching modes', async () => {
    const wrapper = mount(AddTask, { global: { stubs } })
    await flushPromises()
    let resolveFirst!: (value: unknown) => void
    apiMocks.getAsrLang.mockImplementationOnce(() => new Promise(resolve => { resolveFirst = resolve }))
    const modeSelect = wrapper.findAllComponents({ name: 'el-select' })
      .find(item => item.attributes('modelvalue') === '0')!
    modeSelect.vm.$emit('update:modelValue', 1)
    await flushPromises()
    modeSelect.vm.$emit('update:modelValue', 3)
    await flushPromises()
    resolveFirst({ code: 0, data: [{ lang: 'Stale', value: 'stale' }] })
    await flushPromises()
    await wrapper.findAll('input')[0].setValue('https://example.com/video')
    await wrapper.get('.submit-btn').trigger('click')
    await flushPromises()
    expect(apiMocks.addTask).toHaveBeenCalledWith(expect.objectContaining({
      audio_rewrite_type: 3, subtitle_lang: '0',
    }))
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
