export function announce(message: string) {
  const region = document.getElementById('nura-live')
  if (!region) return
  region.textContent = ''
  window.setTimeout(() => {
    region.textContent = message
  }, 50)
}
