/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   NEXUS — Core JS Utilities v2
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

'use strict';

/* ── CSRF Token ─────────────────────────────────────── */
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

/* ── Fetch interceptor — inject CSRF on mutations ─── */
const _origFetch = window.fetch.bind(window);
window.fetch = function(resource, config = {}) {
  const method = (config.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    config.headers = Object.assign({}, config.headers, {
      'X-CSRF-Token': getCsrfToken()
    });
  }
  return _origFetch(resource, config);
};

/* ── apiFetch — centralized API call ────────────────── */
async function apiFetch(url, opts) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const d = await res.json(); detail = d.detail || detail; } catch {}
    const err = new Error(detail);
    err.status = res.status;
    err.detail = detail;
    throw err;
  }
  return res.json();
}

/* ── Safe string helpers ────────────────────────────── */
function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escapeJsString(value) {
  return JSON.stringify(String(value ?? ''))
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}

/* ── Relative time formatter ────────────────────────── */
function formatRelativeTime(dateString) {
  if (!dateString) return 'Never';
  const date = new Date(dateString);
  if (isNaN(date)) return 'Unknown';
  const secs = Math.floor((Date.now() - date) / 1000);
  if (secs < 60)  return 'just now';
  const mins = Math.floor(secs / 60);
  if (mins < 60)  return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)   return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30)  return `${days}d ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  return `${Math.floor(months / 12)}y ago`;
}

/* ── State badge renderer ───────────────────────────── */
function renderStateBadge(state) {
  const map = {
    STRONG:     'badge-strong',
    DEVELOPING: 'badge-developing',
    WEAK:       'badge-weak',
    MISSING:    'badge-missing',
  };
  const cls = map[state] || 'badge-missing';
  return `<span class="badge ${cls}">${escapeHtml(state || 'UNKNOWN')}</span>`;
}

/* ── Severity badge renderer ────────────────────────── */
function renderSeverityBadge(severity) {
  const s = parseFloat(severity) || 0;
  if (s > 1.5) return `<span class="badge badge-severity-high">HIGH</span>`;
  if (s > 0.5) return `<span class="badge badge-severity-medium">MEDIUM</span>`;
  return `<span class="badge badge-severity-low">LOW</span>`;
}

/* ── Toast system ───────────────────────────────────── */
const _TOAST_ICONS = {
  success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
  warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  error:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
  info:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
};

function showToast(message, type, duration) {
  if (type === undefined) type = 'info';
  if (duration === undefined) duration = 4000;

  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    container.setAttribute('aria-live', 'polite');
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', 'alert');

  // Use controlled SVG for icon (static string only), textContent for message (XSS-safe)
  const iconSpan = document.createElement('span');
  iconSpan.className = 'toast-icon';
  iconSpan.innerHTML = _TOAST_ICONS[type] || _TOAST_ICONS.info; // safe: only static SVG constants

  const textSpan = document.createElement('span');
  textSpan.className = 'toast-text';
  textSpan.textContent = message; // safe: textContent never interprets HTML

  toast.appendChild(iconSpan);
  toast.appendChild(textSpan);

  const dismiss = function() {
    toast.classList.add('removing');
    setTimeout(function() { toast.remove(); }, 220);
  };

  toast.addEventListener('click', dismiss);
  container.appendChild(toast);
  if (duration > 0) setTimeout(dismiss, duration);
  return toast;
}

/* ── Drawer system ──────────────────────────────────── */
let _drawerEscHandler = null;

function openDrawer(drawerId) {
  const drawer = document.getElementById(drawerId);
  const overlay = document.getElementById('drawer-overlay');
  if (!drawer || !overlay) return;

  overlay.classList.add('active');
  overlay.removeAttribute('aria-hidden');
  drawer.classList.add('active');
  document.body.style.overflow = 'hidden';

  // Focus first focusable element in drawer
  setTimeout(function() {
    const focusable = drawer.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable.length) focusable[0].focus();
  }, 50);

  if (_drawerEscHandler) document.removeEventListener('keydown', _drawerEscHandler);
  _drawerEscHandler = function(e) {
    if (e.key === 'Escape') closeDrawer(drawerId);
  };
  document.addEventListener('keydown', _drawerEscHandler);
}

function closeDrawer(drawerId) {
  const drawer = document.getElementById(drawerId);
  const overlay = document.getElementById('drawer-overlay');
  if (!drawer || !overlay) return;

  overlay.classList.remove('active');
  overlay.setAttribute('aria-hidden', 'true');
  drawer.classList.remove('active');
  document.body.style.overflow = '';

  if (_drawerEscHandler) {
    document.removeEventListener('keydown', _drawerEscHandler);
    _drawerEscHandler = null;
  }
}

/* ── Modal system ───────────────────────────────────── */
let _modalEscHandler = null;

function openModal(overlayId) {
  const overlay = document.getElementById(overlayId);
  if (!overlay) return;
  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
  setTimeout(function() {
    const focusable = overlay.querySelectorAll('button, input, select, [href], [tabindex]:not([tabindex="-1"])');
    if (focusable.length) focusable[0].focus();
  }, 50);
  if (_modalEscHandler) document.removeEventListener('keydown', _modalEscHandler);
  _modalEscHandler = function(e) { if (e.key === 'Escape') closeModal(overlayId); };
  document.addEventListener('keydown', _modalEscHandler);
}

function closeModal(overlayId) {
  const overlay = document.getElementById(overlayId);
  if (!overlay) return;
  overlay.classList.remove('active');
  document.body.style.overflow = '';
  if (_modalEscHandler) {
    document.removeEventListener('keydown', _modalEscHandler);
    _modalEscHandler = null;
  }
}

/* ── Empty state helper ─────────────────────────────── */
function showEmptyState(container, title, desc, ctaHtml) {
  if (!ctaHtml) ctaHtml = '';
  container.innerHTML =
    `<div class="empty-state">` +
    `<div class="empty-state-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></div>` +
    `<div class="empty-state-title">${escapeHtml(title)}</div>` +
    `<p class="empty-state-desc">${escapeHtml(desc)}</p>` +
    ctaHtml +
    `</div>`;
}

