// Fold away AI slop as posts load. One Jev noul per post, cached by text hash.
const FOLD_AT = 0.80;
const seen = new WeakSet();

async function jevIsSlop(text) {
  const { jevKey } = await chrome.storage.sync.get("jevKey");
  if (!jevKey) return null;

  const cacheKey = "slop:" + text.slice(0, 180);
  const cached = (await chrome.storage.local.get(cacheKey))[cacheKey];
  if (cached !== undefined) return cached;

  const res = await fetch("https://api.typesafe.ai/v1/systemone", {
    method: "POST",
    headers: { Authorization: `Bearer ${jevKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      state: { post: text },
      model: "jev-latest",
      questions: {
        slop: {
          type: "noul",
          instructions: "Is this `post` low-effort AI-generated engagement bait?",
          criteria: {
            true: "Generic hype, emoji spam, listicle padding, hollow motivational phrasing.",
            false: "A specific first-hand observation, number or incident."
          }
        }
      }
    })
  });
  if (!res.ok) return null;
  const p = (await res.json()).answers.slop.noul;
  await chrome.storage.local.set({ [cacheKey]: p });
  return p;
}

function fold(article, p) {
  article.classList.add("jev-folded");
  const bar = document.createElement("div");
  bar.className = "jev-bar";
  bar.textContent = `Folded by Jev — ${Math.round(p * 100)}% likely AI slop`;
  const btn = document.createElement("button");
  btn.textContent = "Show anyway";
  btn.onclick = () => { article.classList.remove("jev-folded"); bar.remove(); };
  bar.appendChild(btn);
  article.parentElement.insertBefore(bar, article);
}

async function check(article) {
  if (seen.has(article)) return;
  seen.add(article);
  const text = (article.innerText || "").trim();
  if (text.length < 60) return;
  const p = await jevIsSlop(text);
  if (p !== null && p >= FOLD_AT) fold(article, p);
}

// Feeds are infinite, so watch for new posts rather than scanning once.
new MutationObserver(() =>
  document.querySelectorAll("article").forEach(check)
).observe(document.body, { childList: true, subtree: true });
document.querySelectorAll("article").forEach(check);
