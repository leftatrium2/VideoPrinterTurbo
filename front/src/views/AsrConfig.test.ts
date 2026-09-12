import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AsrConfig from './AsrConfig.vue'

const apiMocks = vi.hoisted(() => ({
  getLocalWhisperList: vi.fn(),
  getAsrConfig: vi.fn(),
  updateAsrConfig: vi.fn(),
}))

vi.mock('@/services/api', () => ({
  ...apiMocks,
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))

vi.mock('element-plus', () => ({
  ElMessage: { error: vi.fn(), success: vi.fn() },
}))

const savedConfig = {
  tencent_cloud_secret_id: '', tencent_cloud_secret_key: '', xfyun_appid: '', xfyun_secret_key: '', xfyun_web_api: '',
  local_whisper_type: 0, azure_subscription_key: '', azure_region: '', openai_api_key: '', openai_model: '', openai_base_url: '',
  volcengine_appid: '', volcengine_access_token: '', remote_whisper_type: 1, remote_vllm_url: 'http://vllm.example',
  remote_vllm_model: 'whisper-large-v3', remote_whisper_cpp_url: 'http://whisper-cpp.example',
}

const ElSelectStub = defineComponent({
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', Number($event.target.value))"><slot /></select>',
})

const stubs = {
  'el-tabs': { template: '<div><slot /></div>' },
  'el-tab-pane': { props: ['label'], template: '<section>{{ label }}<slot /></section>' },
  'el-select': ElSelectStub,
  'el-option': { props: ['label', 'value'], template: '<option :value="value">{{ label }}</option>' },
  'el-input': { template: '<input />' },
  'el-button': { template: '<button><slot /></button>' },
}

describe('AsrConfig', () => {
  beforeEach(() => {
    apiMocks.getLocalWhisperList.mockResolvedValue([])
    apiMocks.getAsrConfig.mockResolvedValue({ ...savedConfig })
    apiMocks.updateAsrConfig.mockResolvedValue(undefined)
  })

  it('defaults an unset remote Whisper deployment to vLLM fields', async () => {
    apiMocks.getAsrConfig.mockResolvedValue({ ...savedConfig, remote_whisper_type: 0 })
    const wrapper = mount(AsrConfig, { global: { stubs } })
    await flushPromises()

    expect(wrapper.text()).toContain('asrConfig.remoteWhisperTab')
    expect(wrapper.text()).toContain('asrConfig.vllmUrl')
    expect(wrapper.text()).toContain('asrConfig.vllmModel')
  })

  it('shows only the Whisper.cpp URL after selecting the Whisper.cpp deployment', async () => {
    const wrapper = mount(AsrConfig, { global: { stubs } })
    await flushPromises()

    await wrapper.findAll('select')[1].setValue('2')

    expect(wrapper.text()).toContain('asrConfig.whisperCppUrl')
    expect(wrapper.text()).not.toContain('asrConfig.vllmUrl')
    expect(wrapper.text()).not.toContain('asrConfig.vllmModel')
  })

  it('submits every remote Whisper configuration field', async () => {
    const wrapper = mount(AsrConfig, { global: { stubs } })
    await flushPromises()

    await wrapper.findAll('button').at(-1)!.trigger('click')

    expect(apiMocks.updateAsrConfig).toHaveBeenCalledWith(expect.objectContaining({
      remote_whisper_type: 1,
      remote_vllm_url: 'http://vllm.example',
      remote_vllm_model: 'whisper-large-v3',
      remote_whisper_cpp_url: 'http://whisper-cpp.example',
    }))
  })
})