/* ── Error state helper ─────────────────────────────── */
function showError(container, title, desc) {
  container.innerHTML =
    `<div class="error-state">` +
    `<div class="error-state-title">${escapeHtml(title)}</div>` +
    `<p class="error-state-desc">${escapeHtml(desc)}</p>` +
    `<button class="btn btn-secondary btn-sm" onclick="window.location.reload()">Try again</button>` +
    `</div>`;
}

/* ── Skeleton rows helper ───────────────────────────── */
function showSkeleton(container, count, type) {
  if (!count) count = 3;
  if (!type) type = 'row';
  container.innerHTML = Array(count).fill(
    `<div class="skeleton skeleton-${type}" style="margin-bottom:8px;"></div>`
  ).join('');
}

/* ── Mobile nav (Removed in favor of bottom nav) ────── */
function _initMobileNav() {
  // Mobile drawer has been replaced by a CSS-only bottom navigation bar.
}

/* ── Logout ─────────────────────────────────────────── */
function _initLogout() {
  document.querySelectorAll('[data-action="logout"]').forEach(function(btn) {
    btn.addEventListener('click', async function() {
      const originalContent = btn.innerHTML;
      btn.textContent = 'Signing out…';
      btn.disabled = true;
      try {
        await fetch('/api/auth/logout', { method: 'POST' });
      } catch {}
      window.location.href = '/login';
    });
  });
}

