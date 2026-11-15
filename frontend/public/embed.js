/*
 * Support Agent embed script. Add to any website:
 *
 *   <script src="https://YOUR-WIDGET-HOST/embed.js" data-lang="vi" data-color="#0f766e" async></script>
 *
 * It adds a chat button in the bottom-right corner that opens the assistant in an iframe.
 */
(function () {
  if (window.__supportAgentLoaded) return;
  window.__supportAgentLoaded = true;

  var script = document.currentScript;
  var host = new URL(script.src).origin;
  var lang = script.getAttribute("data-lang") === "vi" ? "vi" : "en";
  var color = script.getAttribute("data-color") || "#0f766e";
  var label = lang === "vi" ? "Hỗ trợ" : "Help";

  var frame = document.createElement("iframe");
  frame.src = host + "/widget?lang=" + lang;
  frame.title = lang === "vi" ? "Trợ lý hỗ trợ" : "Support assistant";
  frame.style.cssText =
    "position:fixed;right:20px;bottom:84px;width:380px;max-width:calc(100vw - 24px);height:560px;" +
    "max-height:calc(100vh - 108px);border:0;border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.22);" +
    "z-index:2147483646;display:none;background:#fff;color-scheme:normal";

  var button = document.createElement("button");
  button.type = "button";
  button.setAttribute("aria-expanded", "false");
  button.setAttribute("data-support-agent", "launcher");
  button.textContent = "💬 " + label;
  button.style.cssText =
    "position:fixed;right:20px;bottom:20px;z-index:2147483647;border:0;border-radius:999px;padding:13px 20px;" +
    "font:600 15px system-ui,sans-serif;color:#fff;cursor:pointer;box-shadow:0 6px 20px rgba(0,0,0,.2);background:" + color;

  button.addEventListener("click", function () {
    var open = frame.style.display === "none";
    frame.style.display = open ? "block" : "none";
    button.setAttribute("aria-expanded", String(open));
    button.textContent = open ? "✕" : "💬 " + label;
  });

  function mount() {
    document.body.appendChild(frame);
    document.body.appendChild(button);
  }
  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);
})();
