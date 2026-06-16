// === Batch 5: SVG Chart & Data Viz Atoms ===

// Helper for linear scale (local to this batch)
function _linScale(val, domMin, domMax, rangeMin, rangeMax) {
  if (domMax === domMin) return rangeMin;
  return rangeMin + (val - domMin) / (domMax - domMin) * (rangeMax - rangeMin);
}

// Default color palette for charts
var _CHART_PALETTE = ['#6366f1','#22d3ee','#34d399','#fb923c','#f472b6','#a78bfa','#facc15','#818cf8','#e879f9','#2dd4bf'];

// ─────────────────────────────────────────────────────────
// 1. chartjs_bar — SVG horizontal or vertical bar chart
// ─────────────────────────────────────────────────────────
_RENDERERS['chartjs_bar'] = function(b) {
  var data        = b.data || [];
  var title       = b.title || '';
  var orientation = b.orientation || 'vertical';
  var height      = parseInt(b.height) || 220;
  var width       = parseInt(b.width)  || 560;
  var showVals    = b.show_values === true || b.show_values === 'true';
  var barColor    = b.bar_color || '#6366f1';

  if (!data.length) return '<div class="a2ui-chart-empty">No data</div>';

  var vals   = data.map(function(d){ return parseFloat(d.value) || 0; });
  var maxVal = Math.max.apply(null, vals);
  if (maxVal === 0) maxVal = 1;

  var svg = '';

  if (orientation === 'horizontal') {
    // Horizontal bars
    var padL = 120, padR = 60, padT = 30, padB = 20;
    var barH     = 22;
    var barGap   = 10;
    var totalH   = padT + data.length * (barH + barGap) + padB;
    var chartW   = width - padL - padR;

    svg += '<svg viewBox="0 0 ' + width + ' ' + totalH + '" width="100%" preserveAspectRatio="xMidYMid meet">';
    if (title) svg += '<text x="' + (width/2) + '" y="18" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

    // Gridlines
    for (var g = 0; g <= 4; g++) {
      var gx = padL + (g / 4) * chartW;
      var gv = Math.round(maxVal * g / 4);
      svg += '<line x1="' + gx + '" y1="' + padT + '" x2="' + gx + '" y2="' + (totalH - padB) + '" stroke="#e2e8f0" stroke-width="1"/>';
      svg += '<text x="' + gx + '" y="' + (padT - 5) + '" text-anchor="middle" font-size="9" fill="#94a3b8">' + gv + '</text>';
    }

    data.forEach(function(d, i) {
      var val   = parseFloat(d.value) || 0;
      var bw    = _linScale(val, 0, maxVal, 0, chartW);
      var y     = padT + i * (barH + barGap);
      var color = d.color || barColor;
      svg += '<text x="' + (padL - 6) + '" y="' + (y + barH/2 + 4) + '" text-anchor="end" font-size="11" fill="#334155">' + _esc((d.label||'').substr(0,16)) + '</text>';
      svg += '<rect x="' + padL + '" y="' + y + '" width="' + bw + '" height="' + barH + '" rx="3" fill="' + _esc(color) + '"/>';
      if (showVals) {
        svg += '<text x="' + (padL + bw + 4) + '" y="' + (y + barH/2 + 4) + '" font-size="10" fill="#475569">' + val + '</text>';
      }
    });

    svg += '</svg>';
  } else {
    // Vertical bars
    var padL = 45, padR = 15, padT = 30, padB = 38;
    var chartH = height - padT - padB;
    var chartW = width  - padL - padR;
    var barW   = Math.max(8, (chartW / data.length) * 0.6);
    var barSpacing = chartW / data.length;

    svg += '<svg viewBox="0 0 ' + width + ' ' + height + '" width="100%" preserveAspectRatio="xMidYMid meet">';
    if (title) svg += '<text x="' + (width/2) + '" y="18" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

    // Horizontal gridlines
    for (var g = 0; g <= 4; g++) {
      var gy = padT + (1 - g/4) * chartH;
      var gv = Math.round(maxVal * g / 4);
      svg += '<line x1="' + padL + '" y1="' + gy + '" x2="' + (width - padR) + '" y2="' + gy + '" stroke="#e2e8f0" stroke-width="1"/>';
      svg += '<text x="' + (padL - 4) + '" y="' + (gy + 4) + '" text-anchor="end" font-size="9" fill="#94a3b8">' + gv + '</text>';
    }

    // Baseline
    svg += '<line x1="' + padL + '" y1="' + (padT + chartH) + '" x2="' + (width - padR) + '" y2="' + (padT + chartH) + '" stroke="#cbd5e1" stroke-width="1.5"/>';

    data.forEach(function(d, i) {
      var val   = parseFloat(d.value) || 0;
      var bh    = _linScale(val, 0, maxVal, 0, chartH);
      var cx    = padL + (i + 0.5) * barSpacing;
      var x     = cx - barW / 2;
      var y     = padT + chartH - bh;
      var color = d.color || barColor;
      svg += '<rect x="' + x + '" y="' + y + '" width="' + barW + '" height="' + bh + '" rx="3" fill="' + _esc(color) + '"/>';
      if (showVals && bh > 12) {
        svg += '<text x="' + cx + '" y="' + (y - 3) + '" text-anchor="middle" font-size="9" fill="#475569">' + val + '</text>';
      }
      var lbl = (d.label||'').substr(0,10);
      svg += '<text x="' + cx + '" y="' + (padT + chartH + 14) + '" text-anchor="middle" font-size="10" fill="#64748b">' + _esc(lbl) + '</text>';
    });

    svg += '</svg>';
  }

  return '<div class="a2ui-chartjs-bar">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 2. chartjs_line — SVG line/area chart
// ─────────────────────────────────────────────────────────
_RENDERERS['chartjs_line'] = function(b) {
  var title      = b.title || '';
  var height     = parseInt(b.height) || 260;
  var width      = parseInt(b.width)  || 560;
  var smooth     = b.smooth === true || b.smooth === 'true';
  var showPts    = b.show_points !== false && b.show_points !== 'false';
  var areaFill   = b.area_fill === true || b.area_fill === 'true';

  // Normalise to multi-dataset form
  var datasets, labels;
  if (b.datasets) {
    datasets = b.datasets;
    labels   = b.labels || datasets[0].data.map(function(_, i){ return String(i); });
  } else if (b.data) {
    labels   = b.data.map(function(d){ return d.label || ''; });
    datasets = [{ label: title, data: b.data.map(function(d){ return parseFloat(d.value)||0; }), color: '#6366f1' }];
    title    = '';
  } else {
    return '<div class="a2ui-chart-empty">No data</div>';
  }

  var padL = 50, padR = 20, padT = 36, padB = 50;
  var chartH = height - padT - padB;
  var chartW = width  - padL - padR;

  // Compute global min/max
  var allVals = [];
  datasets.forEach(function(ds){ ds.data.forEach(function(v){ allVals.push(parseFloat(v)||0); }); });
  var minVal = Math.min.apply(null, allVals);
  var maxVal = Math.max.apply(null, allVals);
  if (maxVal === minVal) { maxVal += 1; minVal -= 1; }

  var n = labels.length;

  function px(i)  { return padL + (n > 1 ? i / (n - 1) : 0.5) * chartW; }
  function py(v)  { return padT + (1 - (v - minVal) / (maxVal - minVal)) * chartH; }

  var svg = '<svg viewBox="0 0 ' + width + ' ' + height + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + (width/2) + '" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  // Gridlines
  for (var g = 0; g <= 4; g++) {
    var gy = padT + (g / 4) * chartH;
    var gv = maxVal - (maxVal - minVal) * g / 4;
    svg += '<line x1="' + padL + '" y1="' + gy + '" x2="' + (width - padR) + '" y2="' + gy + '" stroke="#e2e8f0" stroke-width="1"/>';
    svg += '<text x="' + (padL - 4) + '" y="' + (gy + 4) + '" text-anchor="end" font-size="9" fill="#94a3b8">' + Math.round(gv) + '</text>';
  }

  // X-axis labels
  labels.forEach(function(lbl, i) {
    if (n <= 12 || i % Math.ceil(n / 10) === 0) {
      svg += '<text x="' + px(i) + '" y="' + (padT + chartH + 14) + '" text-anchor="middle" font-size="9" fill="#64748b">' + _esc((lbl||'').substr(0,8)) + '</text>';
    }
  });

  // Datasets
  datasets.forEach(function(ds, di) {
    var color = ds.color || _CHART_PALETTE[di % _CHART_PALETTE.length];
    var pts   = ds.data.map(function(v, i){ return { x: px(i), y: py(parseFloat(v)||0) }; });
    if (!pts.length) return;

    // Build path
    var pathD = '';
    if (smooth && pts.length > 2) {
      pathD = 'M ' + pts[0].x + ' ' + pts[0].y;
      for (var i = 0; i < pts.length - 1; i++) {
        var cp1x = pts[i].x + (pts[i+1].x - pts[i].x) / 3;
        var cp1y = pts[i].y;
        var cp2x = pts[i+1].x - (pts[i+1].x - pts[i].x) / 3;
        var cp2y = pts[i+1].y;
        pathD += ' C ' + cp1x + ' ' + cp1y + ' ' + cp2x + ' ' + cp2y + ' ' + pts[i+1].x + ' ' + pts[i+1].y;
      }
    } else {
      pathD = pts.map(function(p, i){ return (i ? 'L' : 'M') + p.x + ' ' + p.y; }).join(' ');
    }

    // Area fill
    if (areaFill || ds.fill) {
      var areaD = pathD + ' L ' + pts[pts.length-1].x + ' ' + (padT + chartH) + ' L ' + pts[0].x + ' ' + (padT + chartH) + ' Z';
      svg += '<path d="' + areaD + '" fill="' + _esc(color) + '" fill-opacity="0.18" stroke="none"/>';
    }

    svg += '<path d="' + pathD + '" fill="none" stroke="' + _esc(color) + '" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>';

    if (showPts) {
      pts.forEach(function(p) {
        svg += '<circle cx="' + p.x + '" cy="' + p.y + '" r="3.5" fill="' + _esc(color) + '" stroke="#fff" stroke-width="1.5"/>';
      });
    }
  });

  // Legend
  if (datasets.length > 1 || (datasets.length === 1 && datasets[0].label)) {
    var legY = padT + chartH + 28;
    var legX = padL;
    datasets.forEach(function(ds, di) {
      var color = ds.color || _CHART_PALETTE[di % _CHART_PALETTE.length];
      svg += '<rect x="' + legX + '" y="' + (legY - 7) + '" width="12" height="3" rx="1.5" fill="' + _esc(color) + '"/>';
      svg += '<text x="' + (legX + 16) + '" y="' + legY + '" font-size="10" fill="#64748b">' + _esc(ds.label||'') + '</text>';
      legX += 80;
    });
  }

  svg += '</svg>';
  return '<div class="a2ui-chartjs-line">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 3. chartjs_pie — SVG pie/donut chart
// ─────────────────────────────────────────────────────────
_RENDERERS['chartjs_pie'] = function(b) {
  var data       = b.data || [];
  var title      = b.title || '';
  var donut      = b.donut === true || b.donut === 'true';
  var innerLabel = b.inner_label || '';
  var height     = parseInt(b.height) || 260;

  if (!data.length) return '<div class="a2ui-chart-empty">No data</div>';

  var total = data.reduce(function(s, d){ return s + (parseFloat(d.value)||0); }, 0);
  if (!total) return '<div class="a2ui-chart-empty">No data</div>';

  var width  = height;
  var cx     = width / 2;
  var cy     = height / 2 - 10;
  var r      = Math.min(cx, cy) - 10;

  var svg = '<svg viewBox="0 0 ' + width + ' ' + (height + 30) + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + cx + '" y="14" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  var startAngle = -Math.PI / 2;
  var colors = _CHART_PALETTE;

  data.forEach(function(d, i) {
    var val      = parseFloat(d.value) || 0;
    var pct      = val / total;
    var endAngle = startAngle + pct * 2 * Math.PI;
    var x1       = cx + r * Math.cos(startAngle);
    var y1       = cy + r * Math.sin(startAngle);
    var x2       = cx + r * Math.cos(endAngle);
    var y2       = cy + r * Math.sin(endAngle);
    var largeArc = pct > 0.5 ? 1 : 0;
    var color    = d.color || colors[i % colors.length];

    var pathD = 'M ' + cx + ' ' + cy + ' L ' + x1 + ' ' + y1 +
                ' A ' + r + ' ' + r + ' 0 ' + largeArc + ' 1 ' + x2 + ' ' + y2 + ' Z';
    svg += '<path d="' + pathD + '" fill="' + _esc(color) + '" stroke="#fff" stroke-width="1.5"/>';
    startAngle = endAngle;
  });

  // Donut hole
  if (donut) {
    var ir = r * 0.55;
    svg += '<circle cx="' + cx + '" cy="' + cy + '" r="' + ir + '" fill="#fff"/>';
    if (innerLabel) {
      svg += '<text x="' + cx + '" y="' + (cy + 5) + '" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(innerLabel) + '</text>';
    }
  }

  // Legend below
  var legCols = Math.min(data.length, 3);
  var legW    = width / legCols;
  data.forEach(function(d, i) {
    var color = d.color || colors[i % colors.length];
    var lx    = (i % legCols) * legW + 4;
    var ly    = height + Math.floor(i / legCols) * 16 + 8;
    svg += '<rect x="' + lx + '" y="' + (ly - 8) + '" width="10" height="10" rx="2" fill="' + _esc(color) + '"/>';
    svg += '<text x="' + (lx + 13) + '" y="' + ly + '" font-size="9" fill="#64748b">' + _esc((d.label||'').substr(0,14)) + '</text>';
  });

  svg += '</svg>';
  return '<div class="a2ui-chartjs-pie">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 4. benchmark_comparison — horizontal bar comparison
// ─────────────────────────────────────────────────────────
_RENDERERS['benchmark_comparison'] = function(b) {
  var items = b.benchmarks || [];
  var title = b.title || '';

  if (!items.length) return '<div class="a2ui-chart-empty">No benchmarks</div>';

  var vals   = items.map(function(d){ return parseFloat(d.value)||0; });
  var globalMax = Math.max.apply(null, vals);

  var padL = 130, padR = 80, padT = 30, rowH = 36, rowGap = 4;
  var width  = 560;
  var totalH = padT + items.length * (rowH + rowGap) + 20;
  var chartW = width - padL - padR;

  var svg = '<svg viewBox="0 0 ' + width + ' ' + totalH + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + (width/2) + '" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  items.forEach(function(d, i) {
    var val    = parseFloat(d.value) || 0;
    var maxV   = parseFloat(d.max_value) || globalMax || 1;
    var pct    = Math.min(val / maxV, 1);
    var bw     = pct * chartW;
    var y      = padT + i * (rowH + rowGap);
    var color  = d.color || _CHART_PALETTE[i % _CHART_PALETTE.length];
    var unit   = d.unit || '';

    // Alternating row bg
    if (i % 2 === 0) {
      svg += '<rect x="0" y="' + y + '" width="' + width + '" height="' + rowH + '" fill="#f8fafc" rx="2"/>';
    }

    // Label
    svg += '<text x="' + (padL - 8) + '" y="' + (y + rowH/2 + 4) + '" text-anchor="end" font-size="11" fill="#334155">' + _esc((d.name||'').substr(0,18)) + '</text>';

    // Bar track
    svg += '<rect x="' + padL + '" y="' + (y + 8) + '" width="' + chartW + '" height="' + (rowH - 16) + '" rx="4" fill="#e2e8f0"/>';
    // Bar fill
    if (bw > 0) {
      svg += '<rect x="' + padL + '" y="' + (y + 8) + '" width="' + bw + '" height="' + (rowH - 16) + '" rx="4" fill="' + _esc(color) + '"/>';
    }

    // Value
    svg += '<text x="' + (padL + chartW + 6) + '" y="' + (y + rowH/2 + 4) + '" font-size="11" font-weight="600" fill="#1e293b">' + _esc(String(val) + (unit ? ' '+unit : '')) + '</text>';
  });

  svg += '</svg>';
  return '<div class="a2ui-benchmark-comparison">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 5. data_table_sortable — styled data table
// ─────────────────────────────────────────────────────────
_RENDERERS['data_table_sortable'] = function(b) {
  var columns = b.columns || [];
  var rows    = b.rows    || [];
  var title   = b.title   || '';
  var striped = b.striped === true || b.striped === 'true';
  var compact = b.compact === true || b.compact === 'true';
  var uid     = Math.random().toString(36).substr(2,6);

  if (!columns.length && rows.length) {
    columns = Object.keys(rows[0]).map(function(k){ return { key: k, label: k }; });
  }
  if (!columns.length) return '<div class="a2ui-chart-empty">No columns defined</div>';

  var cellPad = compact ? '4px 8px' : '8px 12px';

  var html = '';
  if (title) html += '<div class="a2ui-table-title">' + _esc(title) + '</div>';

  html += '<div class="a2ui-table-wrap" style="overflow-x:auto;">';
  html += '<table id="tbl-' + uid + '" class="a2ui-data-table' + (striped ? ' striped' : '') + '" style="width:100%;border-collapse:collapse;font-size:13px;">';

  // Header
  html += '<thead><tr>';
  columns.forEach(function(col) {
    var align = col.type === 'number' ? 'right' : 'left';
    html += '<th data-key="' + _esc(col.key||'') + '" style="background:#1e293b;color:#f1f5f9;padding:' + cellPad + ';text-align:' + align + ';cursor:pointer;user-select:none;white-space:nowrap;" onclick="(function(th){var tbl=th.closest(\'table\');var idx=Array.from(th.parentNode.children).indexOf(th);var asc=th.dataset.asc!==\'1\';th.dataset.asc=asc?\'1\':\'\';Array.from(tbl.querySelectorAll(\'th\')).forEach(function(t){t.textContent=t.textContent.replace(/ [▲▼]$/,\'\');});th.textContent+=(asc?\' ▲\':\' ▼\');var tbody=tbl.querySelector(\'tbody\');var rowsArr=Array.from(tbody.querySelectorAll(\'tr\'));rowsArr.sort(function(a,b){var av=a.cells[idx]?a.cells[idx].textContent:\'\',bv=b.cells[idx]?b.cells[idx].textContent:\'\';var an=parseFloat(av),bn=parseFloat(bv);if(!isNaN(an)&&!isNaN(bn))return asc?an-bn:bn-an;return asc?av.localeCompare(bv):bv.localeCompare(av);});rowsArr.forEach(function(r){tbody.appendChild(r);});})(this)">';
    html += _esc(col.label || col.key || '');
    html += '</th>';
  });
  html += '</tr></thead>';

  // Body
  html += '<tbody>';
  rows.forEach(function(row, ri) {
    var bg = '';
    if (striped && ri % 2 === 1) bg = 'background:#f8fafc;';
    html += '<tr style="' + bg + '">';
    columns.forEach(function(col) {
      var val   = row[col.key];
      var align = col.type === 'number' ? 'right' : 'left';
      var disp  = (val === null || val === undefined) ? '' : String(val);
      html += '<td style="padding:' + cellPad + ';text-align:' + align + ';border-bottom:1px solid #f1f5f9;color:#334155;">' + _esc(disp) + '</td>';
    });
    html += '</tr>';
  });
  html += '</tbody></table></div>';

  return '<div class="a2ui-data-table-sortable">' + html + '</div>';
};

// ─────────────────────────────────────────────────────────
// 6. metric_comparison_card — compare two metrics
// ─────────────────────────────────────────────────────────
_RENDERERS['metric_comparison_card'] = function(b) {
  var baseline   = b.baseline   || {};
  var comparison = b.comparison || {};
  var title      = b.title || '';
  var higherBetter = b.higher_is_better !== false && b.higher_is_better !== 'false';

  var bVal  = parseFloat(baseline.value)   || 0;
  var cVal  = parseFloat(comparison.value) || 0;
  var delta = bVal !== 0 ? ((cVal - bVal) / Math.abs(bVal)) * 100 : 0;
  var better = higherBetter ? (cVal >= bVal) : (cVal <= bVal);
  var deltaColor = better ? '#16a34a' : '#dc2626';
  var arrow      = cVal >= bVal ? '↑' : '↓';
  var deltaTxt   = (delta >= 0 ? '+' : '') + delta.toFixed(1) + '%';

  var html = '<div class="a2ui-metric-comparison">';
  if (title) html += '<div class="a2ui-metric-cmp-title">' + _esc(title) + '</div>';
  html += '<div class="a2ui-metric-cmp-body">';

  // Baseline
  html += '<div class="a2ui-metric-cmp-col">';
  html += '<div class="a2ui-metric-cmp-lbl">' + _esc(baseline.label || 'Baseline') + '</div>';
  html += '<div class="a2ui-metric-cmp-val">' + _esc(String(bVal)) + (baseline.unit ? ' <span class="a2ui-metric-unit">' + _esc(baseline.unit) + '</span>' : '') + '</div>';
  html += '</div>';

  // Delta badge
  html += '<div class="a2ui-metric-cmp-delta" style="color:' + deltaColor + ';border-color:' + deltaColor + ';">' + arrow + ' ' + _esc(deltaTxt) + '</div>';

  // Comparison
  html += '<div class="a2ui-metric-cmp-col">';
  html += '<div class="a2ui-metric-cmp-lbl">' + _esc(comparison.label || 'Comparison') + '</div>';
  html += '<div class="a2ui-metric-cmp-val">' + _esc(String(cVal)) + (comparison.unit ? ' <span class="a2ui-metric-unit">' + _esc(comparison.unit) + '</span>' : '') + '</div>';
  html += '</div>';

  html += '</div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 7. mini_sparkline_set — multiple tiny sparklines
// ─────────────────────────────────────────────────────────
_RENDERERS['mini_sparkline_set'] = function(b) {
  var sparklines = b.sparklines || [];
  if (!sparklines.length) return '<div class="a2ui-chart-empty">No sparklines</div>';

  var html = '<div class="a2ui-sparkline-set">';

  sparklines.forEach(function(sp) {
    var data  = (sp.data || []).map(function(v){ return parseFloat(v)||0; });
    var color = sp.color || '#6366f1';
    var label = sp.label || '';
    var unit  = sp.unit  || '';
    var last  = data.length ? data[data.length-1] : 0;

    var svgW = 80, svgH = 30;
    var minV = Math.min.apply(null, data);
    var maxV = Math.max.apply(null, data);
    if (maxV === minV) { maxV += 1; }
    var n    = data.length;

    var pts = data.map(function(v, i) {
      var x = n > 1 ? (i / (n-1)) * svgW : svgW/2;
      var y = _linScale(v, minV, maxV, svgH - 2, 2);
      return x + ',' + y;
    }).join(' ');

    var sparkSvg = '<svg viewBox="0 0 ' + svgW + ' ' + svgH + '" width="' + svgW + '" height="' + svgH + '" style="display:inline-block;vertical-align:middle;">';
    if (data.length > 1) {
      sparkSvg += '<polyline points="' + pts + '" fill="none" stroke="' + _esc(color) + '" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>';
    }
    sparkSvg += '</svg>';

    html += '<div class="a2ui-sparkline-row">';
    html += '<span class="a2ui-sparkline-label">' + _esc(label) + '</span>';
    html += sparkSvg;
    html += '<span class="a2ui-sparkline-val" style="color:' + _esc(color) + ';">' + _esc(String(last)) + (unit ? ' '+_esc(unit) : '') + '</span>';
    html += '</div>';
  });

  html += '</div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 8. donut_stat — large donut with center stat
// ─────────────────────────────────────────────────────────
_RENDERERS['donut_stat'] = function(b) {
  var value = Math.min(100, Math.max(0, parseFloat(b.value) || 0));
  var label = b.label || '';
  var color = b.color || '#22d3ee';
  var size  = parseInt(b.size) || 160;
  var unit  = b.unit !== undefined ? String(b.unit) : '%';
  var uid   = Math.random().toString(36).substr(2,6);

  var r         = size / 2 - 14;
  var cx        = size / 2;
  var cy        = size / 2;
  var circ      = 2 * Math.PI * r;
  var dashOffset = circ * (1 - value / 100);

  var html = '';
  html += '<style>@keyframes donut-spin-' + uid + '{from{stroke-dashoffset:' + circ.toFixed(2) + '}to{stroke-dashoffset:' + dashOffset.toFixed(2) + '}}</style>';
  html += '<div class="a2ui-donut-stat" style="display:inline-block;text-align:center;">';
  html += '<svg viewBox="0 0 ' + size + ' ' + size + '" width="' + size + '" height="' + size + '">';
  // Track
  html += '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="#e2e8f0" stroke-width="12"/>';
  // Arc
  html += '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="' + _esc(color) + '" stroke-width="12" stroke-linecap="round"' +
          ' stroke-dasharray="' + circ.toFixed(2) + '"' +
          ' stroke-dashoffset="' + circ.toFixed(2) + '"' +
          ' transform="rotate(-90 ' + cx + ' ' + cy + ')"' +
          ' style="animation:donut-spin-' + uid + ' 1s ease-out forwards;"/>';
  // Center text
  html += '<text x="' + cx + '" y="' + (cy - 4) + '" text-anchor="middle" font-size="' + Math.round(size*0.18) + '" font-weight="bold" fill="#1e293b">' + _esc(String(Math.round(value))) + '</text>';
  html += '<text x="' + cx + '" y="' + (cy + Math.round(size*0.14)) + '" text-anchor="middle" font-size="' + Math.round(size*0.1) + '" fill="#64748b">' + _esc(unit) + '</text>';
  html += '</svg>';
  if (label) html += '<div class="a2ui-donut-label" style="margin-top:4px;font-size:13px;color:#64748b;">' + _esc(label) + '</div>';
  html += '</div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 9. status_dashboard — grid of status items
// ─────────────────────────────────────────────────────────
_RENDERERS['status_dashboard'] = function(b) {
  var title = b.title || 'System Status';
  var items = b.items || [];

  var statusColors = {
    operational:  '#22c55e',
    degraded:     '#f59e0b',
    outage:       '#ef4444',
    maintenance:  '#6366f1'
  };
  var statusLabels = {
    operational: 'Operational',
    degraded:    'Degraded',
    outage:      'Outage',
    maintenance: 'Maintenance'
  };

  // Overall status
  var hasOutage      = items.some(function(i){ return i.status === 'outage'; });
  var hasDegraded    = items.some(function(i){ return i.status === 'degraded'; });
  var hasMaintenance = items.some(function(i){ return i.status === 'maintenance'; });
  var overallStatus  = hasOutage ? 'outage' : hasDegraded ? 'degraded' : hasMaintenance ? 'maintenance' : 'operational';
  var overallMessages = {
    operational: 'All systems operational',
    degraded:    'Some systems are experiencing degraded performance',
    outage:      'One or more systems are experiencing an outage',
    maintenance: 'Scheduled maintenance in progress'
  };

  var html = '<div class="a2ui-status-dashboard">';
  html += '<div class="a2ui-status-header" style="background:' + statusColors[overallStatus] + ';">';
  html += '<span class="a2ui-status-dot-lg" style="background:#fff;opacity:0.9;"></span>';
  html += '<div>';
  if (title) html += '<div class="a2ui-status-title">' + _esc(title) + '</div>';
  html += '<div class="a2ui-status-overall">' + _esc(overallMessages[overallStatus]) + '</div>';
  html += '</div></div>';

  html += '<div class="a2ui-status-list">';
  items.forEach(function(item) {
    var st    = item.status || 'operational';
    var color = statusColors[st] || '#94a3b8';
    var stLbl = statusLabels[st] || st;
    html += '<div class="a2ui-status-item">';
    html += '<span class="a2ui-status-dot" style="background:' + color + ';"></span>';
    html += '<div class="a2ui-status-info">';
    html += '<span class="a2ui-status-name">' + _esc(item.name || '') + '</span>';
    if (item.description) html += '<span class="a2ui-status-desc">' + _esc(item.description) + '</span>';
    html += '</div>';
    html += '<span class="a2ui-status-pill" style="background:' + color + '20;color:' + color + ';border:1px solid ' + color + '40;">' + _esc(stLbl) + '</span>';
    html += '</div>';
  });
  html += '</div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 10. uptime_timeline — horizontal uptime bar
// ─────────────────────────────────────────────────────────
_RENDERERS['uptime_timeline'] = function(b) {
  var label   = b.label || '';
  var pct     = parseFloat(b.uptime_percent) || 100;
  var period  = b.period || '';
  var days    = b.days || [];

  function dayColor(d) {
    var s = typeof d === 'object' ? (d.status !== undefined ? d.status : 1) : d;
    var v = parseFloat(s);
    if (v >= 1)   return '#22c55e';
    if (v >= 0.5) return '#f59e0b';
    return '#ef4444';
  }
  function dayTitle(d, i) {
    if (typeof d === 'object' && d.date) return d.date;
    return 'Day ' + (i+1);
  }

  var blockW = days.length > 0 ? Math.max(2, Math.min(8, Math.floor(480 / days.length))) : 6;
  var blockH = 24;
  var gap    = 1;
  var padL   = 10, padR = 70, padT = 20;
  var width  = 560;
  var svgW   = width - padL - padR;

  var html = '<div class="a2ui-uptime-row">';

  var svg = '<svg viewBox="0 0 ' + width + ' ' + (blockH + padT + 10) + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (label) svg += '<text x="' + padL + '" y="14" font-size="12" font-weight="600" fill="#334155">' + _esc(label) + '</text>';

  var x = padL;
  days.forEach(function(d, i) {
    var color = dayColor(d);
    var ttl   = _esc(dayTitle(d, i));
    svg += '<rect x="' + x + '" y="' + padT + '" width="' + (blockW - gap) + '" height="' + blockH + '" rx="1.5" fill="' + color + '"><title>' + ttl + '</title></rect>';
    x += blockW;
  });

  // Fill remaining space gray if blocks don't fill width
  if (days.length === 0) {
    svg += '<rect x="' + padL + '" y="' + padT + '" width="' + svgW + '" height="' + blockH + '" rx="3" fill="#e2e8f0"/>';
  }

  // Uptime badge
  var badgeColor = pct >= 99 ? '#22c55e' : pct >= 95 ? '#f59e0b' : '#ef4444';
  var bx = width - padR + 4;
  svg += '<text x="' + bx + '" y="' + (padT + blockH/2 + 5) + '" font-size="12" font-weight="700" fill="' + badgeColor + '">' + pct.toFixed(2) + '%</text>';
  if (period) svg += '<text x="' + bx + '" y="' + (padT + blockH + 10) + '" font-size="9" fill="#94a3b8">' + _esc(period) + '</text>';

  svg += '</svg>';
  html += svg + '</div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 11. command_palette — searchable command list
// ─────────────────────────────────────────────────────────
_RENDERERS['command_palette'] = function(b) {
  var commands    = b.commands || [];
  var placeholder = b.placeholder || 'Search commands…';
  var uid         = Math.random().toString(36).substr(2,6);

  // Group by category
  var groups = {};
  var order  = [];
  commands.forEach(function(cmd) {
    var cat = cmd.category || 'General';
    if (!groups[cat]) { groups[cat] = []; order.push(cat); }
    groups[cat].push(cmd);
  });

  var html = '<div class="a2ui-cmd-palette" id="cp-' + uid + '">';
  html += '<div class="a2ui-cmd-search-wrap">';
  html += '<svg class="a2ui-cmd-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';
  html += '<input class="a2ui-cmd-input" type="text" placeholder="' + _esc(placeholder) + '"' +
          ' oninput="(function(v){var items=document.querySelectorAll(\'#cp-' + uid + ' .a2ui-cmd-item\');var cats=document.querySelectorAll(\'#cp-' + uid + ' .a2ui-cmd-cat\');' +
          'items.forEach(function(el){var t=el.textContent.toLowerCase();el.style.display=t.indexOf(v.toLowerCase())>-1?\'\':\'none\';});' +
          'cats.forEach(function(cat){var anyVis=false;var next=cat.nextElementSibling;while(next&&!next.classList.contains(\'a2ui-cmd-cat\')){if(next.classList.contains(\'a2ui-cmd-item\')&&next.style.display!==\'none\')anyVis=true;next=next.nextElementSibling;}cat.style.display=anyVis?\'\':\'none\';});' +
          '})(this.value)"/>';
  html += '</div>';
  html += '<div class="a2ui-cmd-list">';

  order.forEach(function(cat) {
    html += '<div class="a2ui-cmd-cat">' + _esc(cat) + '</div>';
    groups[cat].forEach(function(cmd) {
      html += '<div class="a2ui-cmd-item">';
      html += '<span class="a2ui-cmd-name">' + _esc(cmd.name || '') + '</span>';
      if (cmd.description) html += '<span class="a2ui-cmd-desc">' + _esc(cmd.description) + '</span>';
      if (cmd.shortcut) html += '<kbd class="a2ui-cmd-shortcut">' + _esc(cmd.shortcut) + '</kbd>';
      html += '</div>';
    });
  });

  html += '</div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 12. search_result_card — Google-style search result
// ─────────────────────────────────────────────────────────
_RENDERERS['search_result_card'] = function(b) {
  var title      = b.title || '';
  var url        = b.url   || '#';
  var description= b.description || '';
  var breadcrumb = b.breadcrumb || [];
  var date       = b.date || '';
  var faviconUrl = b.favicon_url || '';

  var html = '<div class="a2ui-search-result">';

  // URL / breadcrumb row
  html += '<div class="a2ui-sr-url-row">';
  if (faviconUrl) {
    html += '<img src="' + _esc(faviconUrl) + '" class="a2ui-sr-favicon" width="16" height="16" onerror="this.style.display=\'none\'"/>';
  }
  if (breadcrumb.length) {
    html += '<span class="a2ui-sr-breadcrumb">' + breadcrumb.map(function(p){ return _esc(p); }).join(' › ') + '</span>';
  } else {
    html += '<span class="a2ui-sr-breadcrumb">' + _esc(url) + '</span>';
  }
  html += '</div>';

  // Title
  html += '<a class="a2ui-sr-title" href="' + _esc(url) + '" target="_blank" rel="noopener">' + _esc(title) + '</a>';

  // Meta (date)
  if (date) html += '<span class="a2ui-sr-date">' + _esc(date) + ' — </span>';

  // Description
  if (description) html += '<p class="a2ui-sr-desc">' + _esc(description) + '</p>';

  html += '</div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 13. punch_card — day-of-week × hour heatmap
// ─────────────────────────────────────────────────────────
_RENDERERS['punch_card'] = function(b) {
  var data  = b.data  || [];
  var title = b.title || '';

  var dayLabels  = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  var hourLabels = ['0','','','','','','6','','','','','','12','','','','','','18','','','','','23'];

  // Build lookup
  var counts = {};
  var maxCount = 0;
  data.forEach(function(d) {
    var key = d.day + '-' + d.hour;
    counts[key] = (d.count || 0);
    if (d.count > maxCount) maxCount = d.count;
  });
  if (!maxCount) maxCount = 1;

  var cellW  = 18, cellH = 18, cellG = 3;
  var padL   = 36, padT = 30, padR = 10, padB = 10;
  var svgW   = padL + 24 * (cellW + cellG) + padR;
  var svgH   = padT + 7  * (cellH + cellG) + padB;

  var svg = '<svg viewBox="0 0 ' + svgW + ' ' + svgH + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + (svgW/2) + '" y="14" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  // Hour labels
  for (var h = 0; h < 24; h++) {
    if (hourLabels[h]) {
      svg += '<text x="' + (padL + h*(cellW+cellG) + cellW/2) + '" y="' + (padT-4) + '" text-anchor="middle" font-size="8" fill="#94a3b8">' + hourLabels[h] + '</text>';
    }
  }
  // Day labels
  for (var d = 0; d < 7; d++) {
    svg += '<text x="' + (padL-4) + '" y="' + (padT + d*(cellH+cellG) + cellH/2 + 3) + '" text-anchor="end" font-size="9" fill="#64748b">' + dayLabels[d] + '</text>';
  }

  for (var day = 0; day < 7; day++) {
    for (var hour = 0; hour < 24; hour++) {
      var cnt = counts[day+'-'+hour] || 0;
      var opacity = cnt / maxCount;
      var r = 70 + Math.round(opacity * 115);
      var g = 50 + Math.round(opacity * 10);
      var bv = 200 + Math.round(opacity * 51);
      // Purple scale: light (#e9d5ff) to dark (#581c87)
      var fill = cnt === 0 ? '#f1f5f9' : 'rgb(' + Math.round(233 - opacity*152) + ',' + Math.round(213 - opacity*157) + ',' + Math.round(255 - opacity*130) + ')';
      var cx = padL + hour*(cellW+cellG);
      var cy = padT + day*(cellH+cellG);
      svg += '<rect x="' + cx + '" y="' + cy + '" width="' + cellW + '" height="' + cellH + '" rx="2" fill="' + fill + '"><title>' + dayLabels[day] + ' ' + hour + ':00 — ' + cnt + '</title></rect>';
    }
  }

  svg += '</svg>';
  return '<div class="a2ui-punch-card">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 14. sankey_flow — simple flow diagram (HTML table style)
// ─────────────────────────────────────────────────────────
_RENDERERS['sankey_flow'] = function(b) {
  var nodes = b.nodes || [];
  var links = b.links || [];
  var title = b.title || '';

  // Build node label lookup
  var nodeMap = {};
  nodes.forEach(function(n){ nodeMap[n.id] = n.label || n.id; });

  // Group links by source
  var groups = {};
  var srcOrder = [];
  links.forEach(function(lk) {
    var src = lk.source;
    if (!groups[src]) { groups[src] = []; srcOrder.push(src); }
    groups[src].push(lk);
  });

  var html = '<div class="a2ui-sankey">';
  if (title) html += '<div class="a2ui-sankey-title">' + _esc(title) + '</div>';
  html += '<div class="a2ui-sankey-rows">';

  srcOrder.forEach(function(src) {
    var lks  = groups[src];
    var total = lks.reduce(function(s, l){ return s + (parseFloat(l.value)||0); }, 0);
    html += '<div class="a2ui-sankey-group">';
    html += '<div class="a2ui-sankey-src-hdr">' + _esc(nodeMap[src] || src) + ' <span class="a2ui-sankey-total">Total: ' + total.toLocaleString() + '</span></div>';
    lks.forEach(function(lk) {
      var pct = total > 0 ? ((lk.value / total) * 100).toFixed(1) : '0';
      html += '<div class="a2ui-sankey-link">';
      html += '<span class="a2ui-sankey-from">' + _esc(nodeMap[src] || src) + '</span>';
      html += '<span class="a2ui-sankey-arrow">→</span>';
      html += '<div class="a2ui-sankey-bar-wrap"><div class="a2ui-sankey-bar" style="width:' + pct + '%;"></div></div>';
      html += '<span class="a2ui-sankey-val">' + Number(lk.value).toLocaleString() + '</span>';
      html += '<span class="a2ui-sankey-arrow">→</span>';
      html += '<span class="a2ui-sankey-to">' + _esc(nodeMap[lk.target] || lk.target) + '</span>';
      html += '</div>';
    });
    html += '</div>';
  });

  html += '</div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 15. cohort_retention — retention grid
// ─────────────────────────────────────────────────────────
_RENDERERS['cohort_retention'] = function(b) {
  var cohorts = b.cohorts || [];
  var title   = b.title   || '';

  if (!cohorts.length) return '<div class="a2ui-chart-empty">No cohort data</div>';

  var maxCols = 0;
  cohorts.forEach(function(c){ if ((c.data||[]).length > maxCols) maxCols = c.data.length; });

  var html = '<div class="a2ui-cohort-retention">';
  if (title) html += '<div class="a2ui-cohort-title">' + _esc(title) + '</div>';
  html += '<div style="overflow-x:auto;"><table class="a2ui-cohort-table" style="border-collapse:collapse;font-size:12px;width:100%;">';

  // Header
  html += '<thead><tr><th class="a2ui-cohort-th">Cohort</th>';
  for (var w = 0; w < maxCols; w++) {
    html += '<th class="a2ui-cohort-th">Week ' + w + '</th>';
  }
  html += '</tr></thead><tbody>';

  cohorts.forEach(function(cohort) {
    html += '<tr>';
    html += '<td class="a2ui-cohort-label">' + _esc(cohort.label || '') + '</td>';
    var data = cohort.data || [];
    for (var w = 0; w < maxCols; w++) {
      var val = data[w] !== undefined ? parseFloat(data[w]) : null;
      if (val === null) {
        html += '<td class="a2ui-cohort-cell" style="background:#f8fafc;"></td>';
      } else {
        var pct = Math.min(100, Math.max(0, val));
        var alpha = pct / 100;
        // purple: rgb(99,102,241) deep to light
        var r = Math.round(237 - alpha * 138);
        var g = Math.round(233 - alpha * 131);
        var bv = Math.round(254 - alpha * 13);
        var bg = 'rgb(' + r + ',' + g + ',' + bv + ')';
        var fg = pct > 60 ? '#fff' : '#334155';
        html += '<td class="a2ui-cohort-cell" style="background:' + bg + ';color:' + fg + ';">' + pct.toFixed(0) + '%</td>';
      }
    }
    html += '</tr>';
  });

  html += '</tbody></table></div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 16. heatmap — generic 2D heatmap
// ─────────────────────────────────────────────────────────
_RENDERERS['heatmap'] = function(b) {
  var rowLabels   = b.rows  || [];
  var colLabels   = b.cols  || [];
  var data        = b.data  || [];
  var title       = b.title || '';
  var colorScheme = b.color_scheme || 'purple';

  if (!rowLabels.length || !colLabels.length) return '<div class="a2ui-chart-empty">No heatmap data</div>';

  // Color schemes: [lightR,lightG,lightB, darkR,darkG,darkB]
  var schemes = {
    purple: [237,233,254, 88,28,135],
    blue:   [219,234,254, 30,58,138],
    green:  [220,252,231, 22,101,52],
    red:    [254,226,226, 127,29,29]
  };
  var cs = schemes[colorScheme] || schemes.purple;

  // Flatten to find min/max
  var allVals = [];
  data.forEach(function(row){ row.forEach(function(v){ allVals.push(parseFloat(v)||0); }); });
  var minV = Math.min.apply(null, allVals);
  var maxV = Math.max.apply(null, allVals);
  if (maxV === minV) maxV += 1;

  var padL = 80, padT = 30, cellW = Math.min(60, Math.max(28, Math.floor(480/colLabels.length))), cellH = 28;
  var svgW = padL + colLabels.length * cellW + 10;
  var svgH = padT + rowLabels.length * cellH + 16;

  var svg = '<svg viewBox="0 0 ' + svgW + ' ' + svgH + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + (svgW/2) + '" y="16" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  // Column labels
  colLabels.forEach(function(cl, ci) {
    svg += '<text x="' + (padL + ci*cellW + cellW/2) + '" y="' + (padT - 4) + '" text-anchor="middle" font-size="9" fill="#64748b">' + _esc(String(cl).substr(0,8)) + '</text>';
  });

  // Rows
  rowLabels.forEach(function(rl, ri) {
    svg += '<text x="' + (padL - 4) + '" y="' + (padT + ri*cellH + cellH/2 + 4) + '" text-anchor="end" font-size="9" fill="#64748b">' + _esc(String(rl).substr(0,12)) + '</text>';
    var rowData = data[ri] || [];
    colLabels.forEach(function(cl, ci) {
      var val   = parseFloat(rowData[ci]) || 0;
      var alpha = (val - minV) / (maxV - minV);
      var r = Math.round(cs[0] + alpha * (cs[3] - cs[0]));
      var g = Math.round(cs[1] + alpha * (cs[4] - cs[1]));
      var bv= Math.round(cs[2] + alpha * (cs[5] - cs[2]));
      var bg = 'rgb(' + r + ',' + g + ',' + bv + ')';
      var fg = alpha > 0.55 ? '#fff' : '#334155';
      var cx = padL + ci * cellW;
      var cy = padT + ri * cellH;
      svg += '<rect x="' + cx + '" y="' + cy + '" width="' + (cellW-1) + '" height="' + (cellH-1) + '" fill="' + bg + '"><title>' + _esc(String(rl)) + ' / ' + _esc(String(cl)) + ': ' + val + '</title></rect>';
      if (cellW > 30) {
        svg += '<text x="' + (cx+cellW/2) + '" y="' + (cy+cellH/2+4) + '" text-anchor="middle" font-size="9" fill="' + fg + '">' + val + '</text>';
      }
    });
  });

  svg += '</svg>';
  return '<div class="a2ui-heatmap">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 17. github_activity_grid — contribution graph
// ─────────────────────────────────────────────────────────
_RENDERERS['github_activity_grid'] = function(b) {
  var weeks = b.weeks || [];
  var title = b.title || '';
  var year  = b.year  || '';

  var cellS = 11, cellG = 2;
  var padL  = 24, padT = 24, padR = 6, padB = 6;
  var colors = ['#161b22','#0e4429','#006d32','#26a641','#39d353'];
  // 0 commits = light grey in our light-mode rendering
  var emptyColor = '#ebedf0';

  var dayLabels = {1:'Mon', 3:'Wed', 5:'Fri'};
  var svgW = padL + (weeks.length || 53) * (cellS + cellG) + padR;
  var svgH = padT + 7 * (cellS + cellG) + padB;

  var svg = '<svg viewBox="0 0 ' + svgW + ' ' + svgH + '" width="100%" preserveAspectRatio="xMidYMid meet" style="background:#fff;">';
  if (title || year) svg += '<text x="' + padL + '" y="14" font-size="11" font-weight="600" fill="#24292e">' + _esc(title + (year ? ' '+year : '')) + '</text>';

  // Day labels (left)
  [1,3,5].forEach(function(d) {
    svg += '<text x="' + (padL-2) + '" y="' + (padT + d*(cellS+cellG) + cellS/2 + 3) + '" text-anchor="end" font-size="8" fill="#57606a">' + dayLabels[d] + '</text>';
  });

  // Month labels (top) — detect first day of each month from data
  var lastMonth = '';
  weeks.forEach(function(week, wi) {
    if (week && week[0] && week[0].date) {
      var mo = week[0].date.substr(0,7); // YYYY-MM
      if (mo !== lastMonth) {
        var monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        var mIdx = parseInt(mo.substr(5,2)) - 1;
        svg += '<text x="' + (padL + wi*(cellS+cellG)) + '" y="' + (padT-4) + '" font-size="8" fill="#57606a">' + (monthNames[mIdx]||'') + '</text>';
        lastMonth = mo;
      }
    }
  });

  // All data — find max count for quartile
  var allCounts = [];
  weeks.forEach(function(week){ (week||[]).forEach(function(d){ if(d) allCounts.push(d.count||0); }); });
  allCounts.sort(function(a,b){return a-b;});
  var q = allCounts.length;
  function getLevel(count) {
    if (!count) return 0;
    var rank = allCounts.indexOf(count);
    if (rank < 0) rank = allCounts.filter(function(c){return c<=count;}).length - 1;
    var pct = rank / (q-1||1);
    return pct < 0.25 ? 1 : pct < 0.5 ? 2 : pct < 0.75 ? 3 : 4;
  }

  weeks.forEach(function(week, wi) {
    (week||[]).forEach(function(day, di) {
      if (!day) return;
      var cnt   = day.count || 0;
      var lvl   = getLevel(cnt);
      var color = cnt === 0 ? emptyColor : colors[lvl];
      var cx    = padL + wi*(cellS+cellG);
      var cy    = padT + di*(cellS+cellG);
      var ttl   = (day.date || ('Week '+(wi+1)+' Day '+(di+1))) + ': ' + cnt + ' contribution' + (cnt!==1?'s':'');
      svg += '<rect x="' + cx + '" y="' + cy + '" width="' + cellS + '" height="' + cellS + '" rx="2" fill="' + color + '"><title>' + _esc(ttl) + '</title></rect>';
    });
  });

  svg += '</svg>';
  return '<div class="a2ui-github-grid">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 18. entity_list — structured entity/person list
// ─────────────────────────────────────────────────────────
_RENDERERS['entity_list'] = function(b) {
  var entities = b.entities || [];
  var title    = b.title    || '';

  var typeColors = {
    person:       '#6366f1',
    organization: '#22d3ee',
    location:     '#34d399',
    product:      '#fb923c',
    event:        '#f472b6'
  };

  var html = '<div class="a2ui-entity-list">';
  if (title) html += '<div class="a2ui-entity-list-title">' + _esc(title) + '</div>';
  html += '<div class="a2ui-entity-grid">';

  entities.forEach(function(entity) {
    var typeColor = typeColors[(entity.type||'').toLowerCase()] || '#94a3b8';
    var item = '';

    if (entity.link) {
      item += '<a class="a2ui-entity-card" href="' + _esc(entity.link) + '" target="_blank" rel="noopener" style="text-decoration:none;">';
    } else {
      item += '<div class="a2ui-entity-card">';
    }

    // Avatar
    item += '<div class="a2ui-entity-avatar">';
    if (entity.avatar_url) {
      item += '<img src="' + _esc(entity.avatar_url) + '" width="40" height="40" style="border-radius:50%;object-fit:cover;" onerror="this.style.display=\'none\';this.nextSibling.style.display=\'flex\'"/>';
      item += '<div class="a2ui-entity-initials" style="display:none;background:' + typeColor + ';">' + _esc((entity.name||'?').charAt(0).toUpperCase()) + '</div>';
    } else {
      item += '<div class="a2ui-entity-initials" style="background:' + typeColor + ';">' + _esc((entity.name||'?').charAt(0).toUpperCase()) + '</div>';
    }
    item += '</div>';

    // Info
    item += '<div class="a2ui-entity-info">';
    item += '<div class="a2ui-entity-name">' + _esc(entity.name || '') + '</div>';
    if (entity.type) item += '<span class="a2ui-entity-type" style="background:' + typeColor + '20;color:' + typeColor + ';border:1px solid ' + typeColor + '40;">' + _esc(entity.type) + '</span>';
    if (entity.description) item += '<div class="a2ui-entity-desc">' + _esc(entity.description) + '</div>';
    if (entity.meta) item += '<div class="a2ui-entity-meta">' + _esc(entity.meta) + '</div>';
    item += '</div>';

    item += entity.link ? '</a>' : '</div>';
    html += item;
  });

  html += '</div></div>';
  return html;
};



// === Batch 6: Misc Atoms + Animation Degraded Fallbacks ===

_RENDERERS['markdown_block'] = function(b) {
  var content = b.content || '';
  var html = _markdownToHtml(content);
  return '<div class="asw-markdown-block">' + html + '</div>';
};

_RENDERERS['bento_grid'] = function(b) {
  var items = b.items || [];
  var cols = b.cols || 3;
  var uid = Math.random().toString(36).substr(2, 6);
  var id = 'bento-' + uid;
  var colorSchemes = [
    {bg:'#f3f0ff',border:'#ede9fe'},
    {bg:'#fdf4ff',border:'#fae8ff'},
    {bg:'#f0fdf4',border:'#dcfce7'},
    {bg:'#eff6ff',border:'#dbeafe'},
    {bg:'#fff7ed',border:'#fed7aa'},
    {bg:'#fafafa',border:'#e5e7eb'}
  ];
  var itemsHtml = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var span = Math.min(Math.max(parseInt(item.span) || 1, 1), cols);
    var scheme = colorSchemes[i % colorSchemes.length];
    if (item.color_scheme === 'purple') { scheme = {bg:'#f3f0ff',border:'#ede9fe'}; }
    else if (item.color_scheme === 'green') { scheme = {bg:'#f0fdf4',border:'#dcfce7'}; }
    else if (item.color_scheme === 'blue') { scheme = {bg:'#eff6ff',border:'#dbeafe'}; }
    else if (item.color_scheme === 'orange') { scheme = {bg:'#fff7ed',border:'#fed7aa'}; }
    var iconHtml = item.icon ? '<div style="font-size:1.8rem;margin-bottom:8px;">' + _esc(item.icon) + '</div>' : '';
    var titleHtml = item.title ? '<div style="font-weight:700;font-size:1rem;color:#111827;margin-bottom:6px;">' + _esc(item.title) + '</div>' : '';
    var bodyHtml = item.body ? '<div style="font-size:0.875rem;color:#4b5563;line-height:1.5;">' + _esc(item.body) + '</div>' : '';
    itemsHtml += '<div style="grid-column:span ' + span + ';background:' + scheme.bg + ';border:1px solid ' + scheme.border + ';border-radius:14px;padding:20px;box-sizing:border-box;">' + iconHtml + titleHtml + bodyHtml + '</div>';
  }
  return '<div id="' + id + '" style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:14px;margin:1rem 0;">' + itemsHtml + '</div>';
};

_RENDERERS['cta_section'] = function(b) {
  var headline = b.headline || '';
  var subheadline = b.subheadline || '';
  var primaryLabel = b.primary_label || '';
  var primaryUrl = b.primary_url || '#';
  var secondaryLabel = b.secondary_label || '';
  var secondaryUrl = b.secondary_url || '#';
  var alignment = b.alignment === 'left' ? 'left' : 'center';
  var btnPrimary = primaryLabel ? '<a href="' + _esc(primaryUrl) + '" style="display:inline-block;background:#7c3aed;color:#fff;font-weight:600;padding:12px 28px;border-radius:8px;text-decoration:none;font-size:0.95rem;margin:6px;">' + _esc(primaryLabel) + '</a>' : '';
  var btnSecondary = secondaryLabel ? '<a href="' + _esc(secondaryUrl) + '" style="display:inline-block;background:transparent;color:#7c3aed;font-weight:600;padding:11px 27px;border-radius:8px;text-decoration:none;font-size:0.95rem;border:1.5px solid #7c3aed;margin:6px;">' + _esc(secondaryLabel) + '</a>' : '';
  return '<div style="background:linear-gradient(135deg,#f5f3ff,#faf5ff);border:1px solid #ede9fe;border-radius:16px;padding:40px 32px;margin:1rem 0;text-align:' + alignment + ';">'
    + (headline ? '<h2 style="margin:0 0 12px;font-size:1.75rem;font-weight:800;color:#111827;">' + _esc(headline) + '</h2>' : '')
    + (subheadline ? '<p style="margin:0 0 24px;font-size:1.05rem;color:#4b5563;">' + _esc(subheadline) + '</p>' : '')
    + '<div>' + btnPrimary + btnSecondary + '</div>'
    + '</div>';
};

_RENDERERS['lozenge'] = function(b) {
  var text = b.text || '';
  var color = b.color || 'default';
  var colorMap = {
    'default': {bg:'#f3f4f6',fg:'#374151'},
    'success':  {bg:'#dcfce7',fg:'#166534'},
    'warning':  {bg:'#fef3c7',fg:'#92400e'},
    'danger':   {bg:'#fee2e2',fg:'#991b1b'},
    'info':     {bg:'#dbeafe',fg:'#1d4ed8'}
  };
  var c = colorMap[color] || colorMap['default'];
  return '<span style="display:inline-block;background:' + c.bg + ';color:' + c.fg + ';font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:999px;letter-spacing:0.02em;">' + _esc(text) + '</span>';
};

_RENDERERS['task_list'] = function(b) {
  var items = b.items || [];
  var priorityColors = {high:'#ef4444', medium:'#f59e0b', low:'#9ca3af'};
  var rows = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var dot = item.priority ? '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + (priorityColors[item.priority] || '#9ca3af') + ';margin-right:8px;flex-shrink:0;"></span>' : '';
    var textStyle = item.done ? 'text-decoration:line-through;color:#9ca3af;' : 'color:#111827;';
    var checkIcon = item.done
      ? '<svg width="16" height="16" viewBox="0 0 16 16" style="flex-shrink:0;"><circle cx="8" cy="8" r="7" fill="#7c3aed"/><polyline points="4,8 7,11 12,5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
      : '<svg width="16" height="16" viewBox="0 0 16 16" style="flex-shrink:0;"><circle cx="8" cy="8" r="7" fill="none" stroke="#d1d5db" stroke-width="1.5"/></svg>';
    rows += '<li style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #f3f4f6;">'
      + checkIcon
      + '<span style="' + textStyle + 'flex:1;font-size:0.9rem;">' + _esc(item.text || '') + '</span>'
      + dot
      + '</li>';
  }
  return '<ul style="list-style:none;margin:0.5rem 0;padding:0;">' + rows + '</ul>';
};

_RENDERERS['vote_button_group'] = function(b) {
  var options = b.options || [];
  var question = b.question || '';
  var uid = Math.random().toString(36).substr(2, 6);
  var rows = '';
  for (var i = 0; i < options.length; i++) {
    var opt = options[i];
    var id = 'vote-' + uid + '-' + i;
    rows += '<label for="' + id + '" style="display:flex;align-items:center;gap:12px;padding:12px 16px;border:1.5px solid #e5e7eb;border-radius:10px;cursor:pointer;background:#fff;transition:border-color 0.15s;">'
      + '<input type="radio" name="vote-' + uid + '" id="' + id + '" value="' + i + '" style="accent-color:#7c3aed;">'
      + '<span style="flex:1;font-size:0.9rem;color:#111827;font-weight:500;">' + _esc(opt.label || '') + '</span>'
      + '<span style="font-size:0.82rem;color:#6b7280;background:#f3f4f6;padding:2px 8px;border-radius:999px;">' + (opt.votes || 0) + ' votes</span>'
      + '</label>';
  }
  return '<div style="margin:1rem 0;">'
    + (question ? '<p style="margin:0 0 12px;font-weight:700;color:#111827;font-size:1rem;">' + _esc(question) + '</p>' : '')
    + '<div style="display:flex;flex-direction:column;gap:8px;">' + rows + '</div>'
    + '</div>';
};

_RENDERERS['sprint_board'] = function(b) {
  var columns = b.columns || [];
  var colsHtml = '';
  var priorityColors = {high:'#ef4444', medium:'#f59e0b', low:'#10b981', null:'#d1d5db'};
  for (var c = 0; c < columns.length; c++) {
    var col = columns[c];
    var items = col.items || [];
    var cardsHtml = '';
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      var pcolor = priorityColors[item.priority] || '#d1d5db';
      var assigneeHtml = item.assignee ? '<div style="width:24px;height:24px;border-radius:50%;background:#7c3aed;color:#fff;font-size:0.7rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">' + _esc(item.assignee.charAt(0).toUpperCase()) + '</div>' : '';
      var labelsHtml = '';
      if (item.labels && item.labels.length) {
        for (var l = 0; l < item.labels.length; l++) {
          labelsHtml += '<span style="background:#ede9fe;color:#5b21b6;font-size:0.7rem;padding:1px 6px;border-radius:999px;">' + _esc(item.labels[l]) + '</span>';
        }
      }
      cardsHtml += '<div style="background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:8px;">'
        + '<div style="display:flex;align-items:flex-start;gap:8px;">'
        + '<div style="width:8px;height:8px;border-radius:50%;background:' + pcolor + ';flex-shrink:0;margin-top:5px;"></div>'
        + '<div style="flex:1;">'
        + (item.id ? '<div style="font-size:0.72rem;color:#9ca3af;margin-bottom:3px;">' + _esc(item.id) + '</div>' : '')
        + '<div style="font-size:0.87rem;font-weight:600;color:#111827;">' + _esc(item.title || '') + '</div>'
        + (labelsHtml ? '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px;">' + labelsHtml + '</div>' : '')
        + '</div>'
        + assigneeHtml
        + '</div>'
        + '</div>';
    }
    colsHtml += '<div style="flex:1;min-width:200px;background:#f9fafb;border-radius:12px;padding:14px;">'
      + '<div style="font-weight:700;font-size:0.85rem;color:#374151;margin-bottom:12px;text-transform:uppercase;letter-spacing:0.05em;">' + _esc(col.title || '') + ' <span style="background:#e5e7eb;color:#6b7280;border-radius:999px;padding:1px 7px;font-size:0.75rem;">' + items.length + '</span></div>'
      + cardsHtml
      + '</div>';
  }
  return '<div style="display:flex;gap:12px;overflow-x:auto;margin:1rem 0;padding-bottom:4px;">' + colsHtml + '</div>';
};

_RENDERERS['jira_ticket'] = function(b) {
  var typeIcons = {bug:'🐛', story:'📖', task:'✅', epic:'⚡'};
  var typeColors = {bug:'#fee2e2', story:'#dbeafe', task:'#f0fdf4', epic:'#faf5ff'};
  var statusColors = {
    'To Do':'#f3f4f6','In Progress':'#dbeafe','Done':'#dcfce7',
    'Blocked':'#fee2e2','Review':'#fef3c7'
  };
  var type = b.type || 'task';
  var status = b.status || 'To Do';
  var icon = typeIcons[type] || '📋';
  var bgColor = typeColors[type] || '#f9fafb';
  var statusBg = statusColors[status] || '#f3f4f6';
  var labelsHtml = '';
  if (b.labels && b.labels.length) {
    for (var l = 0; l < b.labels.length; l++) {
      labelsHtml += '<span style="background:#ede9fe;color:#5b21b6;font-size:0.72rem;padding:2px 8px;border-radius:999px;">' + _esc(b.labels[l]) + '</span>';
    }
  }
  var assigneeHtml = b.assignee ? '<div style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:#6b7280;"><div style="width:22px;height:22px;border-radius:50%;background:#7c3aed;color:#fff;font-size:0.7rem;font-weight:700;display:flex;align-items:center;justify-content:center;">' + _esc(b.assignee.charAt(0).toUpperCase()) + '</div>' + _esc(b.assignee) + '</div>' : '';
  return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:18px;margin:0.75rem 0;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,0.06);">'
    + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
    + '<span style="font-size:1.2rem;background:' + bgColor + ';padding:6px;border-radius:8px;">' + icon + '</span>'
    + '<span style="font-size:0.82rem;font-weight:700;color:#6b7280;font-family:monospace;">' + _esc(b.key || '') + '</span>'
    + '<span style="margin-left:auto;background:' + statusBg + ';font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:999px;color:#374151;">' + _esc(status) + '</span>'
    + '</div>'
    + '<div style="font-size:1rem;font-weight:600;color:#111827;margin-bottom:10px;">' + _esc(b.summary || '') + '</div>'
    + (labelsHtml ? '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px;">' + labelsHtml + '</div>' : '')
    + (assigneeHtml ? '<div style="margin-top:8px;">' + assigneeHtml + '</div>' : '')
    + '</div>';
};

_RENDERERS['feature_grid'] = function(b) {
  var features = b.features || [];
  var cols = b.cols || 3;
  var cardsHtml = '';
  for (var i = 0; i < features.length; i++) {
    var f = features[i];
    cardsHtml += '<div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:20px;">'
      + (f.icon ? '<div style="font-size:2rem;margin-bottom:12px;">' + _esc(f.icon) + '</div>' : '')
      + (f.title ? '<div style="font-weight:700;font-size:1rem;color:#111827;margin-bottom:8px;">' + _esc(f.title) + '</div>' : '')
      + (f.description ? '<div style="font-size:0.875rem;color:#4b5563;line-height:1.6;">' + _esc(f.description) + '</div>' : '')
      + '</div>';
  }
  return '<div style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:14px;margin:1rem 0;">' + cardsHtml + '</div>';
};

_RENDERERS['navigation_menu'] = function(b) {
  var items = b.items || [];
  var itemsHtml = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var iconHtml = item.icon ? '<span style="margin-right:6px;">' + _esc(item.icon) + '</span>' : '';
    if (item.children && item.children.length) {
      var subItems = '';
      for (var j = 0; j < item.children.length; j++) {
        var child = item.children[j];
        subItems += '<li><a href="' + _esc(child.url || '#') + '" style="display:block;padding:8px 16px;font-size:0.875rem;color:#374151;text-decoration:none;white-space:nowrap;">' + _esc(child.label || '') + '</a></li>';
      }
      itemsHtml += '<li style="position:relative;">'
        + '<details style="display:inline;">'
        + '<summary style="display:flex;align-items:center;gap:4px;padding:8px 12px;font-size:0.9rem;font-weight:500;color:#111827;cursor:pointer;list-style:none;border-radius:6px;">' + iconHtml + _esc(item.label || '') + ' <span style="font-size:0.7rem;">▾</span></summary>'
        + '<ul style="position:absolute;top:100%;left:0;background:#fff;border:1px solid #e5e7eb;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,0.1);list-style:none;margin:4px 0 0;padding:6px 0;min-width:180px;z-index:10;">' + subItems + '</ul>'
        + '</details>'
        + '</li>';
    } else {
      itemsHtml += '<li><a href="' + _esc(item.url || '#') + '" style="display:flex;align-items:center;padding:8px 12px;font-size:0.9rem;font-weight:500;color:#111827;text-decoration:none;border-radius:6px;">' + iconHtml + _esc(item.label || '') + '</a></li>';
    }
  }
  return '<nav style="margin:0.75rem 0;"><ul style="display:flex;list-style:none;margin:0;padding:8px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:12px;gap:4px;flex-wrap:wrap;">' + itemsHtml + '</ul></nav>';
};

_RENDERERS['order_status_card'] = function(b) {
  var steps = ['Placed', 'Processing', 'Shipped', 'Delivered'];
  var statusIndex = {placed:0, processing:1, shipped:2, delivered:3, cancelled:-1};
  var currentStep = statusIndex[b.status] !== undefined ? statusIndex[b.status] : 0;
  var cancelled = b.status === 'cancelled';
  var stepperHtml = '<div style="display:flex;align-items:center;margin:16px 0 24px;">';
  for (var s = 0; s < steps.length; s++) {
    var done = !cancelled && s <= currentStep;
    var active = !cancelled && s === currentStep;
    var dotBg = cancelled ? '#fee2e2' : (done ? '#7c3aed' : '#e5e7eb');
    var dotColor = cancelled ? '#991b1b' : (done ? '#fff' : '#9ca3af');
    stepperHtml += '<div style="display:flex;flex-direction:column;align-items:center;flex:1;">'
      + '<div style="width:28px;height:28px;border-radius:50%;background:' + dotBg + ';color:' + dotColor + ';font-size:0.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;">' + (done && !active ? '✓' : (s + 1)) + '</div>'
      + '<div style="font-size:0.72rem;margin-top:4px;color:' + (active ? '#7c3aed' : '#6b7280') + ';font-weight:' + (active ? '700' : '400') + ';text-align:center;">' + steps[s] + '</div>'
      + '</div>';
    if (s < steps.length - 1) {
      stepperHtml += '<div style="flex:1;height:2px;background:' + (!cancelled && s < currentStep ? '#7c3aed' : '#e5e7eb') + ';margin-bottom:16px;"></div>';
    }
  }
  stepperHtml += '</div>';
  var itemsHtml = '';
  var items = b.items || [];
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    itemsHtml += '<tr><td style="padding:8px 4px;font-size:0.875rem;color:#111827;">' + _esc(item.name || '') + '</td><td style="padding:8px 4px;font-size:0.875rem;color:#6b7280;text-align:center;">×' + (item.qty || 1) + '</td><td style="padding:8px 4px;font-size:0.875rem;color:#111827;text-align:right;">' + _esc(item.price || '') + '</td></tr>';
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin:1rem 0;background:#fff;">'
    + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
    + '<span style="font-weight:700;color:#111827;font-size:1rem;">Order ' + _esc(b.order_id || '') + '</span>'
    + (cancelled ? '<span style="background:#fee2e2;color:#991b1b;font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:999px;">Cancelled</span>' : '')
    + '</div>'
    + stepperHtml
    + '<table style="width:100%;border-collapse:collapse;border-top:1px solid #f3f4f6;">' + itemsHtml + '</table>'
    + '<div style="display:flex;justify-content:space-between;padding-top:10px;border-top:1px solid #e5e7eb;margin-top:8px;font-weight:700;color:#111827;">'
    + '<span>Total</span><span>' + _esc(b.total || '') + '</span>'
    + '</div>'
    + (b.estimated_delivery ? '<div style="margin-top:10px;font-size:0.82rem;color:#6b7280;">Estimated delivery: <strong style="color:#111827;">' + _esc(b.estimated_delivery) + '</strong></div>' : '')
    + '</div>';
};

_RENDERERS['roadmap_card'] = function(b) {
  var statusColors = {
    'planned':     {bg:'#f3f4f6',fg:'#374151'},
    'in-progress': {bg:'#dbeafe',fg:'#1d4ed8'},
    'done':        {bg:'#dcfce7',fg:'#166534'},
    'deferred':    {bg:'#fef3c7',fg:'#92400e'}
  };
  var sc = statusColors[b.status] || statusColors['planned'];
  var itemsHtml = '';
  if (b.items && b.items.length) {
    for (var i = 0; i < b.items.length; i++) {
      itemsHtml += '<li style="font-size:0.875rem;color:#374151;padding:3px 0;">• ' + _esc(b.items[i]) + '</li>';
    }
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin:0.75rem 0;background:#fff;">'
    + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
    + (b.quarter ? '<span style="font-size:0.82rem;font-weight:700;color:#7c3aed;background:#f3f0ff;padding:3px 10px;border-radius:999px;">' + _esc(b.quarter) + '</span>' : '')
    + '<span style="background:' + sc.bg + ';color:' + sc.fg + ';font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:999px;">' + _esc(b.status || '') + '</span>'
    + '</div>'
    + (b.title ? '<div style="font-weight:700;font-size:1.05rem;color:#111827;margin-bottom:8px;">' + _esc(b.title) + '</div>' : '')
    + (b.description ? '<p style="font-size:0.875rem;color:#4b5563;margin:0 0 12px;line-height:1.5;">' + _esc(b.description) + '</p>' : '')
    + (itemsHtml ? '<ul style="list-style:none;margin:0;padding:0;">' + itemsHtml + '</ul>' : '')
    + '</div>';
};

_RENDERERS['notification_stack'] = function(b) {
  var notifications = b.notifications || [];
  var typeConfig = {
    info:    {bg:'#eff6ff',border:'#93c5fd',icon:'ℹ️',color:'#1d4ed8'},
    success: {bg:'#f0fdf4',border:'#86efac',icon:'✅',color:'#166534'},
    warning: {bg:'#fffbeb',border:'#fcd34d',icon:'⚠️',color:'#92400e'},
    error:   {bg:'#fef2f2',border:'#fca5a5',icon:'❌',color:'#991b1b'}
  };
  var html = '<div style="display:flex;flex-direction:column;gap:8px;margin:1rem 0;">';
  for (var i = 0; i < notifications.length; i++) {
    var n = notifications[i];
    var tc = typeConfig[n.type] || typeConfig['info'];
    html += '<div style="background:' + tc.bg + ';border:1px solid ' + tc.border + ';border-radius:10px;padding:14px 16px;display:flex;gap:12px;align-items:flex-start;">'
      + '<span style="font-size:1rem;flex-shrink:0;">' + tc.icon + '</span>'
      + '<div style="flex:1;">'
      + (n.title ? '<div style="font-weight:700;font-size:0.875rem;color:#111827;">' + _esc(n.title) + '</div>' : '')
      + (n.body ? '<div style="font-size:0.82rem;color:#374151;margin-top:2px;">' + _esc(n.body) + '</div>' : '')
      + '</div>'
      + (n.time ? '<span style="font-size:0.72rem;color:#9ca3af;flex-shrink:0;">' + _esc(n.time) + '</span>' : '')
      + '<button style="background:none;border:none;cursor:pointer;color:#9ca3af;font-size:1rem;padding:0;line-height:1;flex-shrink:0;" aria-label="Dismiss">×</button>'
      + '</div>';
  }
  html += '</div>';
  return html;
};

_RENDERERS['inline_alert'] = function(b) {
  var typeConfig = {
    info:    {bg:'#eff6ff',border:'#3b82f6',fg:'#1d4ed8',icon:'ℹ️'},
    success: {bg:'#f0fdf4',border:'#22c55e',fg:'#166534',icon:'✅'},
    warning: {bg:'#fffbeb',border:'#f59e0b',fg:'#92400e',icon:'⚠️'},
    error:   {bg:'#fef2f2',border:'#ef4444',fg:'#991b1b',icon:'❌'}
  };
  var tc = typeConfig[b.type] || typeConfig['info'];
  return '<div style="display:flex;align-items:flex-start;gap:10px;background:' + tc.bg + ';border-left:4px solid ' + tc.border + ';border-radius:0 8px 8px 0;padding:12px 16px;margin:0.75rem 0;">'
    + '<span style="font-size:0.95rem;flex-shrink:0;">' + tc.icon + '</span>'
    + '<div style="flex:1;font-size:0.875rem;color:' + tc.fg + ';">' + _esc(b.message || '') + '</div>'
    + (b.dismissible ? '<button style="background:none;border:none;cursor:pointer;color:#9ca3af;font-size:1rem;padding:0;line-height:1;" aria-label="Dismiss">×</button>' : '')
    + '</div>';
};

_RENDERERS['source_citation'] = function(b) {
  var authorsHtml = '';
  if (b.authors && b.authors.length) {
    var escapedAuthors = [];
    for (var i = 0; i < b.authors.length; i++) {
      escapedAuthors.push(_esc(b.authors[i]));
    }
    authorsHtml = '<span style="font-size:0.82rem;color:#374151;">' + escapedAuthors.join(', ') + '</span>';
    if (b.year) { authorsHtml += '<span style="font-size:0.82rem;color:#6b7280;"> (' + _esc(b.year) + ')</span>'; }
  }
  var titleHtml = b.url
    ? '<a href="' + _esc(b.url) + '" style="font-weight:600;color:#1d4ed8;text-decoration:none;font-size:0.9rem;">' + _esc(b.title || '') + '</a>'
    : '<span style="font-weight:600;color:#111827;font-size:0.9rem;">' + _esc(b.title || '') + '</span>';
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;margin:0.75rem 0;background:#fafafa;display:flex;gap:12px;">'
    + '<div style="width:28px;height:28px;border-radius:50%;background:#7c3aed;color:#fff;font-size:0.78rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">①</div>'
    + '<div>'
    + titleHtml
    + (authorsHtml ? '<div style="margin-top:3px;">' + authorsHtml + '</div>' : '')
    + (b.publisher ? '<div style="font-size:0.8rem;color:#6b7280;margin-top:2px;font-style:italic;">' + _esc(b.publisher) + '</div>' : '')
    + (b.note ? '<div style="font-size:0.8rem;color:#4b5563;margin-top:5px;background:#f3f4f6;padding:5px 8px;border-radius:6px;">' + _esc(b.note) + '</div>' : '')
    + '</div>'
    + '</div>';
};

_RENDERERS['llm_comparison_table'] = function(b) {
  var models = b.models || [];
  var title = b.title || 'Model Comparison';
  var rows = '';
  for (var i = 0; i < models.length; i++) {
    var m = models[i];
    var strengths = m.strengths ? m.strengths.join(', ') : '';
    var weaknesses = m.weaknesses ? m.weaknesses.join(', ') : '';
    var rowBg = i % 2 === 0 ? '#fff' : '#f9fafb';
    rows += '<tr style="background:' + rowBg + ';">'
      + '<td style="padding:10px 12px;font-weight:600;color:#111827;font-size:0.875rem;">' + _esc(m.name || '') + '</td>'
      + '<td style="padding:10px 12px;font-size:0.82rem;color:#374151;">' + _esc(m.params || '—') + '</td>'
      + '<td style="padding:10px 12px;font-size:0.82rem;color:#374151;">' + _esc(m.context_window ? String(m.context_window) : '—') + '</td>'
      + '<td style="padding:10px 12px;font-size:0.82rem;color:#374151;">' + _esc(m.price_per_1m_tokens ? String(m.price_per_1m_tokens) : '—') + '</td>'
      + '<td style="padding:10px 12px;font-size:0.78rem;color:#166534;">' + _esc(strengths) + '</td>'
      + '<td style="padding:10px 12px;font-size:0.78rem;color:#991b1b;">' + _esc(weaknesses) + '</td>'
      + '</tr>';
  }
  return '<div style="margin:1rem 0;overflow-x:auto;">'
    + (title ? '<div style="font-weight:700;font-size:1rem;color:#111827;margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + '<table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;font-size:0.875rem;">'
    + '<thead><tr style="background:#f3f4f6;"><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Model</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Params</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Context</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">$/1M tokens</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Strengths</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Weaknesses</th></tr></thead>'
    + '<tbody>' + rows + '</tbody>'
    + '</table></div>';
};

_RENDERERS['confidence_bar'] = function(b) {
  var value = Math.min(Math.max(parseFloat(b.value) || 0, 0), 1);
  var pct = Math.round(value * 100);
  var color = b.color || '#7c3aed';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="margin:0.75rem 0;">'
    + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
    + '<span style="font-size:0.875rem;font-weight:500;color:#374151;">' + _esc(b.label || '') + '</span>'
    + '<span style="font-size:0.875rem;font-weight:700;color:' + color + ';">' + pct + '%</span>'
    + '</div>'
    + '<div style="background:#f3f4f6;border-radius:999px;height:8px;overflow:hidden;">'
    + '<div style="width:' + pct + '%;height:100%;background:' + color + ';border-radius:999px;transition:width 0.6s ease;"></div>'
    + '</div>'
    + '</div>';
};

_RENDERERS['token_budget_meter'] = function(b) {
  var used = parseInt(b.used) || 0;
  var total = parseInt(b.total) || 1;
  var unit = b.unit || 'tokens';
  var pct = Math.min(Math.round((used / total) * 100), 100);
  var color = pct < 70 ? '#22c55e' : (pct < 90 ? '#f59e0b' : '#ef4444');
  var label = pct < 70 ? 'On track' : (pct < 90 ? 'Nearing limit' : 'Critical');
  return '<div style="margin:0.75rem 0;">'
    + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
    + '<span style="font-size:0.875rem;font-weight:600;color:#374151;">Token Budget</span>'
    + '<span style="font-size:0.82rem;color:#6b7280;">' + used.toLocaleString() + ' / ' + total.toLocaleString() + ' ' + _esc(unit) + '</span>'
    + '</div>'
    + '<div style="background:#f3f4f6;border-radius:999px;height:10px;overflow:hidden;">'
    + '<div style="width:' + pct + '%;height:100%;background:' + color + ';border-radius:999px;transition:width 0.6s ease;"></div>'
    + '</div>'
    + '<div style="display:flex;justify-content:space-between;margin-top:5px;">'
    + '<span style="font-size:0.72rem;color:' + color + ';font-weight:600;">' + label + '</span>'
    + '<span style="font-size:0.72rem;color:#6b7280;">' + pct + '% used</span>'
    + '</div>'
    + '</div>';
};

_RENDERERS['text_callout'] = function(b) {
  var text = b.text || '';
  var style = b.style || 'highlight';
  if (style === 'quote') {
    return '<blockquote style="border-left:4px solid #7c3aed;padding:12px 16px;margin:1rem 0;color:#4b5563;font-style:italic;background:#fafafa;border-radius:0 8px 8px 0;">' + _esc(text) + '</blockquote>';
  } else if (style === 'bold') {
    return '<div style="font-weight:700;color:#7c3aed;font-size:1.05rem;margin:0.75rem 0;">' + _esc(text) + '</div>';
  } else {
    return '<mark style="background:#fef9c3;color:#111827;padding:2px 6px;border-radius:4px;">' + _esc(text) + '</mark>';
  }
};

_RENDERERS['tag_block'] = function(b) {
  var tags = b.tags || [];
  var pillsHtml = '';
  for (var i = 0; i < tags.length; i++) {
    var tag = tags[i];
    var text, color, url;
    if (typeof tag === 'string') {
      text = tag; color = null; url = null;
    } else {
      text = tag.text || ''; color = tag.color || null; url = tag.url || null;
    }
    var bg = color || '#f3f4f6';
    var fg = color ? '#fff' : '#374151';
    var pill = '<span style="display:inline-flex;align-items:center;background:' + _esc(bg) + ';color:' + fg + ';font-size:0.78rem;font-weight:500;padding:4px 12px;border-radius:999px;white-space:nowrap;">' + _esc(text) + '</span>';
    if (url) {
      pillsHtml += '<a href="' + _esc(url) + '" style="text-decoration:none;">' + pill + '</a>';
    } else {
      pillsHtml += pill;
    }
  }
  return '<div style="display:flex;flex-wrap:wrap;gap:6px;margin:0.5rem 0;">' + pillsHtml + '</div>';
};

_RENDERERS['variant_selector'] = function(b) {
  var label = b.label || '';
  var variants = b.variants || [];
  var uid = Math.random().toString(36).substr(2, 6);
  var variantsHtml = '';
  for (var i = 0; i < variants.length; i++) {
    var v = variants[i];
    var id = 'variant-' + uid + '-' + i;
    if (v.color) {
      variantsHtml += '<label for="' + id + '" title="' + _esc(v.label || v.value || '') + '" style="cursor:pointer;">'
        + '<input type="radio" name="variant-' + uid + '" id="' + id + '" value="' + _esc(v.value || '') + '" style="display:none;"' + (v.disabled ? ' disabled' : '') + '>'
        + '<span style="display:inline-block;width:28px;height:28px;border-radius:50%;background:' + _esc(v.color) + ';border:2px solid #fff;box-shadow:0 0 0 2px #d1d5db;' + (v.disabled ? 'opacity:0.4;' : '') + '"></span>'
        + '</label>';
    } else {
      variantsHtml += '<label for="' + id + '" style="cursor:pointer;">'
        + '<input type="radio" name="variant-' + uid + '" id="' + id + '" value="' + _esc(v.value || '') + '" style="display:none;"' + (v.disabled ? ' disabled' : '') + '>'
        + '<span style="display:inline-block;padding:6px 14px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:0.82rem;font-weight:500;color:#374151;' + (v.disabled ? 'opacity:0.4;' : '') + '">' + _esc(v.label || v.value || '') + '</span>'
        + '</label>';
    }
  }
  return '<div style="margin:0.75rem 0;">'
    + (label ? '<div style="font-size:0.875rem;font-weight:600;color:#111827;margin-bottom:10px;">' + _esc(label) + '</div>' : '')
    + '<div style="display:flex;flex-wrap:wrap;gap:8px;">' + variantsHtml + '</div>'
    + '</div>';
};

_RENDERERS['shortcut_legend'] = function(b) {
  var shortcuts = b.shortcuts || [];
  var rows = '';
  for (var i = 0; i < shortcuts.length; i++) {
    var sc = shortcuts[i];
    var keys = sc.keys || [];
    var keysHtml = '';
    for (var k = 0; k < keys.length; k++) {
      if (k > 0) { keysHtml += '<span style="color:#9ca3af;font-size:0.8rem;margin:0 3px;">+</span>'; }
      keysHtml += '<kbd style="display:inline-block;background:#fff;border:1px solid #d1d5db;border-bottom:2px solid #9ca3af;border-radius:5px;padding:2px 7px;font-size:0.78rem;font-family:monospace;color:#111827;box-shadow:0 1px 0 rgba(0,0,0,0.1);">' + _esc(keys[k]) + '</kbd>';
    }
    rows += '<tr style="' + (i % 2 === 0 ? '' : 'background:#f9fafb;') + '">'
      + '<td style="padding:9px 12px;">' + keysHtml + '</td>'
      + '<td style="padding:9px 12px;font-size:0.875rem;color:#374151;">' + _esc(sc.description || '') + '</td>'
      + '</tr>';
  }
  return '<div style="margin:1rem 0;overflow-x:auto;">'
    + '<table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">'
    + '<thead><tr style="background:#f3f4f6;"><th style="padding:9px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Shortcut</th><th style="padding:9px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Description</th></tr></thead>'
    + '<tbody>' + rows + '</tbody>'
    + '</table></div>';
};

_RENDERERS['rating_summary_bar'] = function(b) {
  var overall = parseFloat(b.overall) || 0;
  var totalReviews = b.total_reviews || 0;
  var dist = b.distribution || {};
  var starsHtml = '';
  var fullStars = Math.floor(overall);
  var halfStar = (overall - fullStars) >= 0.5;
  for (var s = 1; s <= 5; s++) {
    if (s <= fullStars) { starsHtml += '★'; }
    else if (s === fullStars + 1 && halfStar) { starsHtml += '½'; }
    else { starsHtml += '☆'; }
  }
  var barsHtml = '';
  for (var r = 5; r >= 1; r--) {
    var count = dist[String(r)] || 0;
    var pct = totalReviews > 0 ? Math.round((count / totalReviews) * 100) : 0;
    barsHtml += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">'
      + '<span style="font-size:0.78rem;color:#6b7280;width:10px;">' + r + '</span>'
      + '<span style="color:#f59e0b;font-size:0.78rem;">★</span>'
      + '<div style="flex:1;background:#f3f4f6;border-radius:999px;height:8px;overflow:hidden;">'
      + '<div style="width:' + pct + '%;height:100%;background:#f59e0b;border-radius:999px;"></div>'
      + '</div>'
      + '<span style="font-size:0.72rem;color:#6b7280;width:28px;text-align:right;">' + count + '</span>'
      + '</div>';
  }
  return '<div style="display:flex;gap:24px;align-items:flex-start;border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin:1rem 0;background:#fff;">'
    + '<div style="text-align:center;min-width:80px;">'
    + '<div style="font-size:2.5rem;font-weight:800;color:#111827;line-height:1;">' + overall.toFixed(1) + '</div>'
    + '<div style="color:#f59e0b;font-size:1.1rem;letter-spacing:2px;">' + starsHtml + '</div>'
    + '<div style="font-size:0.78rem;color:#6b7280;margin-top:4px;">' + totalReviews.toLocaleString() + ' reviews</div>'
    + '</div>'
    + '<div style="flex:1;">' + barsHtml + '</div>'
    + '</div>';
};

_RENDERERS['model_card'] = function(b) {
  var metricsHtml = '';
  if (b.metrics && b.metrics.length) {
    for (var i = 0; i < b.metrics.length; i++) {
      var m = b.metrics[i];
      metricsHtml += '<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:10px;text-align:center;">'
        + '<div style="font-size:1.1rem;font-weight:700;color:#7c3aed;">' + _esc(m.value || '') + '</div>'
        + '<div style="font-size:0.72rem;color:#6b7280;margin-top:2px;">' + _esc(m.label || '') + '</div>'
        + '</div>';
    }
  }
  var tagsHtml = '';
  if (b.tags && b.tags.length) {
    for (var t = 0; t < b.tags.length; t++) {
      tagsHtml += '<span style="background:#ede9fe;color:#5b21b6;font-size:0.72rem;padding:2px 8px;border-radius:999px;">' + _esc(b.tags[t]) + '</span>';
    }
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin:1rem 0;background:#fff;">'
    + '<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:14px;">'
    + '<div style="flex:1;">'
    + (b.name ? '<div style="font-weight:800;font-size:1.1rem;color:#111827;">' + _esc(b.name) + (b.version ? ' <span style="font-size:0.78rem;color:#6b7280;font-weight:400;">v' + _esc(b.version) + '</span>' : '') + '</div>' : '')
    + (b.type ? '<div style="font-size:0.8rem;color:#7c3aed;font-weight:600;margin-top:2px;">' + _esc(b.type) + '</div>' : '')
    + '</div>'
    + (b.license ? '<span style="background:#f3f4f6;color:#374151;font-size:0.72rem;padding:3px 8px;border-radius:6px;">' + _esc(b.license) + '</span>' : '')
    + '</div>'
    + (b.description ? '<p style="font-size:0.875rem;color:#4b5563;margin:0 0 14px;line-height:1.6;">' + _esc(b.description) + '</p>' : '')
    + (metricsHtml ? '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px;margin-bottom:14px;">' + metricsHtml + '</div>' : '')
    + (tagsHtml ? '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px;">' + tagsHtml + '</div>' : '')
    + (b.link ? '<a href="' + _esc(b.link) + '" style="font-size:0.82rem;color:#7c3aed;text-decoration:none;font-weight:600;">View model →</a>' : '')
    + '</div>';
};

_RENDERERS['conversation_snippet'] = function(b) {
  var messages = b.messages || [];
  var html = '<div style="display:flex;flex-direction:column;gap:10px;margin:1rem 0;">';
  for (var i = 0; i < messages.length; i++) {
    var msg = messages[i];
    var role = msg.role || 'user';
    if (role === 'system') {
      html += '<div style="background:#f3f4f6;border-radius:8px;padding:8px 14px;font-size:0.8rem;color:#6b7280;font-style:italic;text-align:center;">' + _esc(msg.content || '') + '</div>';
    } else if (role === 'user') {
      html += '<div style="display:flex;justify-content:flex-end;">'
        + '<div style="background:#ede9fe;color:#111827;border-radius:16px 16px 4px 16px;padding:10px 14px;max-width:75%;font-size:0.875rem;">' + _esc(msg.content || '') + '</div>'
        + '</div>';
    } else {
      html += '<div style="display:flex;justify-content:flex-start;">'
        + '<div style="background:#fff;border:1px solid #e5e7eb;color:#111827;border-radius:16px 16px 16px 4px;padding:10px 14px;max-width:75%;font-size:0.875rem;">' + _esc(msg.content || '') + '</div>'
        + '</div>';
    }
  }
  html += '</div>';
  return html;
};

_RENDERERS['prompt_template'] = function(b) {
  var template = b.template || '';
  var variables = b.variables || [];
  var highlighted = _esc(template).replace(/\{\{([^}]+)\}\}/g, '<mark style="background:#fef9c3;color:#92400e;border-radius:3px;padding:1px 4px;">{{$1}}</mark>');
  var varsHtml = '';
  for (var i = 0; i < variables.length; i++) {
    var v = variables[i];
    varsHtml += '<tr style="' + (i % 2 === 0 ? '' : 'background:#f9fafb;') + '">'
      + '<td style="padding:8px 10px;font-family:monospace;font-size:0.82rem;color:#7c3aed;white-space:nowrap;">{{' + _esc(v.name || '') + '}}</td>'
      + '<td style="padding:8px 10px;font-size:0.82rem;color:#374151;">' + _esc(v.description || '') + '</td>'
      + '<td style="padding:8px 10px;font-size:0.78rem;color:#6b7280;font-style:italic;">' + _esc(v.example || '') + '</td>'
      + '</tr>';
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;margin:1rem 0;">'
    + '<div style="background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">'
    + '<span style="font-weight:700;font-size:0.9rem;color:#111827;">' + _esc(b.title || 'Prompt Template') + '</span>'
    + (b.use_case ? '<span style="font-size:0.78rem;color:#6b7280;">' + _esc(b.use_case) + '</span>' : '')
    + '</div>'
    + '<pre style="margin:0;padding:16px;background:#1e1e2e;color:#cdd6f4;font-size:0.82rem;line-height:1.6;white-space:pre-wrap;overflow-x:auto;"><code>' + highlighted + '</code></pre>'
    + (varsHtml ? '<div style="padding:14px 16px;border-top:1px solid #e5e7eb;"><div style="font-size:0.8rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Variables</div><table style="width:100%;border-collapse:collapse;font-size:0.82rem;"><thead><tr style="background:#f3f4f6;"><th style="padding:7px 10px;text-align:left;font-size:0.75rem;color:#6b7280;">Variable</th><th style="padding:7px 10px;text-align:left;font-size:0.75rem;color:#6b7280;">Description</th><th style="padding:7px 10px;text-align:left;font-size:0.75rem;color:#6b7280;">Example</th></tr></thead><tbody>' + varsHtml + '</tbody></table></div>' : '')
    + '</div>';
};

// === Animation degraded fallbacks ===

function _animFallback(atomName, label) {
  return '<div style="border:1px dashed #d1d5db;border-radius:10px;padding:16px;margin:1rem 0;background:#fafafa;text-align:center;color:#9ca3af;font-size:0.82rem;">⚡ [' + atomName + ' — not available in this surface]' + (label ? '<br><strong style=\'color:#374151;\'>' + _esc(label) + '</strong>' : '') + '</div>';
}

_RENDERERS['animated_beam'] = function(b) {
  return _animFallback('animated beam', b.title || b.label || b.text || '');
};

_RENDERERS['animated_border_card'] = function(b) {
  return _animFallback('animated border card', b.title || b.label || b.text || '');
};

_RENDERERS['aurora_background'] = function(b) {
  return _animFallback('aurora background', b.title || b.label || b.text || '');
};

_RENDERERS['blur_fade_in'] = function(b) {
  return _animFallback('blur fade-in', b.title || b.label || b.text || '');
};

_RENDERERS['card_stack'] = function(b) {
  return _animFallback('card stack', b.title || b.label || b.text || '');
};

_RENDERERS['countdown_timer'] = function(b) {
  var label = b.title || b.label || b.text || '';
  var extra = b.target_date ? '<br><span style="font-size:0.78rem;color:#6b7280;">Target: ' + _esc(b.target_date) + '</span>' : '';
  return '<div style="border:1px dashed #d1d5db;border-radius:10px;padding:16px;margin:1rem 0;background:#fafafa;text-align:center;color:#9ca3af;font-size:0.82rem;">⚡ [countdown timer — not available in this surface]' + (label ? '<br><strong style=\'color:#374151;\'>' + _esc(label) + '</strong>' : '') + extra + '</div>';
};

_RENDERERS['dot_grid_background'] = function(b) {
  return _animFallback('dot grid background', b.title || b.label || b.text || '');
};

_RENDERERS['effect_overlay'] = function(b) {
  return _animFallback('effect overlay', b.title || b.label || b.text || '');
};

_RENDERERS['encrypted_reveal'] = function(b) {
  return _animFallback('encrypted reveal', b.title || b.label || b.text || '');
};

_RENDERERS['glow_button'] = function(b) {
  var label = b.text || b.label || b.title || 'Action';
  return '<div style="margin:1rem 0;text-align:center;">'
    + '<button style="background:#7c3aed;color:#fff;font-weight:700;font-size:0.95rem;padding:12px 28px;border:none;border-radius:10px;cursor:pointer;box-shadow:0 0 16px rgba(124,58,237,0.5),0 0 32px rgba(124,58,237,0.25);letter-spacing:0.02em;">' + _esc(label) + '</button>'
    + '</div>';
};

_RENDERERS['gradient_text'] = function(b) {
  var text = b.text || b.label || b.title || '';
  return '<span style="background:linear-gradient(135deg,#6366f1,#a855f7,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;font-weight:700;font-size:1.5rem;">' + _esc(text) + '</span>';
};

_RENDERERS['meteor_shower'] = function(b) {
  return _animFallback('meteor shower', b.title || b.label || b.text || '');
};

_RENDERERS['number_odometer'] = function(b) {
  return _animFallback('number odometer', b.title || b.label || b.text || '');
};

_RENDERERS['reveal_on_scroll'] = function(b) {
  return _animFallback('reveal on scroll', b.title || b.label || b.text || '');
};

_RENDERERS['shimmer_button'] = function(b) {
  var label = b.text || b.label || b.title || 'Action';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="margin:1rem 0;text-align:center;">'
    + '<style>.shimmer-btn-' + uid + '{position:relative;overflow:hidden;background:#7c3aed;color:#fff;font-weight:700;font-size:0.95rem;padding:12px 28px;border:none;border-radius:10px;cursor:pointer;}.shimmer-btn-' + uid + '::after{content:\'\';position:absolute;top:0;left:-100%;width:60%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.25),transparent);animation:shimmer-' + uid + ' 1.8s infinite;transform:skewX(-20deg);}@keyframes shimmer-' + uid + '{0%{left:-100%;}100%{left:160%;}}</style>'
    + '<button class="shimmer-btn-' + uid + '">' + _esc(label) + '</button>'
    + '</div>';
};

_RENDERERS['skeleton_stage_card'] = function(b) {
  return _animFallback('skeleton stage card', b.title || b.label || b.text || '');
};

_RENDERERS['sonar_pulse'] = function(b) {
  return _animFallback('sonar pulse', b.title || b.label || b.text || '');
};

_RENDERERS['svg_path_draw'] = function(b) {
  return _animFallback('SVG path draw', b.title || b.label || b.text || '');
};

_RENDERERS['typewriter'] = function(b) {
  var text = b.text || b.content || b.label || '';
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin:1rem 0;background:#1e1e2e;">'
    + '<pre style="margin:0;font-family:\'Courier New\',Courier,monospace;font-size:0.875rem;color:#cdd6f4;white-space:pre-wrap;line-height:1.6;">' + _esc(text) + '<span style="display:inline-block;width:2px;height:1em;background:#a855f7;vertical-align:text-bottom;animation:blink 1s step-end infinite;margin-left:2px;"></span></pre>'
    + '<style>@keyframes blink{0%,100%{opacity:1;}50%{opacity:0;}}</style>'
    + '</div>';
};

_RENDERERS['typewriter_text'] = function(b) {
  var text = b.text || b.content || b.label || '';
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin:1rem 0;background:#1e1e2e;">'
    + '<pre style="margin:0;font-family:\'Courier New\',Courier,monospace;font-size:0.875rem;color:#cdd6f4;white-space:pre-wrap;line-height:1.6;">' + _esc(text) + '<span style="display:inline-block;width:2px;height:1em;background:#a855f7;vertical-align:text-bottom;animation:blink 1s step-end infinite;margin-left:2px;"></span></pre>'
    + '<style>@keyframes blink{0%,100%{opacity:1;}50%{opacity:0;}}</style>'
    + '</div>';
};

_RENDERERS['typing_indicator'] = function(b) {
  return _animFallback('typing indicator', b.title || b.label || b.text || '');
};

_RENDERERS['word_flip'] = function(b) {
  return _animFallback('word flip', b.title || b.label || b.text || '');
};

_RENDERERS['word_scramble'] = function(b) {
  return _animFallback('word scramble', b.title || b.label || b.text || '');
};

_RENDERERS['animated_counter'] = function(b) {
  var value = b.value !== undefined ? b.value : (b.end !== undefined ? b.end : '');
  var label = b.label || b.title || '';
  return '<div style="border:1px dashed #d1d5db;border-radius:10px;padding:16px;margin:1rem 0;background:#fafafa;text-align:center;color:#9ca3af;font-size:0.82rem;">⚡ [animated counter — not available in this surface]<br><strong style="color:#7c3aed;font-size:1.5rem;">' + _esc(String(value)) + '</strong>' + (label ? '<br><span style="color:#374151;">' + _esc(label) + '</span>' : '') + '</div>';
};

_RENDERERS['parallax_section'] = function(b) {
  return _animFallback('parallax section', b.title || b.label || b.text || '');
};

_RENDERERS['scroll_trigger'] = function(b) {
  return _animFallback('scroll trigger', b.title || b.label || b.text || '');
};

_RENDERERS['floating_particles'] = function(b) {
  return _animFallback('floating particles', b.title || b.label || b.text || '');
};

_RENDERERS['confetti_burst'] = function(b) {
  return _animFallback('confetti burst', b.title || b.label || b.text || '');
};

_RENDERERS['glitch_text'] = function(b) {
  return _animFallback('glitch text', b.title || b.label || b.text || '');
};

_RENDERERS['neon_glow'] = function(b) {
  return _animFallback('neon glow', b.title || b.label || b.text || '');
};

_RENDERERS['tilt_card'] = function(b) {
  return _animFallback('tilt card', b.title || b.label || b.text || '');
};

_RENDERERS['magnetic_button'] = function(b) {
  return _animFallback('magnetic button', b.title || b.label || b.text || '');
};

