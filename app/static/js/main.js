/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   NEXUS — Core JS · 2D Engineering Atlas
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

'use strict';

/* ── CSRF Token ─────────────────────────────────────── */
function getCsrfToken() {
  var meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

/* ── Fetch interceptor — inject CSRF on mutations ─── */
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

/* ── apiFetch — centralized API call ────────────────── */
async function apiFetch(url, opts) {
  var res = await fetch(url, opts);
  if (!res.ok) {
    var detail = 'HTTP ' + res.status;
    try { var d = await res.json(); detail = d.detail || detail; } catch(e) {}
    var err = new Error(detail);
    err.status = res.status;
    err.detail = detail;
    throw err;
  }
  return res.json();
}

/* ── Safe string helpers ────────────────────────────── */
function escapeHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/* ── Relative time formatter ────────────────────────── */
function formatRelativeTime(dateString) {
  if (!dateString) return 'Never';
  var date = new Date(dateString);
  if (isNaN(date)) return 'Unknown';
  var secs = Math.floor((Date.now() - date) / 1000);
  if (secs < 60)  return 'just now';
  var mins = Math.floor(secs / 60);
  if (mins < 60)  return mins + 'm ago';
  var hrs = Math.floor(mins / 60);
  if (hrs < 24)   return hrs + 'h ago';
  var days = Math.floor(hrs / 24);
  if (days < 30)  return days + 'd ago';
  var months = Math.floor(days / 30);
  if (months < 12) return months + 'mo ago';
  return Math.floor(months / 12) + 'y ago';
}

/* ── State badge renderer ───────────────────────────── */
function renderStateBadge(state) {
  var map = {
    STRONG:     'badge-strong',
    DEVELOPING: 'badge-developing',
    WEAK:       'badge-weak',
    MISSING:    'badge-missing',
  };
  var cls = map[state] || 'badge-missing';
  return '<span class="badge ' + cls + '">' + escapeHtml(state || 'UNKNOWN') + '</span>';
}

/* ── Severity badge renderer ────────────────────────── */
function renderSeverityBadge(severity) {
  var s = parseFloat(severity) || 0;
  if (s > 1.5) return '<span class="badge badge-severity-high">HIGH</span>';
  if (s > 0.5) return '<span class="badge badge-severity-medium">MEDIUM</span>';
  return '<span class="badge badge-severity-low">LOW</span>';
}

/* ── System Notice (formerly Toast) ───────────────────── */
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
  titleSpan.textContent = type;

  var descSpan = document.createElement('span');
  descSpan.className = 'system-notice-desc';
  descSpan.textContent = message;

  notice.appendChild(titleSpan);
  notice.appendChild(descSpan);

  var dismiss = function() {
    notice.classList.add('removing');
    setTimeout(function() { notice.remove(); }, 220);
  };

  notice.addEventListener('click', dismiss);
  container.appendChild(notice);
  if (duration > 0) setTimeout(dismiss, duration);
  return notice;
}

/* ── Drawer system ──────────────────────────────────── */
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
  }, 50);

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

/* ── Modal system ───────────────────────────────────── */
var _modalEscHandler = null;

function openModal(overlayId) {
  var overlay = document.getElementById(overlayId);
  if (!overlay) return;
  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
  setTimeout(function() {
    var focusable = overlay.querySelectorAll('button, input, select, [href], [tabindex]:not([tabindex="-1"])');
    if (focusable.length) focusable[0].focus();
  }, 50);
  if (_modalEscHandler) document.removeEventListener('keydown', _modalEscHandler);
  _modalEscHandler = function(e) { if (e.key === 'Escape') closeModal(overlayId); };
  document.addEventListener('keydown', _modalEscHandler);
}

function closeModal(overlayId) {
  var overlay = document.getElementById(overlayId);
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
    '<div class="empty-state">' +
    '<div class="empty-state-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></div>' +
    '<div class="empty-state-title">' + escapeHtml(title) + '</div>' +
    '<p class="empty-state-desc">' + escapeHtml(desc) + '</p>' +
    ctaHtml +
    '</div>';
}

/* ── Error state helper ─────────────────────────────── */
function showError(container, title, desc) {
  container.innerHTML =
    '<div class="error-state">' +
    '<div class="error-state-title">' + escapeHtml(title) + '</div>' +
    '<p class="error-state-desc">' + escapeHtml(desc) + '</p>' +
    '<button class="btn btn-secondary btn-sm" onclick="window.location.reload()">Try again</button>' +
    '</div>';
}

/* ── Skeleton rows helper ───────────────────────────── */
function showSkeleton(container, count, type) {
  if (!count) count = 3;
  if (!type) type = 'row';
  var html = '';
  for (var i = 0; i < count; i++) {
    html += '<div class="skeleton skeleton-' + type + '" style="margin-bottom:8px;"></div>';
  }
  container.innerHTML = html;
}

/* ── Mobile nav toggle ──────────────────────────────── */
function _initMobileNav() {
  var toggle = document.getElementById('mobile-menu-toggle');
  var menu = document.getElementById('mobile-nav-menu');
  if (!toggle || !menu) return;

  toggle.addEventListener('click', function() {
    var isOpen = menu.classList.toggle('active');
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });

  // Close menu when clicking a link
  menu.querySelectorAll('a').forEach(function(link) {
    link.addEventListener('click', function() {
      menu.classList.remove('active');
      toggle.setAttribute('aria-expanded', 'false');
    });
  });
}

