/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   NEXUS — 2D Engineering Atlas 2.0 Renderer
   Deterministic Technical Cartography & Interactive Proof Routing
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

'use strict';

var NexusAtlas = (function() {

  // ── Layout Constants ──────────────────────────────────────────────
  var TERRITORY_PADDING = 24;
  var SIGNAL_RADIUS = 6;
  var LANDMARK_SIZE = 9;
  var LABEL_OFFSET = 16;
  var TERRITORY_GAP = 28;
  var COLUMN_WIDTH = 290;
  var ROW_HEIGHT = 38;
  var TERRITORY_HEADER = 44;
  var MIN_TERRITORY_HEIGHT = 120;

  // ── Color System ──────────────────────────────────────────────────
  var STATE_COLORS = {
    STRONG:     '#2FAE94', // Engineering Green
    DEVELOPING: '#4F46E5', // Blueprint Blue
    WEAK:       '#C98A2E', // Amber
    MISSING:    '#D9655A'  // Rust / Coral
  };

  // ── Deterministic Territory Layout (Masonry) ──────────────────────
  function calculateLayout(territories, width) {
    var cols = Math.max(1, Math.floor(width / (COLUMN_WIDTH + TERRITORY_GAP)));
    var colWidth = Math.floor((width - (cols - 1) * TERRITORY_GAP) / cols);
    var positions = [];
    var colHeights = [];
    for (var i = 0; i < cols; i++) colHeights.push(TERRITORY_PADDING);

    // Sort alphabetically for deterministic placement
    var sorted = territories.slice().sort(function(a, b) {
      return a.category.localeCompare(b.category);
    });

    sorted.forEach(function(territory) {
      var signalCount = 0;
      (territory.landmarks || []).forEach(function(lm) { signalCount += (lm.signals || []).length; });
      signalCount += (territory.unexplored || []).length;

      var height = Math.max(
        MIN_TERRITORY_HEIGHT,
        TERRITORY_HEADER + signalCount * ROW_HEIGHT + TERRITORY_PADDING
      );

      // Place in shortest column
      var minCol = 0;
      for (var c = 1; c < cols; c++) {
        if (colHeights[c] < colHeights[minCol]) minCol = c;
      }

      positions.push({
        territory: territory,
        x: minCol * (colWidth + TERRITORY_GAP) + TERRITORY_PADDING,
        y: colHeights[minCol],
        width: colWidth - TERRITORY_PADDING * 2,
        height: height
      });

      colHeights[minCol] += height + TERRITORY_GAP;
    });

    var totalHeight = Math.max.apply(null, colHeights) + TERRITORY_PADDING;
    return { positions: positions, totalHeight: totalHeight };
  }

  // ── SVG Helpers ───────────────────────────────────────────────────
  var SVG_NS = 'http://www.w3.org/2000/svg';

  function svgEl(tag, attrs) {
    var el = document.createElementNS(SVG_NS, tag);
    if (attrs) {
      Object.keys(attrs).forEach(function(k) {
        el.setAttribute(k, attrs[k]);
      });
    }
    return el;
  }

  function svgText(text, attrs) {
    var el = svgEl('text', attrs);
    el.textContent = text;
    return el;
  }

  // ── Main Render Entrypoint ────────────────────────────────────────
  function render(container, data, options) {
    if (!container) return;
    if (!options) options = {};

    container.innerHTML = '';

    var territories = data.atlas_territories || [];
    var targetRole = data.target_role || 'Engineering';

    if (territories.length === 0) {
      renderEmptyAtlas(container, targetRole);
      return;
    }

    var containerWidth = container.clientWidth || 840;
    var layout = calculateLayout(territories, containerWidth);

    var svg = svgEl('svg', {
      'class': 'atlas-svg',
      'viewBox': '0 0 ' + containerWidth + ' ' + layout.totalHeight,
      'role': 'region',
      'aria-label': 'Engineering Atlas — Technical Map of Capability Signals'
    });

    // Grid Layer
    renderGrid(svg, containerWidth, layout.totalHeight);

    // Route Tracing Path Group (Follow the Proof)
    var pathsGroup = svgEl('g', { 'class': 'atlas-paths' });
    svg.appendChild(pathsGroup);

    // Territories Layer
    var allSignalEls = [];
    var allLandmarkEls = [];
    var signalDataMap = {};
    var landmarkPosMap = {};

    layout.positions.forEach(function(pos) {
      var result = renderTerritory(svg, pos, options);
      allSignalEls = allSignalEls.concat(result.signalEls);
      allLandmarkEls = allLandmarkEls.concat(result.landmarkEls);
      
      Object.keys(result.signalDataMap).forEach(function(k) {
        signalDataMap[k] = result.signalDataMap[k];
      });
      Object.keys(result.landmarkPosMap).forEach(function(k) {
        landmarkPosMap[k] = result.landmarkPosMap[k];
      });
    });

    container.appendChild(svg);

    // Render Semantic Accessible Fallback (hidden visually, available to screen readers)
    renderAccessibleFallback(container, territories, targetRole);

    // Attach state to container
    container._atlasState = {
      svg: svg,
      pathsGroup: pathsGroup,
      signals: allSignalEls,
      landmarks: allLandmarkEls,
      signalDataMap: signalDataMap,
      landmarkPosMap: landmarkPosMap,
      selectedSignal: null
    };

    // Check URL query parameters for auto-selection (e.g. ?skill=Python or ?project=1)
    var urlParams = new URLSearchParams(window.location.search);
    var targetSkill = urlParams.get('skill');
    if (targetSkill) {
      setTimeout(function() {
        NexusAtlas.selectSkillByName(container, targetSkill);
      }, 150);
    }
  }

  // ── Grid Lines ────────────────────────────────────────────────────
  function renderGrid(svg, width, height) {
    var g = svgEl('g', { 'class': 'atlas-grid', 'aria-hidden': 'true' });
    var step = 48;
    for (var x = step; x < width; x += step) {
      g.appendChild(svgEl('line', {
        'class': 'atlas-grid-line',
        x1: x, y1: 0, x2: x, y2: height
      }));
    }
    for (var y = step; y < height; y += step) {
      g.appendChild(svgEl('line', {
        'class': 'atlas-grid-line',
        x1: 0, y1: y, x2: width, y2: y
      }));
    }
    svg.appendChild(g);
  }

  // ── Territory Renderer ────────────────────────────────────────────
  function renderTerritory(svg, pos, options) {
    var t = pos.territory;
    var g = svgEl('g', { 'class': 'atlas-territory' });

    // Boundary rectangle
    g.appendChild(svgEl('rect', {
      'class': 'atlas-territory-bg',
      x: pos.x, y: pos.y,
      width: pos.width, height: pos.height
    }));

    // Header Label
    g.appendChild(svgText('TERRITORY // ' + t.category.toUpperCase(), {
      'class': 'atlas-territory-label',
      x: pos.x + 12,
      y: pos.y + 20
    }));

    var signalEls = [];
    var landmarkEls = [];
    var signalDataMap = {};
    var landmarkPosMap = {};
    var yOffset = pos.y + TERRITORY_HEADER;

    // 1. Landmarks & Verified Signals
    (t.landmarks || []).forEach(function(landmark) {
      var lmX = pos.x + 16;
      var lmY = yOffset;

      landmarkPosMap[landmark.project_id] = { x: lmX, y: lmY, name: landmark.project_name };

      var lmG = svgEl('g', {
        'class': 'atlas-landmark',
        'data-project-id': landmark.project_id,
        'role': 'button',
        'tabindex': '0',
        'aria-label': 'Project Landmark: ' + landmark.project_name
      });

      // Diamond Marker
      var diamond = svgEl('rect', {
        'class': 'atlas-landmark-icon',
        x: lmX - LANDMARK_SIZE/2,
        y: lmY - LANDMARK_SIZE/2,
        width: LANDMARK_SIZE,
        height: LANDMARK_SIZE,
        transform: 'rotate(45 ' + lmX + ' ' + lmY + ')'
      });
      lmG.appendChild(diamond);

      lmG.appendChild(svgText(landmark.project_name.toUpperCase(), {
        'class': 'atlas-landmark-label',
        x: lmX + LABEL_OFFSET,
        y: lmY + 4
      }));

      g.appendChild(lmG);
      landmarkEls.push(lmG);
      yOffset += ROW_HEIGHT * 0.75;

      // Signals under this landmark
      (landmark.signals || []).forEach(function(signal) {
        var sX = pos.x + 36;
        var sY = yOffset;
        var state = signal.state || 'MISSING';
        var sigKey = 'signal-' + signal.skill_id;

        signalDataMap[sigKey] = {
          skill_id: signal.skill_id,
          skill_name: signal.skill_name,
          state: state,
          project_id: landmark.project_id,
          project_name: landmark.project_name,
          category: t.category,
          evidence: signal.evidence || [],
          pos: { x: sX, y: sY }
        };

        var sigG = svgEl('g', {
          'class': 'atlas-signal atlas-signal-' + state.toLowerCase(),
          'data-skill-id': signal.skill_id,
          'data-skill-name': signal.skill_name,
          'data-project-id': landmark.project_id,
          'role': 'button',
          'tabindex': '0',
          'aria-label': 'Signal: ' + signal.skill_name + ' (' + state + ')'
        });

        // Circle marker
        var dotColor = STATE_COLORS[state] || STATE_COLORS.MISSING;
        var circle = svgEl('circle', {
          'class': 'atlas-signal-dot',
          cx: sX, cy: sY,
          r: SIGNAL_RADIUS,
          fill: dotColor
        });
        sigG.appendChild(circle);

        // Label
        sigG.appendChild(svgText(signal.skill_name, {
          'class': 'atlas-signal-label',
          x: sX + LABEL_OFFSET,
          y: sY + 4
        }));

        // Interaction
        sigG.addEventListener('click', function() {
          NexusAtlas.selectSignal(svg.parentElement, sigKey);
        });

        sigG.addEventListener('keydown', function(e) {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            NexusAtlas.selectSignal(svg.parentElement, sigKey);
          }
        });

        g.appendChild(sigG);
        signalEls.push(sigG);
        yOffset += ROW_HEIGHT;
      });
    });

    // 2. Unexplored Skills in Territory
    (t.unexplored || []).forEach(function(unexploredSkill) {
      var sX = pos.x + 20;
      var sY = yOffset;
      var sigKey = 'unexplored-' + (unexploredSkill.skill_id || unexploredSkill.name);

      signalDataMap[sigKey] = {
        skill_id: unexploredSkill.skill_id,
        skill_name: unexploredSkill.name || unexploredSkill.skill_name || 'Unexplored Skill',
        state: 'MISSING',
        project_id: null,
        project_name: null,
        category: t.category,
        evidence: [],
        pos: { x: sX, y: sY }
      };

      var unG = svgEl('g', {
        'class': 'atlas-signal atlas-signal-missing',
        'data-skill-name': unexploredSkill.name,
        'role': 'button',
        'tabindex': '0',
        'aria-label': 'Unexplored Area: ' + unexploredSkill.name
      });

      // Dashed circle for unexplored
      var unCircle = svgEl('circle', {
        'class': 'atlas-signal-dot',
        cx: sX, cy: sY,
        r: SIGNAL_RADIUS,
        fill: 'none',
        stroke: '#76726A',
        'stroke-dasharray': '2 2'
      });
      unG.appendChild(unCircle);

      unG.appendChild(svgText(unexploredSkill.name, {
        'class': 'atlas-signal-label t-muted',
        x: sX + LABEL_OFFSET,
        y: sY + 4,
        fill: '#76726A'
      }));

      unG.addEventListener('click', function() {
        NexusAtlas.selectSignal(svg.parentElement, sigKey);
      });

      g.appendChild(unG);
      signalEls.push(unG);
      yOffset += ROW_HEIGHT;
    });

    svg.appendChild(g);
    return { signalEls: signalEls, landmarkEls: landmarkEls, signalDataMap: signalDataMap, landmarkPosMap: landmarkPosMap };
  }

  // ── "Follow the Proof" Route Drawing & Selection ──────────────────
  function selectSignal(container, sigKey) {
    if (!container || !container._atlasState) return;
    var state = container._atlasState;
    var sigData = state.signalDataMap[sigKey];
    if (!sigData) return;

    state.selectedSignal = sigKey;

    // 1. Highlight Selected Signal & Dim Others
    state.signals.forEach(function(el) {
      var id = el.getAttribute('data-skill-id');
      var name = el.getAttribute('data-skill-name');
      if ((id && sigData.skill_id && id == sigData.skill_id) || (name && name === sigData.skill_name)) {
        el.classList.add('highlighted');
        el.classList.remove('dimmed');
      } else {
        el.classList.remove('highlighted');
        el.classList.add('dimmed');
      }
    });

    // 2. Dim Landmarks except the connecting project
    state.landmarks.forEach(function(lm) {
      var pId = lm.getAttribute('data-project-id');
      if (sigData.project_id && pId == sigData.project_id) {
        lm.classList.remove('dimmed');
      } else {
        lm.classList.add('dimmed');
      }
    });

    // 3. Draw Route Path if attached to a Landmark
    state.pathsGroup.innerHTML = '';
    if (sigData.project_id && state.landmarkPosMap[sigData.project_id]) {
      var lmPos = state.landmarkPosMap[sigData.project_id];
      var sigPos = sigData.pos;

      // Draw direct architectural route
      var pathD = 'M ' + lmPos.x + ' ' + lmPos.y +
                  ' L ' + (lmPos.x + 20) + ' ' + lmPos.y +
                  ' L ' + (sigPos.x - 12) + ' ' + sigPos.y +
                  ' L ' + sigPos.x + ' ' + sigPos.y;

      var routePath = svgEl('path', {
        'class': 'atlas-proof-path visible',
        'd': pathD
      });
      state.pathsGroup.appendChild(routePath);
    }

    // 4. Open Field Note Drawer
    if (typeof window.openEvidenceExplorer === 'function') {
      window.openEvidenceExplorer(sigData.skill_id, sigData.skill_name, sigData.state, sigData.project_name, sigData.evidence);
    }
  }

  function selectSkillByName(container, skillName) {
    if (!container || !container._atlasState) return;
    var map = container._atlasState.signalDataMap;
    for (var key in map) {
      if (map[key].skill_name.toLowerCase() === skillName.toLowerCase()) {
        selectSignal(container, key);
        return;
      }
    }
  }

  // ── Accessible Semantic Fallback ──────────────────────────────────
  function renderAccessibleFallback(container, territories, targetRole) {
    var fallback = document.createElement('div');
    fallback.className = 'sr-only';
    fallback.style.position = 'absolute';
    fallback.style.width = '1px';
    fallback.style.height = '1px';
    fallback.style.overflow = 'hidden';
    fallback.style.clip = 'rect(0,0,0,0)';

    var html = '<h2>Engineering Atlas Table for ' + escapeHtml(targetRole) + '</h2><ul>';
    territories.forEach(function(t) {
      html += '<li><h3>Territory: ' + escapeHtml(t.category) + '</h3><ul>';
      (t.landmarks || []).forEach(function(lm) {
        html += '<li>Project: ' + escapeHtml(lm.project_name) + '<ul>';
        (lm.signals || []).forEach(function(s) {
          html += '<li>Signal: ' + escapeHtml(s.skill_name) + ' — State: ' + escapeHtml(s.state) + '</li>';
        });
        html += '</ul></li>';
      });
      (t.unexplored || []).forEach(function(u) {
        html += '<li>Unexplored: ' + escapeHtml(u.name) + ' — State: Missing</li>';
      });
      html += '</ul></li>';
    });
    html += '</ul>';
    fallback.innerHTML = html;
    container.appendChild(fallback);
  }

  // ── Empty Atlas ───────────────────────────────────────────────────
  function renderEmptyAtlas(container, targetRole) {
    container.innerHTML =
      '<div class="empty-state" style="margin: 32px auto;">' +
      '  <div class="page-eyebrow">UNSURVEYED COORDINATES</div>' +
      '  <h2 class="empty-state-title">NO ATLAS DATA AVAILABLE</h2>' +
      '  <p class="empty-state-desc">Your engineering Atlas begins with your first surveyed project repository.</p>' +
      '  <a href="/projects" class="btn btn-primary">CONNECT REPOSITORY</a>' +
      '</div>';
  }

  return {
    render: render,
    selectSignal: selectSignal,
    selectSkillByName: selectSkillByName
  };

})();
