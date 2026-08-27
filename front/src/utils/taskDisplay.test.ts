import { describe, expect, it } from 'vitest'
import { getTaskAddress, getTaskLocalPath, getTaskVideoCategory } from './taskDisplay'

describe('task display helpers', () => {
  it('链接任务优先展示链接并归类为网络视频', () => {
    const task = {
      task_url: 'https://example.com/video',
      task_upload_video_path: 'storage/downloads/local.mp4',
      local_path: 'storage/output/final.mp4',
    }

    expect(getTaskAddress(task)).toBe('https://example.com/video')
    expect(getTaskLocalPath(task)).toBe('storage/downloads/local.mp4')
    expect(getTaskVideoCategory(task)).toBe('network')
  })

  it('本地任务展示上传路径并归类为本地视频', () => {
    const task = {
      task_url: '',
      task_upload_video_path: 'storage/downloads/local.mp4',
      task_original_video_path: 'my-source-video.mp4',
      local_path: 'storage/output/final.mp4',
    }

    expect(getTaskAddress(task)).toBe('my-source-video.mp4')
    expect(getTaskLocalPath(task)).toBe('storage/downloads/local.mp4')
    expect(getTaskVideoCategory(task)).toBe('local')
  })
})
