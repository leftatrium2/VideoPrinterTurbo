import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LocalWhisperModels from './LocalWhisperModels.vue'

const api = vi.hoisted(() => ({ getLocalModelList: vi.fn(), downloadLocalModel: vi.fn() }))
vi.mock('@/services/api', () => api)
vi.mock('vue-i18n', () => ({ useI18n: () => ({ t: (key: string) => key }) }))
vi.mock('element-plus', () => ({ ElMessage: { error: vi.fn() } }))
const status = { model: 'small', state: 'missing', path: 'models/small', completed_files: 0, total_files: 4, error: '' }
const stubs = {
  'el-select': { template: '<select><slot /></select>' },
  'el-option': { template: '<option />' },
  'el-button': { props: ['disabled'], template: '<button :disabled="disabled"><slot /></button>' },
}

describe('LocalWhisperModels', () => {
  beforeEach(() => { vi.resetAllMocks(); api.getLocalModelList.mockResolvedValue([status]) })

  it('downloads the selected model and displays ready status', async () => {
    const wrapper = mount(LocalWhisperModels, { props: { modelValue: 'small' }, global: { stubs } })
    await flushPromises()
    api.downloadLocalModel.mockResolvedValue({ ...status, state: 'ready', completed_files: 4 })
    api.getLocalModelList.mockResolvedValue([{ ...status, state: 'ready', completed_files: 4 }])
    await wrapper.find('button').trigger('click')
    await flushPromises()
    expect(api.downloadLocalModel).toHaveBeenCalledWith('small')
    expect(wrapper.text()).toContain('asrConfig.ready')
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
    wrapper.unmount()
  })

  it('shows download failure and allows retry', async () => {
    api.getLocalModelList.mockResolvedValue([{ ...status, state: 'failed', error: 'network unavailable' }])
    const wrapper = mount(LocalWhisperModels, { props: { modelValue: 'small' }, global: { stubs } })
    await flushPromises()
    expect(wrapper.text()).toContain('network unavailable')
    expect(wrapper.find('button').attributes('disabled')).toBeUndefined()
    wrapper.unmount()
  })
})
