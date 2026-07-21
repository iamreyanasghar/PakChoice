/* BycottPK — main.js */

// ── Theme ──────────────────────────────────────────────
const html = document.documentElement;
const THEME_KEY = 'bpk-theme';

function applyTheme(theme) {
  if (theme === 'light') {
    html.classList.add('light');
  } else {
    html.classList.remove('light');
  }
  const btn = document.getElementById('themeToggle');
  if (btn) btn.textContent = theme === 'light' ? '🌙' : '☀️';
}

function toggleTheme() {
  const current = localStorage.getItem(THEME_KEY) || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  localStorage.setItem(THEME_KEY, next);
  applyTheme(next);
}

// Apply saved theme immediately (before paint)
applyTheme(localStorage.getItem(THEME_KEY) || 'dark');

document.addEventListener('DOMContentLoaded', () => {
  // Re-apply after DOM ready so button text is set
  applyTheme(localStorage.getItem(THEME_KEY) || 'dark');

  // ── Auto-hide flash messages ──────────────────────────
  setTimeout(() => {
    const messages = document.querySelectorAll('.flash-msg');
    messages.forEach((el, index) => {
      setTimeout(() => {
        el.classList.add('animate-slide-out');
        el.addEventListener('animationend', () => {
          el.remove();
          const container = document.getElementById('flash-messages');
          if (container && !container.querySelector('.flash-msg')) {
            container.style.display = 'none';
          }
        }, { once: true });
      }, index * 100);
    });
  }, 4000);

  // ── Mobile search toggle ──────────────────────────────
  const mobileSearchBtn = document.getElementById('mobileSearchBtn');
  const mobileSearchBar = document.getElementById('mobileSearchBar');
  if (mobileSearchBtn && mobileSearchBar) {
    mobileSearchBtn.addEventListener('click', () => {
      mobileSearchBar.classList.toggle('hidden');
      if (!mobileSearchBar.classList.contains('hidden')) {
        mobileSearchBar.querySelector('input')?.focus();
      }
    });
  }
});
