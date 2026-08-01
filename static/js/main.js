/* BuyPakistani — main.js */

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
  // Update theme-color meta tag for mobile browser UI
  const meta = document.getElementById('theme-color-meta');
  if (meta) meta.setAttribute('content', theme === 'light' ? '#f8fafc' : '#0a0a0a');
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

  // ── Autocomplete for all search inputs ────────────────
  initAutocomplete('navbarSearchInput', 'navbarAutocomplete', 'navbarAutocompleteList', 'navbarSearchSpinner', 'navbarSearchForm');
  initAutocomplete('mobileSearchInput', 'mobileAutocomplete', 'mobileAutocompleteList', 'mobileSearchSpinner', 'mobileSearchForm');
  initAutocomplete('searchInput', 'autocompleteDropdown', 'autocompleteList', 'searchSpinner', 'searchForm');
});

function initAutocomplete(inputId, dropdownId, listId, spinnerId, formId) {
  const input = document.getElementById(inputId);
  const dropdown = document.getElementById(dropdownId);
  const list = document.getElementById(listId);
  const spinner = document.getElementById(spinnerId);
  const form = document.getElementById(formId);

  if (!input) return;

  let debounceTimer = null;
  let currentRequest = null;

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function showSuggestions(suggestions) {
    if (!suggestions || suggestions.length === 0) {
      hideAutocomplete();
      return;
    }

    const q = input.value.trim();
    list.innerHTML = '';
    suggestions.forEach((s, i) => {
      const icon = i === 0 ? '🔍' : '📁';
      const safeS = escapeHtml(s);
      const safeQ = q ? escapeHtml(q) : '';
      const highlighted = safeQ
        ? safeS.replace(new RegExp(`(${safeQ.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'), '<strong style="color:#22c55e">$1</strong>')
        : safeS;

      const a = document.createElement('a');
      a.href = (form ? form.action : '/search/') + '?q=' + encodeURIComponent(s);
      a.className = 'flex items-center gap-3 px-4 py-3 text-sm transition hover:bg-white/5';
      a.style.color = 'var(--text-primary)';
      a.innerHTML = `<span class="text-lg">${icon}</span><span>${highlighted}</span>`;
      list.appendChild(a);
    });

    dropdown.classList.remove('hidden');
  }

  function hideAutocomplete() {
    if (dropdown) dropdown.classList.add('hidden');
  }

  function showLoading() {
    if (spinner) spinner.classList.remove('hidden');
  }

  function hideLoading() {
    if (spinner) spinner.classList.add('hidden');
  }

  function fetchSuggestions(query) {
    if (currentRequest) {
      currentRequest.abort();
    }

    if (!query || query.length < 1) {
      hideAutocomplete();
      return;
    }

    showLoading();
    currentRequest = new XMLHttpRequest();
    currentRequest.open('GET', '/search/suggestions/?q=' + encodeURIComponent(query), true);
    currentRequest.onload = function() {
      hideLoading();
      if (this.status === 200) {
        try {
          const data = JSON.parse(this.responseText);
          showSuggestions(data.suggestions);
        } catch(e) {
          hideAutocomplete();
        }
      }
    };
    currentRequest.onerror = function() {
      hideLoading();
      hideAutocomplete();
    };
    currentRequest.send();
  }

  input.addEventListener('input', function() {
    const query = this.value.trim();
    clearTimeout(debounceTimer);

    if (query.length < 1) {
      hideAutocomplete();
      return;
    }

    debounceTimer = setTimeout(function() {
      fetchSuggestions(query);
    }, 200);
  });

  // Hide autocomplete when clicking outside
  document.addEventListener('click', function(e) {
    if (form && !form.contains(e.target)) {
      hideAutocomplete();
    }
  });

  // Hide autocomplete on Escape key
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      hideAutocomplete();
    }
  });
}
