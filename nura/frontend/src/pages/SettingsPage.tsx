import { AppHeader } from '../components/AppHeader'
import { SettingRow, SettingsSection } from '../components/SettingsSection'
import { clearRemoteSession } from '../services/api'
import { useHistory } from '../stores/history'
import { useSession } from '../stores/session'
import { useSettings } from '../stores/settings'
import type { ReadMode, TextSize, Verbosity } from '../types/nura'

export function SettingsPage() {
  const settings = useSettings()
  const session = useSession()
  const clearHistory = useHistory((state) => state.clear)

  return (
    <div className="mx-auto max-w-2xl space-y-4 px-4 py-4 pb-8">
      <AppHeader title="Settings" subtitle="Voice, reading, privacy and accessibility" />

      <SettingsSection title="Voice">
        <SettingRow label="Speech speed" description={`${settings.speechSpeed.toFixed(1)}×`}>
          <input
            type="range"
            min="0.7"
            max="1.2"
            step="0.1"
            aria-label="Speech speed"
            className="w-28"
            value={settings.speechSpeed}
            onChange={(event) => settings.setSetting('speechSpeed', Number(event.target.value))}
          />
        </SettingRow>
        <SettingRow label="Response verbosity">
          <select
            aria-label="Response verbosity"
            className="min-h-12 rounded-2xl border border-white/10 bg-black/30 px-3"
            value={settings.verbosity}
            onChange={(event) => settings.setSetting('verbosity', event.target.value as Verbosity)}
          >
            <option value="concise">Concise</option>
            <option value="standard">Standard</option>
            <option value="detailed">Detailed</option>
          </select>
        </SettingRow>
      </SettingsSection>

      <SettingsSection title="Reading">
        <SettingRow label="Default reading mode">
          <select
            aria-label="Default reading mode"
            className="min-h-12 rounded-2xl border border-white/10 bg-black/30 px-3"
            value={settings.defaultMode}
            onChange={(event) => settings.setSetting('defaultMode', event.target.value as ReadMode)}
          >
            <option value="read">Read</option>
            <option value="currency">Currency</option>
            <option value="sign">Sign</option>
            <option value="document">Document</option>
          </select>
        </SettingRow>
        <SettingRow label="Automatic playback" description="Play ElevenLabs audio after each scan">
          <Toggle
            checked={settings.autoPlay}
            label="Automatic playback"
            onChange={(value) => settings.setSetting('autoPlay', value)}
          />
        </SettingRow>
        <SettingRow label="Continuous reading" description="Keep reading longer extracted text">
          <Toggle
            checked={settings.continuousReading}
            label="Continuous reading"
            onChange={(value) => settings.setSetting('continuousReading', value)}
          />
        </SettingRow>
      </SettingsSection>

      <SettingsSection title="Privacy">
        <SettingRow label="Do not retain images" description="Camera frames are not stored on this device">
          <Toggle
            checked={!settings.retainImages}
            label="Do not retain images"
            onChange={(value) => settings.setSetting('retainImages', !value)}
          />
        </SettingRow>
        <button
          type="button"
          className="min-h-12 w-full rounded-2xl border border-white/10 bg-white/5 font-bold"
          onClick={() => {
            clearHistory()
          }}
        >
          Clear history
        </button>
        <button
          type="button"
          className="min-h-12 w-full rounded-2xl border border-white/10 bg-white/5 font-bold"
          onClick={() => {
            void clearRemoteSession(session.sessionId)
            session.clearSession()
          }}
        >
          Clear session
        </button>
      </SettingsSection>

      <SettingsSection title="Accessibility">
        <SettingRow label="Text size">
          <select
            aria-label="Text size"
            className="min-h-12 rounded-2xl border border-white/10 bg-black/30 px-3"
            value={settings.textSize}
            onChange={(event) => settings.setSetting('textSize', event.target.value as TextSize)}
          >
            <option value="standard">Standard</option>
            <option value="large">Large</option>
            <option value="xl">Extra large</option>
          </select>
        </SettingRow>
        <SettingRow label="High contrast">
          <Toggle checked={settings.highContrast} label="High contrast" onChange={(value) => settings.setSetting('highContrast', value)} />
        </SettingRow>
        <SettingRow label="Reduced motion">
          <Toggle checked={settings.reducedMotion} label="Reduced motion" onChange={(value) => settings.setSetting('reducedMotion', value)} />
        </SettingRow>
      </SettingsSection>
    </div>
  )
}

function Toggle({
  checked,
  label,
  onChange,
}: {
  checked: boolean
  label: string
  onChange: (value: boolean) => void
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={[
        'relative h-8 w-14 rounded-full',
        checked ? 'bg-[var(--accent)]' : 'bg-[var(--border)]',
      ].join(' ')}
    >
      <span
        className={[
          'absolute top-1 h-6 w-6 rounded-full bg-white transition',
          checked ? 'right-1' : 'left-1',
        ].join(' ')}
      />
    </button>
  )
}
