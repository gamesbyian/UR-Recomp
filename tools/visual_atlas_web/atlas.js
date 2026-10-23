"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  const labels = {captured:"Real Windows SDL capture",capture_pending:"Capture pending",capture_failed:"Capture failed",planned:"COMING SOON"};
  const modes = {modern:"Modern",authentic:"Authentic", "original-4x":"Original 4×",remastered:"Remastered",widescreen:"Widescreen",future:"Planned"};
  const escapeHTML = (text) => String(text).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  let entries = [], displayed = [], selected = null, pressX = null;
  const url = (path) => "./" + path;
  const artwork = (entry) => url("assets/" + encodeURIComponent(entry.art) + ".png");
  const img = (entry) => entry.status === "captured" ? url(entry.image) : artwork(entry);
  const title = (entry) => modes[entry.mode] || entry.mode;
  const statusLabel = (entry) => labels[entry.status] || entry.status;
  const isHosted = () => /^https?:$/.test(location.protocol);
  const referenceUrl = (entry) => isHosted() ? location.href.split("#")[0] + "#" + entry.id : "";
  const agentReference = (entry) => {
    const detail = entry.evidence ? "Real Windows SDL capture; source " + entry.evidence.source_sha + "; EXE SHA256 " + entry.evidence.exe_sha256 + "; PNG SHA256 " + entry.evidence.png_sha256 + "." : "No Windows screenshot admitted; " + statusLabel(entry).toLowerCase() + ", conceptual graph-paper plate only.";
    return "Inspect " + entry.id + ": " + entry.title + ". " + title(entry) + " / " + entry.family + " / " + entry.state + " / " + entry.display + ". " + detail + (referenceUrl(entry) ? " Atlas: " + referenceUrl(entry) : " Atlas ID: " + entry.id);
  };
  async function copy(value, element) {
    let done = false;
    try {
      if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(value); done = true; }
    } catch (_) { /* fall back to selection */ }
    if (!done) {
      const textarea = document.createElement("textarea");
      textarea.value = value; textarea.setAttribute("readonly", "");
      textarea.style.cssText = "position:fixed;left:-9999px;top:0";
      document.body.append(textarea); textarea.select();
      try { done = document.execCommand("copy"); } catch (_) { /* show text */ }
      textarea.remove();
    }
    if (!done) {
      window.prompt("Select and copy this reference:", value);
      return;
    }
    const target = element || $("copy-status");
    if (target) {
      const original = target.tagName === "BUTTON" ? target.textContent : "";
      target.textContent = target.tagName === "BUTTON" ? "Copied ✓" : "Reference copied";
      if (target.tagName === "BUTTON") setTimeout(() => { target.textContent = original; }, 1200);
    }
  }
  function option(select, value, label) {
    const item = document.createElement("option"); item.value = value; item.textContent = label; select.append(item);
  }
  function filtered() {
    const query = $("search").value.trim().toLowerCase(), mode = $("mode").value;
    const family = $("family").value, status = $("status").value;
    return entries.filter(e =>
      (!mode || e.mode === mode) && (!family || e.family === family) &&
      (!status || e.status === status) &&
      (!query || [e.id,e.title,e.mode,e.family,e.state,e.display].join(" ").toLowerCase().includes(query)));
  }
  function render() {
    displayed = filtered();
    const gallery = $("gallery");
    gallery.replaceChildren();
    if (!displayed.length) { gallery.innerHTML = '<p class="loading">No entries match those filters.</p>'; return; }
    const fragment = document.createDocumentFragment();
    for (const e of displayed) {
      const card = document.createElement("article");
      card.className = "tile"; card.dataset.status = e.status;
      card.innerHTML = '<button class="preview" type="button" aria-label="Inspect ' + escapeHTML(e.title) + '"><img loading="lazy" alt="' +
        escapeHTML(e.status === "captured" ? "Native Windows SDL screenshot: " + e.title : "Original promotional graph-paper plate, not a screenshot: " + e.title) +
        '" src="' + escapeHTML(img(e)) + '"><span class="overlay">' + escapeHTML(statusLabel(e)) + '</span></button>' +
        '<div class="tile-description"><span class="eyebrow">' + escapeHTML(title(e)) + '</span><h2>' + escapeHTML(e.title) + '</h2>' +
        '<p class="tile-sub">' + escapeHTML(e.family) + ' · ' + escapeHTML(e.display) + '</p><div class="tile-foot"><span class="refid">' +
        escapeHTML(e.id) + '</span><button class="copy-small" type="button" aria-label="Copy agent reference for ' + escapeHTML(e.id) + '">Copy ref</button></div></div>';
      card.querySelector(".preview").addEventListener("click", () => open(e));
      card.querySelector(".copy-small").addEventListener("click", ev => copy(agentReference(e), ev.currentTarget));
      fragment.append(card);
    }
    gallery.append(fragment);
  }
  function open(entry, setHash = true) {
    selected = entry;
    $("copy-status").textContent = "";
    $("detail-id").textContent = entry.id + "  /  " + statusLabel(entry);
    $("detail-title").textContent = entry.title;
    $("detail-meta").textContent = [title(entry), entry.family, entry.state, entry.display].join(" • ");
    $("detail-provenance").textContent = entry.status === "captured" ?
      "Observed final SDL drawable from native Windows. Semantic scripted input, not a physical-display or final-art acceptance." :
      "COMING SOON / capture unavailable. Background is an authentic editorial plate from the existing graph-paper promotional set; it is not a simulated Windows screen.";
    $("detail-evidence").textContent = entry.evidence ? JSON.stringify(entry.evidence, null, 2) :
      "No authentic Windows capture and receipt associated with this entry.";
    $("zoom").disabled = entry.status !== "captured";
    $("zoom").textContent = "1:1 pixels";
    $("image-stage").classList.remove("native");
    $("image-stage").innerHTML = entry.status === "captured"
      ? '<img alt="' + escapeHTML(entry.title) + '" src="' + escapeHTML(img(entry)) + '">'
      : '<div class="placeholder"><img alt="Authentic graph-paper promo illustration" src="' +
        escapeHTML(img(entry)) + '"><strong>' + escapeHTML(statusLabel(entry)) + '</strong></div>';
    if (!$("detail").open) $("detail").showModal();
    if (setHash) history.replaceState(null, "", "#" + entry.id);
  }
  function navigate(delta) {
    const index = displayed.findIndex(e => e.id === selected?.id);
    if (index < 0 || displayed.length < 2) return;
    open(displayed[(index + delta + displayed.length) % displayed.length]);
  }
  function close() {
    $("detail").close();
    selected = null;
    if (location.hash.startsWith("#URV-")) history.replaceState(null, "", location.pathname + location.search);
  }
  async function init() {
    try {
      const response = await fetch("./atlas.json", {cache:"no-cache"});
      if (!response.ok) throw new Error("atlas.json HTTP " + response.status);
      const payload = await response.json();
      if (payload.schema_version !== 1 || !Array.isArray(payload.entries)) throw new Error("Unrecognized atlas inventory");
      entries = payload.entries;
      for (const mode of [...new Set(entries.map(e => e.mode))].sort()) option($("mode"), mode, modes[mode] || mode);
      for (const family of [...new Set(entries.map(e => e.family))].sort()) option($("family"), family, family);
      const real = entries.filter(e => e.status === "captured").length;
      $("summary").textContent = entries.length + " reference plates · " + real + " source-bound Windows captures";
      for (const id of ["search","mode","family","status"]) $(id).addEventListener("input", render);
      render();
      const deepLink = entries.find(e => "#" + e.id === location.hash);
      if (deepLink) open(deepLink, false);
    } catch (error) {
      $("summary").textContent = "Inventory unavailable";
      $("gallery").textContent = "Atlas manifest could not be loaded: " + error.message + ". Serve the generated folder over HTTP, rather than opening index.html directly as a file.";
    }
  }
  $("close").addEventListener("click", close);
  $("detail").addEventListener("cancel", () => {
    selected = null;
    if (location.hash.startsWith("#URV-")) history.replaceState(null, "", location.pathname + location.search);
  });
  $("copy-ref").addEventListener("click", () => selected && copy(agentReference(selected)));
  $("copy-link").addEventListener("click", () => selected && copy(referenceUrl(selected) || selected.id));
  $("zoom").addEventListener("click", () => {
    const on = $("image-stage").classList.toggle("native");
    $("zoom").textContent = on ? "Fit image" : "1:1 pixels";
  });
  $("prev").addEventListener("click", () => navigate(-1));
  $("next").addEventListener("click", () => navigate(1));
  $("image-stage").addEventListener("touchstart", ev => { pressX = ev.touches[0]?.clientX ?? null; }, {passive:true});
  $("image-stage").addEventListener("touchend", ev => {
    if (pressX == null) return;
    const delta = (ev.changedTouches[0]?.clientX ?? pressX) - pressX;
    pressX = null;
    if (!$("image-stage").classList.contains("native") && Math.abs(delta) > 75) navigate(delta > 0 ? -1 : 1);
  }, {passive:true});
  document.addEventListener("keydown", ev => {
    if (!$("detail").open) return;
    if (ev.key === "ArrowRight") navigate(1);
    if (ev.key === "ArrowLeft") navigate(-1);
  });
  window.addEventListener("hashchange", () => {
    const found = entries.find(e => "#" + e.id === location.hash);
    if (found) open(found, false);
  });
  init();
})();
