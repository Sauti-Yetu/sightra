export async function compressImage(blob: Blob, maxDimension = 1280, quality = 0.72): Promise<Blob> {
  const bitmap = await createImageBitmap(blob)
  const scale = Math.min(1, maxDimension / Math.max(bitmap.width, bitmap.height))
  const width = Math.max(1, Math.round(bitmap.width * scale))
  const height = Math.max(1, Math.round(bitmap.height * scale))
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  if (!context) return blob
  context.drawImage(bitmap, 0, 0, width, height)
  bitmap.close()
  return await new Promise((resolve) => {
    canvas.toBlob((next) => resolve(next ?? blob), 'image/jpeg', quality)
  })
}

export function captureFromVideo(video: HTMLVideoElement, maxDimension = 1280, quality = 0.72): Promise<Blob> {
  const width = video.videoWidth
  const height = video.videoHeight
  const scale = Math.min(1, maxDimension / Math.max(width, height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(width * scale))
  canvas.height = Math.max(1, Math.round(height * scale))
  const context = canvas.getContext('2d')
  if (!context) {
    return Promise.reject(new Error('capture-failed'))
  }
  context.drawImage(video, 0, 0, canvas.width, canvas.height)
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob)
      else reject(new Error('capture-failed'))
    }, 'image/jpeg', quality)
  })
}

export function dataUrlFromBase64(base64: string, mime = 'audio/mpeg'): string {
  return `data:${mime};base64,${base64}`
}
