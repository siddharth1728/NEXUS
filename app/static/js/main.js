/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   NEXUS — Core JavaScript Engine · 2D Engineering Atlas
   Production Quality Interaction, Navigation & CSRF Integrity
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

'use strict';

/* ── 1. CSRF Token & Fetch Interceptor ─────────────────────────────── */
function getCsrfToken() {
  var meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

var _origFetch = window.fetch.bind(window);
window.fetch = function(resource, config) {
  if (!config) config = {};
  var method = (config.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].indexOf(method) !== -1) {
    config.headers = Object.assign({}, config.headers, {
      'X-CSRF-Token': getCsrfToken()
    });
  }
  return _origFetch(resource, config);
};

/* ── 2. Centralized API Fetch ──────────────────────────────────────── */
async function apiFetch(url, opts) {
  var res = await fetch(url, opts);
  if (!res.ok) {
    var detail = 'HTTP ' + res.status;
    try {
      var d = await res.json();
      detail = d.detail || detail;
    } catch(e) {}
    var err = new Error(detail);
    err.status = res.status;
    err.detail = detail;
    throw err;
  }
  return res.json();
}

/* ── 3. HTML Escaping ──────────────────────────────────────────────── */
function escapeHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/* ── 4. Relative Time Formatter ────────────────────────────────────── */
function formatRelativeTime(dateString) {
  if (!dateString) return 'Never';
  var date = new Date(dateString);
  if (isNaN(date.getTime())) return 'Unknown';
  var secs = Math.floor((Date.now() - date.getTime()) / 1000);
  if (secs < 60)   return 'just now';
  var mins = Math.floor(secs / 60);
  if (mins < 60)   return mins + 'm ago';
  var hrs = Math.floor(mins / 60);
  if (hrs < 24)    return hrs + 'h ago';
  var days = Math.floor(hrs / 24);
  if (days < 30)   return days + 'd ago';
  var months = Math.floor(days / 30);
  if (months < 12) return months + 'mo ago';
  return Math.floor(months / 12) + 'y ago';
}

/* ── 5. State & Severity Badges ────────────────────────────────────── */
function renderStateBadge(state) {
  var s = (state || 'MISSING').toUpperCase();
  var cls = 'badge-missing';
  if (s === 'STRONG') cls = 'badge-strong';
  else if (s === 'DEVELOPING') cls = 'badge-developing';
  else if (s === 'WEAK') cls = 'badge-weak';
  return '<span class="badge ' + cls + '">' + escapeHtml(s) + '</span>';
}

function renderSeverityBadge(severity) {
  var s = parseFloat(severity) || 0;
  if (s > 1.5) return '<span class="badge badge-severity-high">HIGH</span>';
  if (s > 0.5) return '<span class="badge badge-severity-medium">MEDIUM</span>';
  return '<span class="badge badge-severity-low">LOW</span>';
}

/* ── 6. System Notices (Technical Cartography Alerts) ──────────────── */
function showToast(message, type, duration) {
  if (type === undefined) type = 'info';
  if (duration === undefined) duration = 4000;

  var container = document.getElementById('toast-container');
  if (!container) return;

  var notice = document.createElement('div');
  notice.className = 'system-notice system-notice-' + type;
  notice.setAttribute('role', 'alert');

  var titleSpan = document.createElement('span');
  titleSpan.className = 'system-notice-title';
  titleSpan.textContent = (type === 'success' ? 'SURVEY CONFIRMED' : (type === 'error' ? 'ACCESS INTERRUPTION' : 'SYSTEM NOTICE'));

  var descSpan = document.createElement('span');
  descSpan.className = 'system-notice-desc';
  descSpan.textContent = message;

  notice.appendChild(titleSpan);
  notice.appendChild(descSpan);

  var dismiss = function() {
    notice.classList.add('removing');
    setTimeout(function() { notice.remove(); }, 180);
  };

  notice.addEventListener('click', dismiss);
  container.appendChild(notice);

  if (duration > 0) {
    setTimeout(dismiss, duration);
  }
  return notice;
}

/* ── 7. Drawer & Modal System ──────────────────────────────────────── */
var _drawerEscHandler = null;