/* ── Logout ─────────────────────────────────────────── */
function _initLogout() {
  document.querySelectorAll('[data-action="logout"]').forEach(function(btn) {
    btn.addEventListener('click', async function() {
      btn.textContent = 'Signing out…';
      btn.disabled = true;
      try {
        await fetch('/api/auth/logout', { method: 'POST' });
      } catch(e) {}
      window.location.href = '/login';
    });
  });
}

/* ── Top nav user info ──────────────────────────────── */
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
    avatarEl.textContent = initials || '–';
    avatarEl.title = email;

    if (roleEl && profile.target_role) {
      roleEl.textContent = profile.target_role;
      roleEl.style.display = '';
    } else if (roleEl) {
      roleEl.style.display = 'none';
    }

    // Avatar click goes to profile
    avatarEl.addEventListener('click', function() {
      window.location.href = '/profile';
    });
    avatarEl.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        window.location.href = '/profile';
      }
    });

  } catch(e) {
    if (avatarEl) avatarEl.textContent = '–';
    if (roleEl) roleEl.style.display = 'none';
  }

  // Fetch last sync time from identity
  try {
    var identity = await apiFetch('/api/identity');
    if (syncLabel && identity.last_synced) {
      syncLabel.textContent = formatRelativeTime(identity.last_synced);
      if (syncDot) {
        var ago = (Date.now() - new Date(identity.last_synced)) / 1000;
        syncDot.className = 'sync-dot' + (ago > 86400 ? ' stale' : '');
      }
    } else if (syncLabel) {
      syncLabel.textContent = 'Never synced';
      if (syncDot) syncDot.className = 'sync-dot never';
    }
  } catch(e) {
    if (syncLabel) syncLabel.textContent = '–';
  }
}

/* ── Drawer overlay click closes drawer ─────────────── */
function _initDrawerOverlay() {
  var overlay = document.getElementById('drawer-overlay');
  if (!overlay) return;
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) {
      document.querySelectorAll('.drawer.active').forEach(function(d) {
        closeDrawer(d.id);
      });
    }
  });
}

/* ── Evidence Explorer / Field Note ─────────────────── */
window.openEvidenceExplorer = async function(skillId, skillName, state) {
  var nameEl  = document.getElementById('drawer-skill-name');
  var stateEl = document.getElementById('drawer-state-badge');
  var body    = document.getElementById('evidence-drawer-body');

  if (!nameEl || !body) return;

  nameEl.textContent = skillName || '–';
  if (stateEl) stateEl.innerHTML = renderStateBadge(state);

  body.innerHTML =
    '<div class="skeleton skeleton-text skeleton-full" style="margin-bottom:8px;"></div>' +
    '<div class="skeleton skeleton-text skeleton-3-4" style="margin-bottom:8px;"></div>' +
    '<div class="skeleton skeleton-text skeleton-1-2"></div>';

  openDrawer('evidence-explorer-drawer');

  try {
    var evidence = await apiFetch('/api/skills/' + skillId + '/evidence');
    body.innerHTML = '';

    if (!evidence || evidence.length === 0) {
      showEmptyState(
        body,
        'No evidence yet',
        'NEXUS hasn\'t found enough engineering evidence for ' + (skillName || 'this skill') +
        '. Sync a repository to generate observations.',
        ''
      );
      return;
    }

    var summary = document.createElement('p');
    summary.className = 't-caption mb-6';
    summary.innerHTML = '<span style="color:var(--primary); font-family:\'DM Mono\', monospace; text-transform:uppercase;">' + evidence.length + ' evidence signal' + (evidence.length !== 1 ? 's' : '') + '</span> contributing to this state.';
    body.appendChild(summary);

    var ledgerContainer = document.createElement('div');
    ledgerContainer.className = 'proof-ledger';

    evidence.forEach(function(e) {
      var item = document.createElement('div');
      item.className = 'proof-ledger-item';
      
      var grid = document.createElement('div');
      grid.className = 'proof-ledger-grid';
      
      var path = (e.source_reference || '').split(/[\/\\]/).pop() || e.source_reference || '–';
      var quality = ((e.quality_score || 0) * 100).toFixed(0);

      grid.innerHTML =
        '<div class="proof-ledger-label">SOURCE</div>' +
        '<div class="proof-ledger-value t-mono" style="font-size:11px;">' + escapeHtml(path) + '</div>' +
        
        '<div class="proof-ledger-label mt-3">OBSERVATION</div>' +
        '<div class="proof-ledger-value mt-3" style="font-size:13px;">' + escapeHtml(e.raw_observation_text || '–') + '</div>' +
        
        '<div class="proof-ledger-label mt-3">SIGNAL</div>' +
        '<div class="proof-ledger-value mt-3" style="font-family:\'DM Mono\', monospace; font-size:11px; text-transform:uppercase; color:var(--muted);">' + 
        escapeHtml(e.type || '–') + ' // QUALITY ' + quality + '%' +
        '</div>';

      item.appendChild(grid);
      ledgerContainer.appendChild(item);
    });
    
    body.appendChild(ledgerContainer);
  } catch (err) {
    showError(body, 'Failed to Load Evidence', 'Unable to retrieve evidence details.');
  }
};

/* ── Init ───────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function() {
  _initMobileNav();
  _initLogout();
  _initNavUser();
  _initDrawerOverlay();
});
