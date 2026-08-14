/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   NEXUS — Atlas Renderer
   Deterministic 2D SVG Engineering Atlas
   
   TRUTH CONTRACT:
   Every visual element traces to real NEXUS API data.
   No frontend-only inference. No fabricated data.
   If data is missing → honest empty state.
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

'use strict';

var NexusAtlas = (function() {

  // ── Layout constants (deterministic) ──────────────
  var TERRITORY_PADDING = 30;
  var SIGNAL_RADIUS = 6;
  var LANDMARK_SIZE = 8;
  var LABEL_OFFSET = 16;
  var TERRITORY_GAP = 40;
  var COLUMN_WIDTH = 280;
  var ROW_HEIGHT_PER_SIGNAL = 36;
  var TERRITORY_HEADER = 40;
  var MIN_TERRITORY_HEIGHT = 100;

  // ── Color mapping ────────────────────────────────
  var STATE_COLORS = {
    STRONG:     '#2FAE94',
    DEVELOPING: '#4F46E5',
    WEAK:       '#C98A2E',
    MISSING:    '#7D7A73'
  };

  // ── Deterministic territory positions ─────────────
  // Categories are sorted alphabetically for stability.
  // Territories are placed in a grid layout.
  function calculateLayout(territories, width) {
    var cols = Math.max(1, Math.floor(width / (COLUMN_WIDTH + TERRITORY_GAP)));
    var colWidth = Math.floor((width - (cols - 1) * TERRITORY_GAP) / cols);
    var positions = [];
    var colHeights = [];
    for (var i = 0; i < cols; i++) colHeights.push(TERRITORY_PADDING);

    // Sort territories alphabetically for determinism
    var sorted = territories.slice().sort(function(a, b) {
      return a.category.localeCompare(b.category);
    });

    sorted.forEach(function(territory) {
      // Count total items (signals from landmarks + unexplored)
      var signalCount = 0;
      territory.landmarks.forEach(function(lm) { signalCount += lm.signals.length; });
      signalCount += territory.unexplored.length;
      
      var height = Math.max(
        MIN_TERRITORY_HEIGHT,
        TERRITORY_HEADER + signalCount * ROW_HEIGHT_PER_SIGNAL + TERRITORY_PADDING
      );

      // Place in shortest column (masonry)
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

  // ── SVG element helpers ───────────────────────────
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

  // ── Main render function ──────────────────────────
  function render(container, data, options) {
    if (!container) return;
    if (!options) options = {};

    container.innerHTML = '';

    var territories = data.atlas_territories || [];
    var targetRole = data.target_role || null;
    var journey = data.engineering_journey || {};

    // Empty state
    if (territories.length === 0) {
      renderEmptyAtlas(container, targetRole);
      return;
    }

    var containerWidth = container.clientWidth || 800;
    var layout = calculateLayout(territories, containerWidth);

    var svg = svgEl('svg', {
      'class': 'atlas-svg',
      'viewBox': '0 0 ' + containerWidth + ' ' + layout.totalHeight,
      'role': 'img',
      'aria-label': 'Engineering Atlas showing skill signals across territories'
    });

    // Grid background lines
    renderGrid(svg, containerWidth, layout.totalHeight);

    // Group for dynamic paths
    var pathsG = svgEl('g', { 'class': 'atlas-paths' });
    svg.appendChild(pathsG);

    // Render each territory
    var allSignalEls = [];
    var allLandmarkEls = [];
    var signalDataMap = {};

    layout.positions.forEach(function(pos) {
      var result = renderTerritory(svg, pos, options);
      allSignalEls = allSignalEls.concat(result.signalEls);
      allLandmarkEls = allLandmarkEls.concat(result.landmarkEls);
      Object.keys(result.signalDataMap).forEach(function(k) {
        signalDataMap[k] = result.signalDataMap[k];
      });
    });

    container.appendChild(svg);

    // Build legend
    renderLegend(container);

    // Build mobile summary
    renderMobileSummary(container, territories);

    // Store references for interaction
    container._atlasData = {
      signalEls: allSignalEls,
      landmarkEls: allLandmarkEls,
      signalDataMap: signalDataMap,
      svg: svg,
      pathsG: pathsG
    };
  }

  // ── Render grid lines ─────────────────────────────
  function renderGrid(svg, width, height) {
    var g = svgEl('g', { 'class': 'atlas-grid', 'aria-hidden': 'true' });
    var step = 60;
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

  // ── Render territory ──────────────────────────────
  function renderTerritory(svg, pos, options) {
    var t = pos.territory;
    var g = svgEl('g', { 'class': 'atlas-territory' });

    // Territory boundary (dashed rectangle)
    g.appendChild(svgEl('rect', {
      'class': 'atlas-territory-bg',
      x: pos.x, y: pos.y,
      width: pos.width, height: pos.height,
      rx: 4
    }));

    // Territory label
    g.appendChild(svgText(t.category.toUpperCase(), {
      'class': 'atlas-territory-label',
      x: pos.x + 8,
      y: pos.y + 16
    }));

    var signalEls = [];
    var landmarkEls = [];
    var signalDataMap = {};
    var yOffset = pos.y + TERRITORY_HEADER;

    // Render landmarks with their signals
    t.landmarks.forEach(function(landmark) {
      // Landmark diamond
      var lmX = pos.x + 12;
      var lmY = yOffset;

      var lmG = svgEl('g', {
        'class': 'atlas-landmark',
        'data-project-id': landmark.project_id,
        'role': 'button',
        'tabindex': '0',
        'aria-label': 'Project: ' + escapeHtml(landmark.project_name)
      });

      var diamond = svgEl('rect', {
        'class': 'atlas-landmark-icon',
        x: lmX - LANDMARK_SIZE/2,
        y: lmY - LANDMARK_SIZE/2,
        width: LANDMARK_SIZE,
        height: LANDMARK_SIZE,
        transform: 'rotate(45 ' + lmX + ' ' + lmY + ')'
      });
      lmG.appendChild(diamond);

      lmG.appendChild(svgText(landmark.project_name, {
        'class': 'atlas-landmark-label',
        x: lmX + LABEL_OFFSET,
        y: lmY + 4
      }));

      svg.appendChild(lmG);
      landmarkEls.push(lmG);
      yOffset += ROW_HEIGHT_PER_SIGNAL * 0.6;

      // Render signals for this landmark
      landmark.signals.forEach(function(signal) {
        var sX = pos.x + 32;
        var sY = yOffset;
        var stateClass = 'atlas-signal-' + (signal.state || 'MISSING').toLowerCase();
        var key = 'signal-' + signal.skill_id;

        var sG = svgEl('g', {
          'class': 'atlas-signal ' + stateClass,
          'data-skill-id': signal.skill_id,
          'data-skill-name': signal.skill_name,
          'data-state': signal.state,
          'role': 'button',
          'tabindex': '0',
          'aria-label': signal.skill_name + ': ' + signal.state
        });

        sG.appendChild(svgEl('circle', {
          'class': 'atlas-signal-dot',
          cx: sX, cy: sY, r: SIGNAL_RADIUS
        }));

        sG.appendChild(svgText(signal.skill_name, {
          'class': 'atlas-signal-label',
          x: sX + LABEL_OFFSET,
          y: sY + 4
        }));

        // State badge text
        sG.appendChild(svgText(signal.state, {
          'class': 'atlas-signal-label',
          x: pos.x + pos.width - 8,
          y: sY + 4,
          'text-anchor': 'end',
          'fill': STATE_COLORS[signal.state] || STATE_COLORS.MISSING,
          'font-size': '9px',
          'font-weight': '600',
          'letter-spacing': '0.08em'
        }));

        svg.appendChild(sG);
        signalEls.push(sG);
        signalDataMap[key] = {
          signal: signal,
          landmark: { id: landmark.project_id, x: lmX, y: lmY },
          el: sG,
          x: sX, y: sY
        };

        // Click handler — Follow the Proof
        (function(sig, sk, sn, st) {
          sG.addEventListener('click', function() {
            highlightSignal(container, sk);
            if (typeof window.openEvidenceExplorer === 'function') {
              window.openEvidenceExplorer(sk, sn, st);
            }
          });
          sG.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              sG.click();
            }
          });
        })(signal, signal.skill_id, signal.skill_name, signal.state);

        yOffset += ROW_HEIGHT_PER_SIGNAL;
      });
    });

    // Render unexplored signals
    t.unexplored.forEach(function(ue) {
      var sX = pos.x + 32;
      var sY = yOffset;
      var key = 'signal-' + ue.skill_id;

      var sG = svgEl('g', {
        'class': 'atlas-signal atlas-signal-missing',
        'data-skill-id': ue.skill_id,
        'data-skill-name': ue.skill_name,
        'data-state': 'UNEXPLORED',
        'role': 'button',
        'tabindex': '0',
        'aria-label': ue.skill_name + ': Unexplored'
      });

      sG.appendChild(svgEl('circle', {
        'class': 'atlas-signal-dot',
        cx: sX, cy: sY, r: SIGNAL_RADIUS
      }));

      sG.appendChild(svgText(ue.skill_name, {
        'class': 'atlas-signal-label',
        x: sX + LABEL_OFFSET,
        y: sY + 4,
        'fill': '#7D7A73'
      }));

      sG.appendChild(svgText('UNEXPLORED', {
        'class': 'atlas-signal-label',
        x: pos.x + pos.width - 8,
        y: sY + 4,
        'text-anchor': 'end',
        'fill': '#7D7A73',
        'font-size': '9px',
        'font-weight': '600',
        'letter-spacing': '0.08em'
      }));

      svg.appendChild(sG);
      signalEls.push(sG);
      signalDataMap[key] = {
        signal: { skill_id: ue.skill_id, skill_name: ue.skill_name, state: 'MISSING', evidence: [] },
        landmark: null,
        el: sG,
        x: sX, y: sY
      };

      sG.addEventListener('click', function() {
        highlightSignal(container, ue.skill_id);
        if (typeof window.openEvidenceExplorer === 'function') {
          window.openEvidenceExplorer(ue.skill_id, ue.skill_name, 'MISSING');
        }
      });
      sG.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); sG.click(); }
      });

      yOffset += ROW_HEIGHT_PER_SIGNAL;
    });

    svg.appendChild(g);
    return { signalEls: signalEls, landmarkEls: landmarkEls, signalDataMap: signalDataMap };
  }

  // ── Highlight signal (Follow the Proof) ───────────
  function highlightSignal(container, skillId) {
    if (!container || !container._atlasData) return;
    var data = container._atlasData;
    var key = 'signal-' + skillId;
    var target = data.signalDataMap[key];

    // Clear existing paths
    data.pathsG.innerHTML = '';

    // Dim all others
    data.signalEls.forEach(function(el) {
      el.classList.toggle('dimmed', el.getAttribute('data-skill-id') != skillId);
      el.classList.toggle('highlighted', el.getAttribute('data-skill-id') == skillId);
    });
    data.landmarkEls.forEach(function(el) {
      if (target && target.landmark) {
        el.classList.toggle('dimmed',
          el.getAttribute('data-project-id') != target.landmark.id
        );
      } else {
        el.classList.add('dimmed');
      }
    });

    // Draw SVG route line
    if (target && target.landmark && target.landmark.x !== undefined) {
       var pathD = 'M ' + target.landmark.x + ' ' + (target.landmark.y + 4) + 
                   ' L ' + target.landmark.x + ' ' + target.y + 
                   ' L ' + (target.x - 10) + ' ' + target.y;
       var pathEl = svgEl('path', {
         'class': 'atlas-proof-path visible',
         'd': pathD
       });
       data.pathsG.appendChild(pathEl);
    }
  }

  // ── Clear highlight ───────────────────────────────
  function clearHighlight(container) {
    if (!container || !container._atlasData) return;
    var data = container._atlasData;
    data.pathsG.innerHTML = '';
    data.signalEls.forEach(function(el) {
      el.classList.remove('dimmed', 'highlighted');
    });
    data.landmarkEls.forEach(function(el) {
      el.classList.remove('dimmed');
    });
  }

  // ── Render legend ─────────────────────────────────
  function renderLegend(container) {
    // Remove existing legend
    var existing = container.querySelector('.atlas-legend');
    if (existing) existing.remove();

    var legend = document.createElement('div');
    legend.className = 'atlas-legend';
    legend.setAttribute('aria-label', 'Atlas legend');

    var items = [
      { label: 'Proven', cls: 'atlas-legend-dot-strong' },
      { label: 'Developing', cls: 'atlas-legend-dot-developing' },
      { label: 'Weak', cls: 'atlas-legend-dot-weak' },
      { label: 'Unexplored', cls: 'atlas-legend-dot-missing' }
    ];

    items.forEach(function(item) {
      var div = document.createElement('div');
      div.className = 'atlas-legend-item';
      var dot = document.createElement('span');
      dot.className = 'atlas-legend-dot ' + item.cls;
      var text = document.createElement('span');
      text.textContent = item.label;
      div.appendChild(dot);
      div.appendChild(text);
      legend.appendChild(div);
    });

    container.appendChild(legend);
  }

  // ── Render mobile summary ─────────────────────────
  function renderMobileSummary(container, territories) {
    var existing = container.querySelector('.atlas-mobile-grid');
    if (existing) existing.remove();

    var wrapper = document.createElement('div');
    wrapper.className = 'atlas-mobile-grid';

    territories.forEach(function(t) {
      var territoryDiv = document.createElement('div');
      territoryDiv.className = 'atlas-mobile-territory';

      var tLabel = document.createElement('div');
      tLabel.className = 'atlas-mobile-territory-label';
      tLabel.textContent = t.category.toUpperCase();
      territoryDiv.appendChild(tLabel);

      t.landmarks.forEach(function(lm) {
        var lmDiv = document.createElement('div');
        lmDiv.className = 'atlas-mobile-landmark';
        
        var lmHeader = document.createElement('div');
        lmHeader.className = 'atlas-mobile-landmark-header';
        lmHeader.innerHTML = '<span class="atlas-mobile-landmark-icon"></span>' + escapeHtml(lm.project_name);
        lmDiv.appendChild(lmHeader);

        var signalsList = document.createElement('div');
        signalsList.className = 'atlas-mobile-signals';

        lm.signals.forEach(function(s) {
          var state = s.state || 'MISSING';
          var item = document.createElement('div');
          item.className = 'atlas-mobile-item';

          var dot = document.createElement('span');
          dot.className = 'atlas-mobile-dot';
          dot.style.background = STATE_COLORS[state] || STATE_COLORS.MISSING;

          var name = document.createElement('span');
          name.className = 'atlas-mobile-item-name';
          name.textContent = s.skill_name;

          item.appendChild(dot);
          item.appendChild(name);
          signalsList.appendChild(item);

          item.addEventListener('click', function() {
            if (typeof window.openEvidenceExplorer === 'function') {
              window.openEvidenceExplorer(s.skill_id, s.skill_name, state);
            }
          });
        });

        lmDiv.appendChild(signalsList);
        territoryDiv.appendChild(lmDiv);
      });

      if (t.unexplored && t.unexplored.length > 0) {
        var uHeader = document.createElement('div');
        uHeader.className = 'atlas-mobile-landmark-header';
        uHeader.style.color = 'var(--muted)';
        uHeader.textContent = 'Unexplored Signals';
        territoryDiv.appendChild(uHeader);

        var uList = document.createElement('div');
        uList.className = 'atlas-mobile-signals';

        t.unexplored.forEach(function(u) {
          var item = document.createElement('div');
          item.className = 'atlas-mobile-item';

          var dot = document.createElement('span');
          dot.className = 'atlas-mobile-dot atlas-mobile-dot-unexplored';

          var name = document.createElement('span');
          name.className = 'atlas-mobile-item-name';
          name.style.color = 'var(--muted)';
          name.textContent = u.skill_name;

          item.appendChild(dot);
          item.appendChild(name);
          uList.appendChild(item);

          item.addEventListener('click', function() {
            if (typeof window.openEvidenceExplorer === 'function') {
              window.openEvidenceExplorer(u.skill_id, u.skill_name, 'MISSING');
            }
          });
        });
        territoryDiv.appendChild(uList);
      }

      wrapper.appendChild(territoryDiv);
    });

    container.appendChild(wrapper);
  }

  // ── Empty atlas ───────────────────────────────────
  function renderEmptyAtlas(container, targetRole) {
    var div = document.createElement('div');
    div.className = 'atlas-empty';

    var title = document.createElement('div');
    title.className = 'atlas-empty-title';
    title.textContent = 'Your engineering atlas is waiting';

    var desc = document.createElement('p');
    desc.className = 'atlas-empty-desc';
    desc.textContent = 'Connect a GitHub repository and sync it to begin mapping your engineering identity. ' +
      'NEXUS will analyze your actual work to discover evidence and calculate skill signals.';

    var cta = document.createElement('a');
    cta.href = '/projects';
    cta.className = 'btn btn-primary';
    cta.textContent = 'Add Your First Project';

    div.appendChild(title);
    div.appendChild(desc);
    div.appendChild(cta);
    container.appendChild(div);
  }

  // Public API
  return {
    render: render,
    highlightSignal: highlightSignal,
    clearHighlight: clearHighlight
  };

})();