function openDrawer(drawerId) {
  var drawer = document.getElementById(drawerId);
  var overlay = document.getElementById('drawer-overlay');
  if (!drawer || !overlay) return;

  overlay.classList.add('active');
  overlay.removeAttribute('aria-hidden');
  drawer.classList.add('active');
  document.body.style.overflow = 'hidden';

  setTimeout(function() {
    var focusable = drawer.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable.length) focusable[0].focus();
  }, 60);

  if (_drawerEscHandler) document.removeEventListener('keydown', _drawerEscHandler);
  _drawerEscHandler = function(e) {
    if (e.key === 'Escape') closeDrawer(drawerId);
  };
  document.addEventListener('keydown', _drawerEscHandler);
}

function closeDrawer(drawerId) {
  var drawer = document.getElementById(drawerId);
  var overlay = document.getElementById('drawer-overlay');
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

/* ── 8. Empty & Error State Helpers ────────────────────────────────── */
function showEmptyState(container, title, desc, ctaHtml) {
  if (!ctaHtml) ctaHtml = '';
  container.innerHTML =
    '<div class="empty-state">' +
    '  <div class="page-eyebrow">UNSURVEYED COORDINATES</div>' +
    '  <h2 class="empty-state-title">' + escapeHtml(title) + '</h2>' +
    '  <p class="empty-state-desc">' + escapeHtml(desc) + '</p>' +
    ctaHtml +
    '</div>';
}

function showError(container, title, desc) {
  container.innerHTML =
    '<div class="empty-state" style="border-color: var(--coral);">' +
    '  <div class="page-eyebrow" style="color: var(--coral);">SYSTEM INTERRUPTED</div>' +
    '  <h2 class="empty-state-title">' + escapeHtml(title) + '</h2>' +
    '  <p class="empty-state-desc">' + escapeHtml(desc) + '</p>' +
    '  <button class="btn btn-secondary btn-sm" onclick="window.location.reload()">RELOAD</button>' +
    '</div>';
}

/* ── 9. Mobile Nav & Navigation Sync ───────────────────────────────── */
function _initMobileNav() {
  var toggle = document.getElementById('mobile-menu-toggle');
  var menu = document.getElementById('mobile-nav-menu');
  if (!toggle || !menu) return;

  toggle.addEventListener('click', function() {
    var isOpen = menu.classList.toggle('active');
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });

  menu.querySelectorAll('a').forEach(function(link) {
    link.addEventListener('click', function() {
      menu.classList.remove('active');
      toggle.setAttribute('aria-expanded', 'false');
    });
  });
}

async function _initNavUser() {
  var roleEl = document.getElementById('nav-target-role');
  var avatarEl = document.getElementById('nav-avatar');
  var syncDot = document.getElementById('nav-sync-dot');
  var syncLabel = document.getElementById('nav-sync-label');
  if (!avatarEl) return;

  try {
    var profile = await apiFetch('/api/profile');
    var email = profile.email || '';
    var initials = email.split('@')[0].substring(0, 2).toUpperCase();
    avatarEl.textContent = initials || 'EX';
    avatarEl.title = email;

    if (roleEl && profile.target_role) {
      roleEl.textContent = profile.target_role;
      roleEl.style.display = 'inline-block';
    } else if (roleEl) {
      roleEl.style.display = 'none';
    }

    avatarEl.addEventListener('click', function() {
      window.location.href = '/profile';
    });

  } catch(e) {
    if (avatarEl) avatarEl.textContent = '–';
    if (roleEl) roleEl.style.display = 'none';
  }

  try {
    var identity = await apiFetch('/api/identity');
    if (syncLabel && identity.last_synced) {
      syncLabel.textContent = formatRelativeTime(identity.last_synced);
      if (syncDot) syncDot.className = 'sync-dot';
    } else if (syncLabel) {
      syncLabel.textContent = 'Unsurveyed';
      if (syncDot) syncDot.className = 'sync-dot never';
    }
  } catch(e) {
    if (syncLabel) syncLabel.textContent = '–';
  }
}

function _initDrawerOverlay() {
  var overlay = document.getElementById('drawer-overlay');
  if (!overlay) return;
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) {
      document.querySelectorAll('.drawer.active, .atlas-drawer.active').forEach(function(d) {
        d.classList.remove('active');
      });
      overlay.classList.remove('active');
      document.body.style.overflow = '';
    }
  });
}

/* ── Init ──────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function() {
  _initMobileNav();
  _initNavUser();
  _initDrawerOverlay();
});
