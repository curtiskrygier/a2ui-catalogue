/**
 * A2UI Gem Renderer
 *
 * Three modes:
 *   GET  ?p=BASE64   — decode base64 payload, render atoms (small schemas, shareable URL)
 *   POST ?p=JSON     — read raw JSON from form field (large schemas, no URL limit)
 *   GET  (no params) — serve the helper UI for pasting / encoding JSON
 */

function doGet(e) {
  var p = e && e.parameter && e.parameter.p;
  if (p) return _renderFromParam(p);
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('A2UI — Page Generator')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function doPost(e) {
  var raw = e.parameter && e.parameter.p;
  if (!raw && e.postData) raw = e.postData.contents;
  if (!raw) return doGet(e);
  try {
    var payload = JSON.parse(raw);
    return _renderFromPayload(payload);
  } catch (err) {
    // Fallback: treat as base64
    return _renderFromParam(raw);
  }
}

function _renderFromParam(encoded) {
  try {
    var bytes   = Utilities.base64Decode(encoded, Utilities.Charset.UTF_8);
    var json    = Utilities.newBlob(bytes).getDataAsString();
    return _renderFromPayload(JSON.parse(json));
  } catch (err) {
    return _errorPage(err.message);
  }
}

function _renderFromPayload(payload) {
  try {
    var blocks  = Array.isArray(payload) ? payload : (payload.blocks || []);
    var title   = (Array.isArray(payload) ? '' : payload.title) || 'A2UI Page';
    var theme   = (Array.isArray(payload) ? 'light' : payload.theme) || 'light';
    var content = renderAtoms(blocks, { theme: theme });
    var tmpl    = HtmlService.createTemplateFromFile('AtomPage');
    tmpl.title   = title;
    tmpl.content = content;
    tmpl.theme   = theme;
    tmpl.sidebar = false;
    return tmpl.evaluate()
      .setTitle(title)
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  } catch (err) {
    return _errorPage(err.message);
  }
}

function _errorPage(msg) {
  return HtmlService.createHtmlOutput(
    '<body style="font-family:monospace;padding:40px;background:#0a0f1e;color:#ef4444">' +
    '<h2>Render error</h2><pre>' + msg + '</pre>' +
    '<p><a href="' + ScriptApp.getService().getUrl() + '" style="color:#60a5fa">← Back to generator</a></p>' +
    '</body>'
  ).setTitle('Render error');
}

/** Called by AtomPage.html to include partial files. */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}
