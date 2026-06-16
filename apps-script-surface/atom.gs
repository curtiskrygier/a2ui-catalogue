/**
 * Google Apps Script Web App Renderer — atom.gs
 * Server-side V8 JavaScript engine for rendering A2UI Atom components.
 */

/**
 * Main entry point: renders an array of atom blocks to an HTML string.
 *
 * @param {Object[]} blocks - List of atom block objects (complying with schema.yaml).
 * @param {Object} [opts] - Configuration options.
 * @param {string} [opts.theme='light'] - 'light' or 'dark'.
 * @param {boolean} [opts.sidebar=false] - If true, optimized for sidebar width.
 * @returns {string} Injected HTML fragment.
 */
function renderAtoms(blocks, opts) {
  if (!blocks || !Array.isArray(blocks)) {
    return '<!-- a2ui: blocks list is empty or invalid -->';
  }
  
  opts = opts || {};
  var theme = opts.theme || 'light';
  var sidebar = !!opts.sidebar;
  
  var parts = [];
  for (var i = 0; i < blocks.length; i++) {
    var block = blocks[i];
    var btype = block.component || block.type;
    var fn = _RENDERERS[btype];
    
    if (fn) {
      try {
        parts.append ? parts.append(fn(block)) : parts.push(fn(block));
      } catch (err) {
        parts.push('<div class="asw-callout" style="border-left-color:var(--red);">' +
                   '<span class="asw-callout-icon">⚠️</span>' +
                   '<div class="asw-callout-content">Error rendering <strong>' + _esc(btype) + '</strong>: ' + _esc(err.message) + '</div>' +
                   '</div>');
      }
    } else {
      parts.push('<!-- a2ui: unknown or unsupported atom "' + _esc(btype) + '" -->');
    }
  }
  
  return parts.join('\n\n');
}

