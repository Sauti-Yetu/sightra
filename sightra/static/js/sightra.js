/**
 * Sightra — Core frontend utilities
 * Theme, accessibility, network status, PWA install, screen reader announcements
 */
(function () {
  'use strict';

  const STORAGE_KEYS = {
    theme: 'sightra-theme',
    a11y: 'sightra-a11y',
    installDismissed: 'sightra-install-dismissed',
  };

  /* ── Theme ── */
  function getTheme() {
    return localStorage.getItem(STORAGE_KEYS.theme) ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  }

  function applyTheme(theme) {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem(STORAGE_KEYS.theme, theme);
    document.querySelectorAll('[data-theme-icon]').forEach(function (el) {
      el.textContent = theme === 'dark' ? 'light_mode' : 'dark_mode';
    });
    document.querySelectorAll('[data-theme-toggle-input]').forEach(function (input) {
      input.checked = theme === 'dark';
    });
    window.dispatchEvent(new CustomEvent('sightra:themechange', { detail: { theme: theme } }));
  }

  function initTheme() {
    applyTheme(getTheme());
    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        applyTheme(getTheme() === 'dark' ? 'light' : 'dark');
        announce(getTheme() === 'dark' ? 'Dark mode enabled' : 'Light mode enabled');
      });
    });
  }

  /* ── Accessibility preferences ── */
  function getA11yPrefs() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEYS.a11y) || '{}');
    } catch (e) {
      return {};
    }
  }

  function saveA11yPrefs(prefs) {
    localStorage.setItem(STORAGE_KEYS.a11y, JSON.stringify(prefs));
  }

  function applyA11yPrefs(prefs) {
    const html = document.documentElement;
    html.classList.toggle('a11y-high-contrast', !!prefs.highContrast);
    html.classList.toggle('a11y-large-text', prefs.textSize === 'large');
    html.classList.toggle('a11y-extra-large-text', prefs.textSize === 'extra-large');
    html.classList.toggle('a11y-large-targets', !!prefs.largeTargets);
    html.classList.toggle('a11y-reduced-transparency', !!prefs.reducedTransparency);
    html.classList.toggle('a11y-focus-enhanced', !!prefs.focusEnhanced);
    html.classList.toggle('a11y-spacing', !!prefs.increasedSpacing);
    html.classList.toggle('a11y-voice-first', !!prefs.voiceFirst);

    if (prefs.reducedMotion || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      html.classList.add('a11y-reduced-motion');
    }
  }

  function initA11yControls() {
    const prefs = getA11yPrefs();
    applyA11yPrefs(prefs);

    document.querySelectorAll('[data-a11y-toggle]').forEach(function (el) {
      const key = el.dataset.a11yToggle;
      if (el.type === 'checkbox') {
        el.checked = !!prefs[key];
        el.addEventListener('change', function () {
          prefs[key] = el.checked;
          saveA11yPrefs(prefs);
          applyA11yPrefs(prefs);
          announce(el.dataset.a11yLabel || (el.checked ? 'Setting enabled' : 'Setting disabled'));
        });
      }
    });

    document.querySelectorAll('[data-a11y-select]').forEach(function (el) {
      const key = el.dataset.a11ySelect;
      if (prefs[key]) el.value = prefs[key];
      el.addEventListener('change', function () {
        prefs[key] = el.value;
        saveA11yPrefs(prefs);
        applyA11yPrefs(prefs);
        announce('Accessibility setting updated');
      });
    });

    document.querySelectorAll('[data-a11y-mode]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const mode = btn.dataset.a11yMode;
        const modes = {
          standard: {},
          'high-contrast': { highContrast: true, focusEnhanced: true },
          'voice-first': { voiceFirst: true, largeTargets: true },
          'large-interface': { textSize: 'extra-large', largeTargets: true, increasedSpacing: true },
        };
        const newPrefs = modes[mode] || {};
        saveA11yPrefs(newPrefs);
        applyA11yPrefs(newPrefs);
        syncA11yUI(newPrefs);
        announce('Accessibility mode: ' + btn.textContent.trim());
      });
    });
  }

  function syncA11yUI(prefs) {
    document.querySelectorAll('[data-a11y-toggle]').forEach(function (el) {
      const key = el.dataset.a11yToggle;
      if (el.type === 'checkbox') el.checked = !!prefs[key];
    });
    document.querySelectorAll('[data-a11y-select]').forEach(function (el) {
      const key = el.dataset.a11ySelect;
      if (prefs[key]) el.value = prefs[key];
    });
  }

  /* ── Screen reader announcements ── */
  function announce(message, priority) {
    const region = document.getElementById('sr-announcer');
    if (!region) return;
    region.setAttribute('aria-live', priority === 'assertive' ? 'assertive' : 'polite');
    region.textContent = '';
    requestAnimationFrame(function () {
      region.textContent = message;
    });
  }

  window.Sightra = window.Sightra || {};
  window.Sightra.announce = announce;

  /* ── Network status ── */
  function initNetworkStatus() {
    const banner = document.getElementById('network-banner');
    if (!banner) return;

    const textEl = banner.querySelector('[data-network-text]');
    let hideTimeout;

    function setStatus(state, message) {
      banner.className = 'network-banner network-banner--' + state + ' is-visible';
      if (textEl) textEl.textContent = message;
      announce(message, state === 'offline' ? 'assertive' : 'polite');

      clearTimeout(hideTimeout);
      if (state === 'online') {
        hideTimeout = setTimeout(function () {
          banner.classList.remove('is-visible');
        }, 3000);
      }
    }

    function update() {
      if (!navigator.onLine) {
        setStatus('offline', "You're offline. Sightra features that need internet may not work.");
      } else {
        setStatus('online', "You're connected.");
      }
    }

    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    update();
  }

  /* ── PWA Install ── */
  let deferredPrompt = null;

  function initPWA() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function (err) {
        console.warn('Service worker registration failed:', err);
      });
    }

    window.addEventListener('beforeinstallprompt', function (e) {
      e.preventDefault();
      deferredPrompt = e;
      showInstallPrompt();
    });

    if (window.matchMedia('(display-mode: standalone)').matches) {
      hideInstallPrompt();
      return;
    }

    document.querySelectorAll('[data-install-trigger]').forEach(function (btn) {
      btn.addEventListener('click', triggerInstall);
    });

    document.querySelectorAll('[data-install-dismiss]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        localStorage.setItem(STORAGE_KEYS.installDismissed, '1');
        hideInstallPrompt();
      });
    });

    if (!localStorage.getItem(STORAGE_KEYS.installDismissed)) {
      setTimeout(showInstallPrompt, 5000);
    }
  }

  function showInstallPrompt() {
    if (localStorage.getItem(STORAGE_KEYS.installDismissed)) return;
    if (window.matchMedia('(display-mode: standalone)').matches) return;
    const el = document.getElementById('install-prompt');
    if (el) el.classList.add('is-visible');
  }

  function hideInstallPrompt() {
    const el = document.getElementById('install-prompt');
    if (el) el.classList.remove('is-visible');
  }

  function triggerInstall() {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function () {
        deferredPrompt = null;
        hideInstallPrompt();
      });
    } else {
      announce('To install Sightra, use your browser menu and choose Add to Home Screen.');
    }
  }

  /* ── Navigation active state ── */
  function initNav() {
    const path = window.location.pathname.replace(/\/$/, '') || '/';
    document.querySelectorAll('[data-nav-target]').forEach(function (link) {
      const target = link.dataset.navTarget.replace(/\/$/, '') || '/';
      const isActive = path === target || (target !== '/' && path.startsWith(target));
      link.classList.toggle('is-active', isActive);
      if (isActive) link.setAttribute('aria-current', 'page');
    });
  }

  /* ── Focus management on page load ── */
  function initFocusManagement() {
    const main = document.getElementById('main-content');
    if (main && window.location.hash === '#main-content') {
      main.focus();
    }
  }

  /* ── Voice speed (TTS) ── */
  window.Sightra.getVoiceRate = function () {
    const prefs = getA11yPrefs();
    return parseFloat(prefs.voiceRate) || 1;
  };

  window.Sightra.speak = function (text, options) {
    if (!text || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.rate = (options && options.rate) || window.Sightra.getVoiceRate();
    if (options && options.onEnd) utt.onend = options.onEnd;
    window.speechSynthesis.speak(utt);
  };

  /* ── Init ── */
  document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    initA11yControls();
    initNetworkStatus();
    initPWA();
    initNav();
    initFocusManagement();
  });
})();
