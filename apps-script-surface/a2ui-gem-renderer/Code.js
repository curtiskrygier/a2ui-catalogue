/**
 * A2UI Gem Renderer
 *
 * Two modes:
 *   ?p=BASE64   — decode payload, render atoms, serve the page
 *   (no params) — serve the helper UI for pasting / encoding JSON
 */

function doGet(e) {
  var p = e && e.parameter && e.parameter.p;

  if (p) {
    return _renderFromParam(p);
  }

  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('A2UI — Page Generator')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function _renderFromParam(encoded) {
  try {
    var bytes   = Utilities.base64Decode(encoded, Utilities.Charset.UTF_8);
    var json    = Utilities.newBlob(bytes).getDataAsString();
    var payload = JSON.parse(json);

    var blocks  = Array.isArray(payload) ? payload : (payload.blocks || []);
    var title   = (Array.isArray(payload) ? '' : payload.title) || 'A2UI Page';
    var theme   = (Array.isArray(payload) ? 'light' : payload.theme) || 'light';

    var content = renderAtoms(blocks, { theme: theme });

    var tmpl         = HtmlService.createTemplateFromFile('AtomPage');
    tmpl.title       = title;
    tmpl.content     = content;
    tmpl.theme       = theme;
    tmpl.sidebar     = false;

    return tmpl.evaluate()
      .setTitle(title)
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);

  } catch (err) {
    return HtmlService.createHtmlOutput(
      '<body style="font-family:monospace;padding:40px;background:#0a0f1e;color:#ef4444">' +
      '<h2>Render error</h2><pre>' + err.message + '</pre>' +
      '<p><a href="' + ScriptApp.getService().getUrl() + '" style="color:#60a5fa">← Back to generator</a></p>' +
      '</body>'
    ).setTitle('Render error');
  }
}

/** Called by AtomPage.html to include partial files. */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}