/**
 * Apps Script HTML Template include helper.
 * Pulls partial files (AtomStyles, AtomScripts) dynamically.
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

// ── HTML Escape Helper ────────────────────────────────────────────────────────
function _esc(str) {
  if (str === undefined || str === null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ── Renderers Registry ────────────────────────────────────────────────────────
var _RENDERERS = {};

// ── Category A: Static Content Renderers ──────────────────────────────────────

_RENDERERS['body'] = function(b) {
  return '<p class="asw-body">' + _markdownToHtml(b.text) + '</p>';
};

_RENDERERS['paragraph'] = function(b) {
  return '<p class="asw-paragraph">' + _markdownToHtml(b.text) + '</p>';
};

_RENDERERS['text_block'] = function(b) {
  return '<p class="asw-text-block">' + _markdownToHtml(b.text) + '</p>';
};

_RENDERERS['heading'] = function(b) {
  var level = b.level || 2;
  return '<h' + level + ' class="asw-heading">' + _esc(b.text) + '</h' + level + '>';
};

_RENDERERS['subheading'] = function(b) {
  var level = b.level || 3;
  return '<h' + level + ' class="asw-subheading">' + _esc(b.text) + '</h' + level + '>';
};

_RENDERERS['blockquote'] = function(b) {
  var cite = b.attribution ? '<cite style="display:block;margin-top:6px;font-size:0.8rem;text-align:right;">— ' + _esc(b.attribution) + '</cite>' : '';
  return '<blockquote>' + _markdownToHtml(b.text) + cite + '</blockquote>';
};

_RENDERERS['divider'] = function(b) {
  return '<hr class="asw-divider">';
};

_RENDERERS['spacer'] = function(b) {
  var height = b.height || 20;
  return '<div class="asw-spacer" style="height:' + height + 'px;"></div>';
};

_RENDERERS['callout'] = function(b) {
  var icon = b.icon || '💡';
  var color = b.color || 'var(--accent)';
  return '<div class="asw-callout" style="border-left-color:' + color + ';">' +
         '<span class="asw-callout-icon">' + icon + '</span>' +
         '<div class="asw-callout-content">' + _markdownToHtml(b.text) + '</div>' +
         '</div>';
};

_RENDERERS['alert_banner'] = function(b) {
  var variant = b.variant || 'info'; // info, success, warning, critical
  var icons = { info: 'ℹ️', success: '✅', warning: '⚠️', critical: '🚨' };
  var colors = { info: 'var(--accent)', success: 'var(--green)', warning: 'var(--orange)', critical: 'var(--red)' };
  
  return '<div class="asw-callout" style="border-left-color:' + colors[variant] + '; background:var(--surface2);">' +
         '<span class="asw-callout-icon">' + (b.icon || icons[variant]) + '</span>' +
         '<div class="asw-callout-content" style="font-weight:500;">' + _markdownToHtml(b.text) + '</div>' +
         '</div>';
};

_RENDERERS['info_card'] = function(b) {
  return '<div class="asw-native-card">' +
         (b.title ? '<div style="font-weight:700;margin-bottom:8px;font-size:0.95rem;">' + _esc(b.title) + '</div>' : '') +
         '<div style="font-size:0.88rem;color:var(--muted);">' + _markdownToHtml(b.text) + '</div>' +
         '</div>';
};

_RENDERERS['code_block'] = function(b) {
  return '<pre><code class="language-' + _esc(b.language || 'text') + '">' + _esc(b.content) + '</code></pre>';
};

_RENDERERS['code'] = function(b) {
  return '<pre><code class="language-' + _esc(b.language || 'text') + '">' + _esc(b.content) + '</code></pre>';
};

_RENDERERS['inline_code'] = function(b) {
  return '<code>' + _esc(b.text) + '</code>';
};

_RENDERERS['tag_chip'] = function(b) {
  var color = b.color || 'var(--accent)';
  return '<span class="asw-badge" style="background:rgba(26,115,232,0.1);color:' + color + ';padding:4px 8px;border-radius:12px;font-size:0.75rem;font-weight:600;margin-right:6px;">' + _esc(b.text) + '</span>';
};

_RENDERERS['badge'] = function(b) {
  var color = b.color || 'var(--muted)';
  return '<span class="asw-badge" style="border:1px solid ' + color + ';color:' + color + ';padding:2px 6px;border-radius:4px;font-size:0.7rem;font-weight:600;text-transform:uppercase;">' + _esc(b.text) + '</span>';
};

_RENDERERS['image'] = function(b) {
  var caption = b.caption ? '<div style="font-size:0.8rem;color:var(--muted);text-align:center;margin-top:6px;">' + _esc(b.caption) + '</div>' : '';
  return '<div style="margin:16px 0;text-align:center;">' +
         '<img src="' + _esc(b.url) + '" alt="' + _esc(b.alt || '') + '" style="max-width:100%;border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">' +
         caption +
         '</div>';
};

_RENDERERS['highlighted_text'] = function(b) {
  var color = b.color || '#fef08a';
  var noteAttr = b.annotation ? ' data-note="' + _esc(b.annotation) + '"' : '';
  return '<mark class="asw-highlight" style="background:' + color + '"' + noteAttr + '>' + _esc(b.text) + '</mark>';
};

_RENDERERS['table'] = function(b) {
  var html = '<table>';
  if (b.headers && b.headers.length) {
    html += '<thead><tr>';
    for (var i = 0; i < b.headers.length; i++) {
      html += '<th>' + _esc(b.headers[i]) + '</th>';
    }
    html += '</tr></thead>';
  }
  if (b.rows && b.rows.length) {
    html += '<tbody>';
    for (var r = 0; r < b.rows.length; r++) {
      html += '<tr>';
      for (var c = 0; c < b.rows[r].length; c++) {
        html += '<td>' + _markdownToHtml(b.rows[r][c]) + '</td>';
      }
      html += '</tr>';
    }
    html += '</tbody>';
  }
  html += '</table>';
  return html;
};

_RENDERERS['bullet_list'] = function(b) {
  var html = '<ul>';
  for (var i = 0; i < b.items.length; i++) {
    var item = b.items[i];
    var lead = item.label ? '<strong>' + _esc(item.label) + ': </strong>' : '';
    html += '<li>' + lead + _markdownToHtml(item.text) + '</li>';
  }
  html += '</ul>';
  return html;
};

// ── Category B: Link / Navigation Renderers ─────────────────────────────────

_RENDERERS['link_button'] = function(b) {
  return '<div style="margin:12px 0;">' +
         '<a href="' + _esc(b.url) + '" class="asw-btn asw-btn-primary" target="_top">' + _esc(b.label) + '</a>' +
         '</div>';
};

_RENDERERS['cta_button'] = function(b) {
  return '<div style="margin:16px 0;text-align:center;">' +
         '<a href="' + _esc(b.url) + '" class="asw-btn asw-btn-primary" style="padding:10px 24px;font-size:0.85rem;" target="_top">' + _esc(b.label) + '</a>' +
         '</div>';
};

_RENDERERS['nav_link'] = function(b) {
  return '<a href="' + _esc(b.url) + '" class="asw-nav-link" style="font-size:0.88rem;font-weight:500;margin-right:12px;" target="_top">' + _esc(b.label) + '</a>';
};

_RENDERERS['lesson_nav'] = function(b) {
  var prevHtml = b.prev_url ? 
    '<a href="' + _esc(b.prev_url) + '" class="asw-lesson-nav-side" target="_top"><span class="nav-arrow">←</span><span>' + _esc(b.prev_title || 'Previous') + '</span></a>' : 
    '<span></span>';
  var nextHtml = b.next_url ? 
    '<a href="' + _esc(b.next_url) + '" class="asw-lesson-nav-side" style="justify-content:flex-end;text-align:right;" target="_top"><span>' + _esc(b.next_title || 'Next') + '</span><span class="nav-arrow">→</span></a>' : 
    '<span></span>';
  
  var moduleLabel = b.module_label ? '<div class="asw-lesson-nav-module">' + _esc(b.module_label) + '</div>' : '';
  
  var checkbox = b.show_completion ? 
    '<label class="asw-complete-row"><input type="checkbox" onchange="if(typeof localStorage !== \'undefined\'){localStorage.setItem(\'complete-\' + ' + JSON.stringify(b.current_title) + ', this.checked);}"> Mark as complete</label>' : '';

  return '<div class="asw-lesson-nav">' +
         prevHtml +
         '<div class="asw-lesson-nav-center">' + moduleLabel + '<div class="asw-lesson-nav-title">' + _esc(b.current_title) + '</div>' + checkbox + '</div>' +
         nextHtml +
         '</div>';
};

_RENDERERS['course_progress_card'] = function(b) {
  var modules = b.modules || [];
  var accent = b.accent || 'var(--accent)';
  var lessonsTotal = 0;
  var lessonsDone = 0;
  
  var modsHtml = '';
  for (var i = 0; i < modules.length; i++) {
    var m = modules[i];
    var lt = m.lessons_total || 1;
    var ld = m.lessons_done || 0;
    lessonsTotal += lt;
    lessonsDone += ld;
    var mpct = Math.min(100, Math.round((ld / lt) * 100));
    
    modsHtml += '<div class="asw-course-module">' +
                '<div class="asw-course-mod-row">' +
                '<span class="asw-course-mod-name">' + _esc(m.title) + '</span>' +
                '<span class="asw-course-mod-pct">' + ld + '/' + lt + '</span>' +
                '</div>' +
                '<div class="asw-course-bar-track">' +
                '<div class="asw-course-bar-fill" style="width:' + mpct + '%;background:' + accent + ';"></div>' +
                '</div>' +
                '</div>';
  }
  
  var overallPct = lessonsTotal ? Math.min(100, Math.round((lessonsDone / lessonsTotal) * 100)) : 0;
  
  return '<div class="asw-course-card">' +
         '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">' +
         '<div class="asw-course-title">' + _esc(b.course_title) + '</div>' +
         '<div style="font-family:var(--mono);font-size:1.1rem;font-weight:700;color:' + accent + '">' + overallPct + '%</div>' +
         '</div>' +
         modsHtml +
         '</div>';
};

// ── Category C: Interactive Renderers ────────────────────────────────────────

_RENDERERS['quiz_question'] = function(b) {
  var options = b.options || [];
  var correctIdx = b.correct || 0;
  var explanation = b.explanation || '';
  var atomId = b.id || 'quiz-' + Math.floor(Math.random() * 100000);
  var uid = 'q' + Math.floor(Math.random() * 100000);

  var optsHtml = '';
  for (var i = 0; i < options.length; i++) {
    optsHtml += '<div class="asw-quiz-opt" id="' + uid + '-opt-' + i + '" data-idx="' + i + '">' + _esc(options[i]) + '</div>';
  }

  var expHtml = explanation ? '<div class="asw-quiz-explain" id="' + uid + '-explain">' + _markdownToHtml(explanation) + '</div>' : '';

  var initScript = '<script>(function(){ initQuiz(' + JSON.stringify(uid) + ',' + correctIdx + ',' + JSON.stringify(atomId) + '); })();</script>';

  return '<div class="asw-quiz" id="' + uid + '-quiz">' +
         '<div class="asw-quiz-label">Question</div>' +
         '<div class="asw-quiz-q">' + _esc(b.question) + '</div>' +
         '<div class="asw-quiz-opts">' + optsHtml + '</div>' +
         expHtml +
         '</div>' +
         initScript;
};

_RENDERERS['fill_in_blank'] = function(b) {
  var template = b.template || '';
  var atomId = b.id || 'fib-' + Math.floor(Math.random() * 100000);
  var uid = 'fib' + Math.floor(Math.random() * 100000);
  var hintHtml = b.hint ? '<p style="margin-top:8px;font-size:0.8rem;color:var(--muted)">💡 ' + _esc(b.hint) + '</p>' : '';

  var blankIdx = 0;
  var htmlTemplate = template.replace(/\{blank\}/g, function() {
    var i = blankIdx++;
    return '<input class="asw-fib-input" id="' + uid + '-inp-' + i + '" data-idx="' + i + '" placeholder="…" autocomplete="off">';
  });

  var initScript = '<script>(function(){ initFillInBlank(' + JSON.stringify(uid) + ',' + JSON.stringify(atomId) + '); })();</script>';

  return '<div class="asw-fib" id="' + uid + '-fib">' +
         '<div class="asw-fib-label">Fill in the blank</div>' +
         '<div style="font-size:0.9rem;line-height:2;">' + htmlTemplate + '</div>' +
         hintHtml +
         '<div class="asw-fib-actions">' +
         '<button class="asw-btn asw-btn-primary" id="' + uid + '-check">Check</button>' +
         '<button class="asw-btn asw-btn-ghost" id="' + uid + '-reset">Reset</button>' +
         '</div>' +
         '</div>' +
         initScript;
};

_RENDERERS['match_exercise'] = function(b) {
  var pairs = b.pairs || [];
  var atomId = b.id || 'match-' + Math.floor(Math.random() * 100000);
  var uid = 'match' + Math.floor(Math.random() * 100000);
  
  var lefts = [];
  var rights = [];
  var correctMap = {};
  
  for (var i = 0; i < pairs.length; i++) {
    lefts.push({ idx: i, text: pairs[i].term });
    rights.push({ idx: i, text: pairs[i].definition });
  }

  // Shuffle right side if desired
  if (b.shuffle !== false) {
    rights.sort(function() { return Math.random() - 0.5; });
  }

  // Map left idx to right side visual position idx
  for (var l = 0; l < lefts.length; l++) {
    for (var r = 0; r < rights.length; r++) {
      if (lefts[l].idx === rights[r].idx) {
        correctMap[l] = r;
      }
    }
  }

  var leftsHtml = '';
  for (var l = 0; l < lefts.length; l++) {
    leftsHtml += '<div class="asw-match-item" id="' + uid + '-l-' + l + '" data-side="left" data-idx="' + l + '">' + _esc(lefts[l].text) + '</div>';
  }

  var rightsHtml = '';
  for (var r = 0; r < rights.length; r++) {
    rightsHtml += '<div class="asw-match-item" id="' + uid + '-r-' + r + '" data-side="right" data-idx="' + r + '">' + _esc(rights[r].text) + '</div>';
  }

  var initScript = '<script>(function(){ initMatchExercise(' + JSON.stringify(uid) + ',' + JSON.stringify(atomId) + ',' + JSON.stringify(correctMap) + '); })();</script>';

  return '<div class="asw-match">' +
         '<div class="asw-match-label">Matching Exercise</div>' +
         '<div class="asw-match-sub">Click a term, then click its matching definition.</div>' +
         '<div class="asw-match-grid">' +
         '<div class="asw-match-col"><h4>Term</h4>' + leftsHtml + '</div>' +
         '<div class="asw-match-col"><h4>Definition</h4>' + rightsHtml + '</div>' +
         '</div>' +
         '<div class="asw-match-score">Matched: <strong id="' + uid + '-score">0 / ' + pairs.length + '</strong></div>' +
         '</div>' +
         initScript;
};

_RENDERERS['hint_reveal'] = function(b) {
  var accent = b.accent || 'var(--accent)';
  var label = b.label || 'Show hint';
  return '<details class="asw-hint" style="border-left-color:' + accent + ';">' +
         '<summary style="color:' + accent + ';">' + _esc(label) + '</summary>' +
         '<div class="asw-hint-body">' + _markdownToHtml(b.hint) + '</div>' +
         '</details>';
};

_RENDERERS['achievement_badge'] = function(b) {
  var icon = b.icon || '🏆';
  var color = b.color || 'var(--yellow)';
  var size = b.size || 'card';
  var locked = !!b.locked;
  
  var badgeClass = 'asw-achievement' + (locked ? ' locked' : '');
  var unlockedHtml = b.unlocked_at && !locked ? '<div class="asw-achievement-date">Unlocked ' + _esc(b.unlocked_at) + '</div>' : '';

  if (size === 'pill') {
    return '<span class="' + badgeClass + '" style="border-color:' + color + ';display:inline-flex;padding:6px 14px;align-items:center;gap:6px;margin:4px 0;">' +
           '<span class="asw-achievement-icon" style="font-size:1.1rem;line-height:1;">' + icon + '</span>' +
           '<span class="asw-achievement-title" style="color:' + color + ';margin:0;font-size:0.8rem;">' + _esc(b.title) + '</span>' +
           '</span>';
  }

  return '<div class="' + badgeClass + '" style="border-color:' + color + ';">' +
         '<div class="asw-achievement-icon">' + icon + '</div>' +
         '<div>' +
         '<div class="asw-achievement-title" style="color:' + color + '">' + _esc(b.title) + '</div>' +
         (b.description ? '<div class="asw-achievement-desc">' + _esc(b.description) + '</div>' : '') +
         unlockedHtml +
         '</div>' +
         '</div>';
};

_RENDERERS['score_summary'] = function(b) {
  var correct = b.correct || 0;
  var total = b.total || 1;
  var pct = Math.min(100, Math.round((correct / total) * 100));
  var passed = pct >= (b.pass_threshold || 60);
  var classPct = passed ? '' : ' fail';
  var label = passed ? 'Passed' : 'Failed';
  
  var timeHtml = b.time_taken ? 
    '<div class="asw-score-stat"><div class="asw-score-stat-val">' + _esc(b.time_taken) + '</div><div class="asw-score-stat-lbl">Time</div></div>' : '';
  
  var ctas = '';
  if (b.retry_label || b.continue_label) {
    var retry = b.retry_label ? '<button class="asw-btn asw-btn-ghost" onclick="if(typeof location !== \'undefined\')location.reload();">' + _esc(b.retry_label) + '</button>' : '';
    var cont = b.continue_label ? '<a href="' + _esc(b.continue_url || '#') + '" class="asw-btn asw-btn-primary" target="_top">' + _esc(b.continue_label) + '</a>' : '';
    ctas = '<div class="asw-score-ctas">' + retry + cont + '</div>';
  }

  return '<div class="asw-score">' +
         '<div class="asw-score-pct' + classPct + '">' + pct + '%</div>' +
         '<div class="asw-score-label">' + label + '</div>' +
         '<div class="asw-score-row">' +
         '<div class="asw-score-stat"><div class="asw-score-stat-val">' + correct + '/' + total + '</div><div class="asw-score-stat-lbl">Score</div></div>' +
         timeHtml +
         '</div>' +
         ctas +
         '</div>';
};

_RENDERERS['xp_bar'] = function(b) {
  var xpCurrent = b.xp_current || 0;
  var xpNext = b.xp_next || 100;
  var pct = Math.min(100, Math.round((xpCurrent / xpNext) * 100));
  var accent = b.accent || 'var(--accent)';
  
  return '<div class="asw-xp">' +
         '<div class="asw-xp-row">' +
         '<span class="asw-xp-level">' + _esc(b.level_label || 'Level 1') + '</span>' +
         '<span class="asw-xp-count">' + xpCurrent + ' / ' + xpNext + ' XP</span>' +
         '</div>' +
         '<div class="asw-xp-track">' +
         '<div class="asw-xp-fill" style="width:' + pct + '%;background:' + accent + ';"></div>' +
         '</div>' +
         '</div>';
};

// ── Category D: Workspace-Native Renderers ───────────────────────────────────

_RENDERERS['drive_file_list'] = function(b) {
  var folderId = b.folder_id;
  var maxResults = b.max_results || 10;
  var files = [];
  var errorMsg = null;
  
  // Real implementation (GAS native server code)
  if (typeof DriveApp !== 'undefined') {
    try {
      var folder = DriveApp.getFolderById(folderId);
      var fileIterator = folder.getFiles();
      var count = 0;
      while (fileIterator.hasNext() && count < maxResults) {
        var file = fileIterator.next();
        files.push({
          name: file.getName(),
          url: file.getUrl(),
          mimeType: file.getMimeType()
        });
        count++;
      }
    } catch (err) {
      errorMsg = err.message;
    }
  } else {
    // Fallback/Mock data for preview
    files = [
      { name: 'Document_1.pdf', url: '#', mimeType: 'application/pdf' },
      { name: 'Project_Sheet.xlsx', url: '#', mimeType: 'application/vnd.google-apps.spreadsheet' },
      { name: 'Slideshow.gslides', url: '#', mimeType: 'application/vnd.google-apps.presentation' }
    ];
  }

  var listHtml = '';
  if (errorMsg) {
    listHtml = '<div style="font-size:0.82rem;color:var(--red);">Unable to retrieve files: ' + _esc(errorMsg) + '</div>';
  } else if (files.length === 0) {
    listHtml = '<div style="font-size:0.82rem;color:var(--muted);">No files found in folder.</div>';
  } else {
    listHtml += '<ul class="asw-drive-list">';
    for (var i = 0; i < files.length; i++) {
      var icon = '📄';
      if (files[i].mimeType.indexOf('pdf') !== -1) icon = '📕';
      else if (files[i].mimeType.indexOf('spreadsheet') !== -1) icon = '📊';
      else if (files[i].mimeType.indexOf('presentation') !== -1) icon = '📈';
      else if (files[i].mimeType.indexOf('folder') !== -1) icon = '📁';
      
      listHtml += '<li class="asw-drive-item">' +
                  '<span class="asw-drive-icon">' + icon + '</span>' +
                  '<a href="' + _esc(files[i].url) + '" class="asw-drive-link" target="_top">' + _esc(files[i].name) + '</a>' +
                  '</li>';
    }
    listHtml += '</ul>';
  }

  return '<div class="asw-native-card">' +
         '<div class="asw-native-header"><span class="asw-native-header-icon">📁</span> Google Drive Folder</div>' +
         listHtml +
         '</div>';
};

_RENDERERS['sheet_preview'] = function(b) {
  var spreadsheetId = b.spreadsheet_id;
  var sheetName = b.sheet_name;
  var rangeStr = b.range;
  var data = [];
  var errorMsg = null;
  
  if (typeof SpreadsheetApp !== 'undefined') {
    try {
      var ss = SpreadsheetApp.openById(spreadsheetId);
      var sheet = sheetName ? ss.getSheetByName(sheetName) : ss.getSheets()[0];
      var range = sheet.getRange(rangeStr);
      data = range.getValues();
    } catch (err) {
      errorMsg = err.message;
    }
  } else {
    // Fallback/Mock data for preview
    data = [
      ['Header 1', 'Header 2', 'Header 3'],
      ['Row 1 Col 1', 'Row 1 Col 2', 'Row 1 Col 3'],
      ['Row 2 Col 1', 'Row 2 Col 2', 'Row 2 Col 3']
    ];
  }

  var tableHtml = '';
  if (errorMsg) {
    tableHtml = '<div style="font-size:0.82rem;color:var(--red);">Unable to load Sheet range: ' + _esc(errorMsg) + '</div>';
  } else {
    tableHtml += '<div class="asw-sheet-preview-wrapper"><table class="asw-sheet-table">';
    for (var r = 0; r < data.length; r++) {
      tableHtml += '<tr>';
      for (var c = 0; c < data[r].length; c++) {
        var cellText = _esc(data[r][c]);
        if (r === 0) {
          tableHtml += '<th>' + cellText + '</th>';
        } else {
          tableHtml += '<td>' + cellText + '</td>';
        }
      }
      tableHtml += '</tr>';
    }
    tableHtml += '</table></div>';
  }

  return '<div class="asw-native-card">' +
         '<div class="asw-native-header"><span class="asw-native-header-icon">📊</span> Google Sheet Live Preview (' + _esc(sheetName || 'Sheet1') + '!' + _esc(rangeStr) + ')</div>' +
         tableHtml +
         '</div>';
};

_RENDERERS['gmail_summary'] = function(b) {
  var query = b.query || 'is:unread';
  var maxResults = b.max_results || 5;
  var threads = [];
  var errorMsg = null;
  
  if (typeof GmailApp !== 'undefined') {
    try {
      var gmailThreads = GmailApp.search(query, 0, maxResults);
      for (var i = 0; i < gmailThreads.length; i++) {
        var firstMsg = gmailThreads[i].getMessages()[0];
        threads.push({
          subject: gmailThreads[i].getFirstMessageSubject(),
          from: firstMsg.getFrom(),
          date: firstMsg.getDate().toLocaleDateString()
        });
      }
    } catch (err) {
      errorMsg = err.message;
    }
  } else {
    // Fallback/Mock data for preview
    threads = [
      { from: 'Google Apps Script team <dev@google.com>', subject: 'New V8 features available', date: '6/16/2026' },
      { from: 'GitHub Notification <noreply@github.com>', subject: '[a2ui-catalogue] Pull request #4 merged', date: '6/15/2026' }
    ];
  }

  var listHtml = '';
  if (errorMsg) {
    listHtml = '<div style="font-size:0.82rem;color:var(--red);">Gmail access failed: ' + _esc(errorMsg) + '</div>';
  } else if (threads.length === 0) {
    listHtml = '<div style="font-size:0.82rem;color:var(--muted);">No messages matched query "' + _esc(query) + '".</div>';
  } else {
    listHtml += '<ul class="asw-gmail-list">';
    for (var i = 0; i < threads.length; i++) {
      listHtml += '<li class="asw-gmail-item">' +
                  '<div class="asw-gmail-meta">' +
                  '<span class="asw-gmail-from">' + _esc(threads[i].from) + '</span>' +
                  '<span class="asw-gmail-date">' + _esc(threads[i].date) + '</span>' +
                  '</div>' +
                  '<div class="asw-gmail-subject">' + _esc(threads[i].subject) + '</div>' +
                  '</li>';
    }
    listHtml += '</ul>';
  }

  return '<div class="asw-native-card">' +
         '<div class="asw-native-header"><span class="asw-native-header-icon">✉️</span> Gmail Search: "' + _esc(query) + '"</div>' +
         listHtml +
         '</div>';
};

_RENDERERS['calendar_upcoming'] = function(b) {
  var maxResults = b.max_results || 5;
  var events = [];
  var errorMsg = null;
  
  if (typeof CalendarApp !== 'undefined') {
    try {
      var cal = CalendarApp.getDefaultCalendar();
      var now = new Date();
      var end = new Date(now.getTime() + (30 * 24 * 60 * 60 * 1000)); // 30 days ahead
      var calEvents = cal.getEvents(now, end);
      
      var limit = Math.min(calEvents.length, maxResults);
      for (var i = 0; i < limit; i++) {
        var start = calEvents[i].getStartTime();
        events.push({
          title: calEvents[i].getTitle(),
          startDay: start.getDate(),
          startMonth: start.toLocaleDateString(undefined, { month: 'short' }),
          timeStr: start.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
        });
      }
    } catch (err) {
      errorMsg = err.message;
    }
  } else {
    // Fallback/Mock data for preview
    events = [
      { title: 'A2UI Review Meeting', startDay: 18, startMonth: 'Jun', timeStr: '10:00 AM' },
      { title: 'Weekly Pair Programming', startDay: 20, startMonth: 'Jun', timeStr: '02:00 PM' }
    ];
  }

  var listHtml = '';
  if (errorMsg) {
    listHtml = '<div style="font-size:0.82rem;color:var(--red);">Calendar access failed: ' + _esc(errorMsg) + '</div>';
  } else if (events.length === 0) {
    listHtml = '<div style="font-size:0.82rem;color:var(--muted);">No upcoming events.</div>';
  } else {
    listHtml += '<ul class="asw-cal-list">';
    for (var i = 0; i < events.length; i++) {
      listHtml += '<li class="asw-cal-item">' +
                  '<div class="asw-cal-date-badge">' +
                  '<span class="day">' + events[i].startDay + '</span>' +
                  '<span class="month">' + events[i].startMonth + '</span>' +
                  '</div>' +
                  '<div class="asw-cal-details">' +
                  '<span class="asw-cal-title">' + _esc(events[i].title) + '</span>' +
                  '<span class="asw-cal-time">⏰ ' + events[i].timeStr + '</span>' +
                  '</div>' +
                  '</li>';
    }
    listHtml += '</ul>';
  }

  return '<div class="asw-native-card">' +
         '<div class="asw-native-header"><span class="asw-native-header-icon">📅</span> Calendar Schedule</div>' +
         listHtml +
         '</div>';
};

_RENDERERS['user_greeting'] = function(b) {
  var prefix = b.prefix || 'Hello';
  var email = 'curtis@example.com';
  
  if (typeof Session !== 'undefined') {
    try {
      email = Session.getActiveUser().getEmail() || email;
    } catch (err) {}
  }
  
  var initial = email.charAt(0).toUpperCase();

  return '<div class="asw-user-greeting">' +
         '<div class="asw-user-avatar">' + initial + '</div>' +
         '<div>' + _esc(prefix) + ', <span class="asw-user-email">' + _esc(email) + '</span>!</div>' +
         '</div>';
};

_RENDERERS['script_run_button'] = function(b) {
  var label = b.label || 'Run Script';
  var functionName = b.function_name || 'myFunction';
  var argument = b.argument || '';
  var btnId = 'btn-' + Math.floor(Math.random() * 100000);

  return '<div style="margin:16px 0; display:flex; align-items:center; gap:12px;">' +
         '<button id="' + btnId + '" class="asw-btn asw-btn-primary" onclick="runCustomScript(' + 
         JSON.stringify(btnId) + ',' + JSON.stringify(functionName) + ',' + JSON.stringify(argument) + ')">' +
         '<span class="asw-spinner" style="display:none;"></span>' +
         '<span class="asw-btn-label">' + _esc(label) + '</span>' +
         '</button>' +
         '<span id="' + btnId + '-status" style="font-size:0.8rem; font-weight:500;"></span>' +
         '</div>';
};

// ── Category E: Degraded Renderers ───────────────────────────────────────────

_RENDERERS['youtube'] = function(b) {
  return '<div class="asw-degraded-card">' +
         '<div class="asw-degraded-title">📹 YouTube Video Fallback</div>' +
         '<div class="asw-degraded-text">Direct iframe playback is restricted inside the Google Apps Script Web App sandbox environment.</div>' +
         '<a href="' + _esc(b.url) + '" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Watch on YouTube →</a>' +
         '</div>';
};

_RENDERERS['embed_codepen'] = _degradedLinkRenderer('CodePen sandbox embed');
_RENDERERS['embed_stackblitz'] = _degradedLinkRenderer('StackBlitz sandbox embed');
_RENDERERS['embed_gist'] = _degradedLinkRenderer('GitHub Gist widget');
_RENDERERS['embed_google_slides'] = _degradedLinkRenderer('Google Slides preview iframe');
_RENDERERS['figma_embed'] = _degradedLinkRenderer('Figma interactive canvas design preview');

function _degradedLinkRenderer(typeName) {
  return function(b) {
    var url = b.url || '#';
    return '<div class="asw-degraded-card">' +
           '<div class="asw-degraded-title">🔗 External Resource (' + typeName + ')</div>' +
           '<div class="asw-degraded-text">Interactive frames are restricted inside the Google Apps Script iframe sandbox.</div>' +
           '<a href="' + _esc(url) + '" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Open Link in New Tab →</a>' +
           '</div>';
  };
}

_RENDERERS['lottie_animation'] = function(b) {
  return b.fallback_image_url ? 
    _RENDERERS['image']({ url: b.fallback_image_url, caption: b.caption || 'Animation static preview' }) : 
    '<!-- lottie animation stripped: requires external client JS bundles -->';
};

_RENDERERS['parallax_card'] = function(b) {
  // Degrades to static card presentation
  return '<div class="asw-native-card" style="background-image:linear-gradient(rgba(0,0,0,0.05), rgba(0,0,0,0.05));">' +
         '<div style="font-weight:700;margin-bottom:8px;">' + _esc(b.title || 'Parallax Card') + '</div>' +
         '<div style="font-size:0.88rem;color:var(--muted);">' + _esc(b.subtitle || '') + '</div>' +
         '</div>';
};

_RENDERERS['embed_tweet'] = function(b) {
  return '<blockquote class="asw-twitter-degraded" style="border-left-color:#1da1f2;">' +
         '<div style="font-size:0.75rem;font-weight:700;color:#1da1f2;margin-bottom:6px;">𝕏 Tweet (Static View)</div>' +
         '<p>' + _esc(b.text || 'Tweet contents') + '</p>' +
         (b.author ? '<cite style="display:block;margin-top:4px;font-size:0.8rem;text-align:right;">— ' + _esc(b.author) + '</cite>' : '') +
         '</blockquote>';
};

_RENDERERS['social_feed_embed'] = function(b) {
  return '<div class="asw-degraded-card">' +
         '<div class="asw-degraded-title">💬 Social Media Feed</div>' +
         '<div class="asw-degraded-text">Live media feeds are disabled. Click below to view directly.</div>' +
         '<a href="' + _esc(b.url || '#') + '" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Open Social Feed →</a>' +
         '</div>';
};

// ── Markdown Parser Stub ──────────────────────────────────────────────────────
// Custom simple parser to map bold (**), italic (*), and link syntax to HTML tags.
function _markdownToHtml(md) {
  if (!md) return '';
  var res = _esc(md);
  
  // Bold **word**
  res = res.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Italic *word*
  res = res.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Inline link: [text](url) - force target="_top" for GAS Web App CSP
  res = res.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_top">$1</a>');
  
  return res;
}

// ── Server-Side Handlers Stubs (Can be overridden by custom GAS apps) ─────────
function saveQuizAnswer(atomId, selectedIdx) {
  var user = Session.getActiveUser().getEmail() || 'anonymous';
  var prop = PropertiesService.getUserProperties();
  prop.setProperty('quiz_' + atomId + '_' + user, String(selectedIdx));
  return { success: true, user: user, atomId: atomId, selectedIdx: selectedIdx };
}

function checkFillInBlank(atomId, userAnswers) {
  // Stubs for validating on server. Standard checks can also be client-driven.
  // We return validation array for answers
  return { success: true, correct: userAnswers.map(function(ans) { return !!ans; }) };
}

function saveMatchResult(atomId, score) {
  var user = Session.getActiveUser().getEmail() || 'anonymous';
  return { success: true, user: user, atomId: atomId, score: score };
}

function unlockAchievement(badgeId) {
  return { success: true, badgeId: badgeId };
}

function getXP(userId) {
  return { success: true, xp: 120 };
}

function getScoreData(sessionId) {
  return { success: true, score: 80 };
}

function submitFeedback(data) {
  return { success: true };
}