/* ── Sidebar user info ──────────────────────────────── */
async function _initSidebarUser() {
  const nameEl   = document.getElementById('sidebar-user-name');
  const emailEl  = document.getElementById('sidebar-user-email');
  const avatarEl = document.getElementById('sidebar-user-avatar');
  if (!nameEl) return;

  try {
    const profile = await apiFetch('/api/profile');
    const name  = profile.name  || 'User';
    const email = profile.email || '';
    nameEl.textContent = name;
    if (emailEl) emailEl.textContent = email;
    if (avatarEl) {
      const initials = name.split(' ')
        .map(function(n) { return n[0]; })
        .slice(0, 2)
        .join('')
        .toUpperCase();
      avatarEl.textContent = initials || '–';
    }
  } catch {
    if (nameEl) nameEl.textContent = 'My Account';
  }
}

/* ── Drawer overlay click closes drawer ─────────────── */
function _initDrawerOverlay() {
  const overlay = document.getElementById('drawer-overlay');
  if (!overlay) return;
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) {
      document.querySelectorAll('.drawer.active').forEach(function(d) {
        closeDrawer(d.id);
      });
    }
  });
}

/* ── Evidence Explorer (available to all pages) ─────── */
window.openEvidenceExplorer = async function(skillId, skillName, state) {
  const nameEl  = document.getElementById('drawer-skill-name');
  const stateEl = document.getElementById('drawer-state-badge');
  const body    = document.getElementById('evidence-drawer-body');

  if (!nameEl || !body) return;

  nameEl.textContent = skillName || '–';
  if (stateEl) stateEl.innerHTML = renderStateBadge(state);

  // Show skeleton while loading
  body.innerHTML =
    `<div class="skeleton skeleton-text skeleton-full" style="margin-bottom:8px;"></div>` +
    `<div class="skeleton skeleton-text skeleton-3-4" style="margin-bottom:8px;"></div>` +
    `<div class="skeleton skeleton-text skeleton-1-2"></div>`;

  openDrawer('evidence-explorer-drawer');

  try {
    const evidence = await apiFetch(`/api/skills/${skillId}/evidence`);
    body.innerHTML = '';

    if (!evidence || evidence.length === 0) {
      showEmptyState(
        body,
        'No Evidence Yet',
        `NEXUS has not recorded engineering evidence for ${skillName}. ` +
        `Sync a repository to generate observations.`,
        ''
      );
      return;
    }

    const summary = document.createElement('p');
    summary.style.cssText = 'font-size:12px;color:var(--text-muted);margin-bottom:16px;';
    summary.textContent = `${evidence.length} evidence signal${evidence.length !== 1 ? 's' : ''} contributing to this state.`;
    body.appendChild(summary);

    evidence.forEach(function(e) {
      const item = document.createElement('div');
      item.className = 'evidence-item';
      const path = (e.source_reference || '').split(/[\/\\]/).pop() || e.source_reference || '–';
      const quality = ((e.quality_score || 0) * 100).toFixed(0);

      // Use textContent for all server-derived values to prevent XSS
      const textDiv = document.createElement('div');
      textDiv.className = 'evidence-item-text';
      textDiv.textContent = e.raw_observation_text || '–';

      const metaDiv = document.createElement('div');
      metaDiv.className = 'evidence-item-meta';

      const typeBadge = document.createElement('span');
      typeBadge.className = 'badge badge-type';
      typeBadge.textContent = e.type || '–';

      const sourceCode = document.createElement('code');
      sourceCode.className = 'evidence-source';
      sourceCode.textContent = path;

      const scoreSpan = document.createElement('span');
      scoreSpan.className = 'evidence-score';
      scoreSpan.textContent = `Quality ${quality}%`;

      metaDiv.appendChild(typeBadge);
      metaDiv.appendChild(sourceCode);
      metaDiv.appendChild(scoreSpan);

      item.appendChild(textDiv);
      item.appendChild(metaDiv);
      body.appendChild(item);
    });
  } catch (err) {
    showError(body, 'Failed to Load Evidence', 'Unable to retrieve evidence details.');
  }
};

/* ── Init ───────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function() {
  _initMobileNav();
  _initLogout();
  _initSidebarUser();
  _initDrawerOverlay();
});

/* Note: showToast is fully defined above. No duplicate needed. */
