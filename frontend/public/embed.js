/*!
 * AI Mock Interviewer embed widget.
 * Usage on any site (e.g. your portfolio):
 *   <div id="ai-interviewer"></div>
 *   <script src="https://YOUR-FRONTEND-HOST/embed.js"
 *           data-target="#ai-interviewer" data-theme="dark" data-accent="22c55e" data-height="760"></script>
 * Options: data-target (CSS selector, default: inserted after the script tag),
 *          data-theme (light|dark|auto), data-accent (hex without #), data-height (initial px).
 */
(function () {
  var script = document.currentScript;
  if (!script) return;
  var base = script.src.replace(/embed\.js(\?.*)?$/, "");
  var params = new URLSearchParams({ embed: "1" });
  var theme = script.getAttribute("data-theme");
  var accent = script.getAttribute("data-accent");
  if (theme && theme !== "auto") params.set("theme", theme);
  if (accent) params.set("accent", accent.replace("#", ""));

  var iframe = document.createElement("iframe");
  iframe.src = base + "index.html?" + params.toString() + "#/";
  iframe.title = "AI Mock Interviewer";
  iframe.allow = "microphone; clipboard-write";
  iframe.loading = "lazy";
  iframe.style.cssText = "width:100%;border:0;display:block;border-radius:16px;overflow:hidden;";
  iframe.style.height = (parseInt(script.getAttribute("data-height"), 10) || 760) + "px";

  var targetSelector = script.getAttribute("data-target");
  var target = targetSelector && document.querySelector(targetSelector);
  if (target) target.appendChild(iframe);
  else script.parentNode.insertBefore(iframe, script.nextSibling);

  var origin = new URL(base, window.location.href).origin;
  window.addEventListener("message", function (event) {
    if (event.origin !== origin || event.source !== iframe.contentWindow) return;
    var data = event.data || {};
    if (data.type === "ai-interviewer:height" && data.height > 0) {
      iframe.style.height = Math.max(520, Math.ceil(data.height)) + "px";
    }
  });
})();
