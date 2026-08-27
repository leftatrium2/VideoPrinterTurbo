import type { Task } from '@/services/api'

type TaskDisplayInput = Pick<Task, 'task_url' | 'task_upload_video_path' | 'task_original_video_path' | 'local_path'>

export function getTaskAddress(task: TaskDisplayInput): string {
  return task.task_url || task.task_original_video_path || task.task_upload_video_path || ''
}

export function getTaskLocalPath(task: TaskDisplayInput): string {
  return task.task_upload_video_path || task.local_path || ''
}

export function getTaskVideoCategory(task: TaskDisplayInput): 'network' | 'local' | undefined {
  if (task.task_url) return 'network'
  if (task.task_upload_video_path) return 'local'
  return undefined
}
