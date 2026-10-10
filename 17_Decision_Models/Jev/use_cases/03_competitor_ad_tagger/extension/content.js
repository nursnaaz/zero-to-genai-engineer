// Save each ad you scroll past, tagged by Jev with format, CTA and funnel stage.
const QUESTIONS = {
  format: { type: "choice", instructions: "What format is this ad `copy`?", criteria: {
    problem_solution: "Names a pain, then offers the product as the fix.",
    social_proof: "Leads with a customer result or numbers.",
    educational: "Offers a guide, report or template.",
    demo_offer: "Invites you to see the product.",
    urgency_offer: "Discount, deadline or scarcity." } },
  cta: { type: "choice", instructions: "What is the main call to action in `copy`?", criteria: {
    start_trial: "Sign up now.", book_demo: "Talk to a human.",
    download: "Grab a resource.", watch: "Watch a video.",
    read: "Read something.", none: "No clear action." } },
  funnel_stage: { type: "choice", instructions: "What funnel stage is `copy` aimed at?", criteria: {
    awareness: "Does not know they have the problem.",
    consideration: "Comparing options.",
    conversion: "Ready to act now." } }
};

async function tag(copy) {
  const { jevKey } = await chrome.storage.sync.get("jevKey");
  const res = await fetch("https://api.typesafe.ai/v1/systemone", {
    method: "POST",
    headers: { Authorization: `Bearer ${jevKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({ state: { copy }, model: "jev-latest", questions: QUESTIONS })
  });
  if (!res.ok) return null;
  const a = (await res.json()).answers;
  return { format: a.format.choice, cta: a.cta.choice,
           funnel_stage: a.funnel_stage.choice,
           confidence: Math.min(a.format.confidence, a.cta.confidence, a.funnel_stage.confidence) };
}

const saved = new Set();
async function sweep() {
  for (const card of document.querySelectorAll('[role="article"]')) {
    const copy = (card.innerText || "").trim().slice(0, 600);
    if (copy.length < 40 || saved.has(copy)) continue;
    saved.add(copy);
    const tags = await tag(copy);
    if (!tags) continue;
    const { ads = [] } = await chrome.storage.local.get("ads");
    ads.push({ copy, ...tags, saved_at: new Date().toISOString() });
    await chrome.storage.local.set({ ads });
  }
}
setInterval(sweep, 3000);
sweep();
