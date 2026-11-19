// Embedding support. URL options (before or after the #):
//   ?embed=1            compact chrome for iframes
//   ?theme=light|dark   force a colour scheme (default: follows the OS)
//   ?accent=4f46e5      brand colour as hex, without '#'
// In embed mode the page posts its height to the parent so embed.js can size the iframe.

function readParams(): URLSearchParams {
  const params = new URLSearchParams(window.location.search);
  const hashQuery = window.location.hash.split("?")[1];
  if (hashQuery) new URLSearchParams(hashQuery).forEach((v, k) => params.set(k, v));
  return params;
}

const params = readParams();
const embedFlag = params.get("embed") === "1" || params.get("embed") === "true";
export const isEmbedded = embedFlag || window.self !== window.top;

export function applyEmbedOptions() {
  const root = document.documentElement;
  const theme = params.get("theme");
  if (theme === "light" || theme === "dark") root.dataset.theme = theme;
  const accent = params.get("accent");
  if (accent && /^[0-9a-fA-F]{3,8}$/.test(accent)) root.style.setProperty("--accent", `#${accent}`);
  if (isEmbedded) root.dataset.embed = "1";

  if (isEmbedded && window.parent !== window) {
    let last = 0;
    const post = () => {
      const height = document.documentElement.scrollHeight;
      if (height !== last) {
        last = height;
        window.parent.postMessage({ type: "ai-interviewer:height", height }, "*");
      }
    };
    new ResizeObserver(post).observe(document.body);
    post();
  }
}
