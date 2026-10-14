import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage } from 'element-plus'
import BatchDownload from './BatchDownload.vue'

const api = vi.hoisted(() => ({ batchDownload: vi.fn(), batchDownloadUpload: vi.fn() }))
vi.mock('@/services/api', () => api)
vi.mock('vue-i18n', () => ({ useI18n: () => ({ t: (key: string) => key }) }))
vi.mock('element-plus', () => ({ ElMessage: { error: vi.fn(), success: vi.fn() } }))

function render() {
  return mount(BatchDownload, { global: { stubs: {
    'el-tabs': { template: '<div><slot /></div>' },
    'el-tab-pane': { template: '<section><slot /></section>' },
    'el-input': {
      props: ['modelValue'], emits: ['update:modelValue'],
      template: '<textarea :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    },
    'el-checkbox': {
      props: ['modelValue'], emits: ['update:modelValue'],
      template: '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
    },
    'el-button': { template: '<button><slot /></button>' },
    'el-upload': { name: 'ElUpload', props: ['onChange'], methods: { clearFiles() {} }, template: '<div><slot /></div>' },
    'el-icon': { template: '<span />' },
  } } })
}

describe('BatchDownload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.batchDownload.mockResolvedValue(undefined)
    api.batchDownloadUpload.mockResolvedValue(undefined)
  })

  it('submits parsed URLs with the proxy setting and resets on success', async () => {
    const wrapper = render()
    await wrapper.find('textarea').setValue(' https://example.com/a \n\nhttps://example.com/b')
    await wrapper.findAll('input')[0].setValue(true)
    await wrapper.findAll('button')[1].trigger('click')
    await flushPromises()
    expect(api.batchDownload).toHaveBeenCalledWith([
      { task_url: 'https://example.com/a', is_use_proxy: true },
      { task_url: 'https://example.com/b', is_use_proxy: true },
    ])
    expect(wrapper.find('textarea').element.value).toBe('')
    expect(wrapper.findAll('input')[0].element.checked).toBe(false)
  })

  it('keeps input and displays the backend error on failure', async () => {
    api.batchDownload.mockRejectedValue(new Error('Backend error'))
    const wrapper = render()
    await wrapper.find('textarea').setValue('https://example.com')
    await wrapper.findAll('button')[1].trigger('click')
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('Backend error')
    expect(wrapper.find('textarea').element.value).toBe('https://example.com')
  })

  it('rejects more than 100 URLs before sending a request', async () => {
    const wrapper = render()
    await wrapper.find('textarea').setValue(Array(101).fill('https://example.com').join('\n'))
    await wrapper.findAll('button')[1].trigger('click')
    expect(api.batchDownload).not.toHaveBeenCalled()
    expect(ElMessage.error).toHaveBeenCalledWith('batchDownload.tooMany')
  })

  it('validates file contents before upload and preserves an invalid selection', async () => {
    const wrapper = render()
    const file = new File(['not-a-url'], 'urls.txt')
    Object.defineProperty(file, 'arrayBuffer', { value: async () => new TextEncoder().encode('not-a-url').buffer })
    wrapper.findComponent({ name: 'ElUpload' }).props('onChange')({ raw: file })
    await wrapper.vm.$nextTick()
    await wrapper.findAll('button').at(-1)!.trigger('click')
    await flushPromises()
    expect(api.batchDownloadUpload).not.toHaveBeenCalled()
    expect(ElMessage.error).toHaveBeenCalledWith('batchDownload.invalidUrl')
    expect(wrapper.text()).toContain('urls.txt')
  })

  it('uploads a valid file using its separate proxy choice and resets only the file tab', async () => {
    const wrapper = render()
    await wrapper.find('textarea').setValue('https://example.com/preserved')
    const file = new File(['https://example.com/video'], 'urls.csv')
    Object.defineProperty(file, 'arrayBuffer', { value: async () => new TextEncoder().encode('https://example.com/video').buffer })
    wrapper.findComponent({ name: 'ElUpload' }).props('onChange')({ raw: file })
    await wrapper.findAll('input')[1].setValue(true)
    await wrapper.findAll('button').at(-1)!.trigger('click')
    await flushPromises()
    expect(api.batchDownloadUpload).toHaveBeenCalledWith(expect.objectContaining({ name: 'urls.csv' }), true)
    expect(wrapper.text()).not.toContain('urls.csv')
    expect(wrapper.find('textarea').element.value).toBe('https://example.com/preserved')
  })
})
