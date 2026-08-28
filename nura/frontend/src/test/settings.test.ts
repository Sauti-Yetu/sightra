import { beforeEach, describe, expect, it } from 'vitest'
import { useSettings } from '../stores/settings'

describe('settings store', () => {
  beforeEach(() => {
    useSettings.setState({
      verbosity: 'standard',
      autoPlay: true,
      highContrast: false,
    })
  })

  it('updates verbosity and playback preferences', () => {
    useSettings.getState().setSetting('verbosity', 'concise')
    useSettings.getState().setSetting('autoPlay', false)
    expect(useSettings.getState().verbosity).toBe('concise')
    expect(useSettings.getState().autoPlay).toBe(false)
  })
})
