import '@testing-library/jest-dom/vitest'

if (typeof crypto.randomUUID !== 'function') {
  crypto.randomUUID = () => '11111111-1111-1111-1111-111111111111'
}

HTMLMediaElement.prototype.play = async () => undefined
HTMLMediaElement.prototype.pause = () => undefined

if (!window.speechSynthesis) {
  Object.defineProperty(window, 'speechSynthesis', {
    value: { cancel: () => undefined, pause: () => undefined, speak: () => undefined },
  })
}
