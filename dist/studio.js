"use strict";

const $ = (id) => document.getElementById(id);
const paths = {
  home: '<path d="M3 10 12 3l9 7v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/><path d="M9 20v-6h6v6"/>',
  chat: '<path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l1.8-3.4A8.5 8.5 0 1 1 21 11.5Z"/><path d="M8.5 11.5h.1m3.8 0h.1m3.8 0h.1"/>',
  create: '<path d="M12 2l2.2 7.8L22 12l-7.8 2.2L12 22l-2.2-7.8L2 12l7.8-2.2L12 2Z"/>',
  agent: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m7 9 3 3-3 3m6 0h4"/>',
  library: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18m-14 4h4m2 0h4m-10 3h4"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8" cy="9" r="1.4"/><path d="m4 17 5-4 3 2.5 3.5-4L20 16"/>',
  edit: '<path d="M12 5H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7m-2-9 4 4-8 8-5 1 1-5z"/>',
  video: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m10 9 5 3-5 3z"/>',
  voice: '<rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11v1a7 7 0 0 0 14 0v-1m-7 8v3m-3 0h6"/>',
  music: '<path d="M9 18V5l11-2v13M9 8l11-2"/><ellipse cx="6" cy="18" rx="3" ry="2"/><ellipse cx="17" cy="16" rx="3" ry="2"/>',
  settings: '<path d="M4 7h16M4 12h16M4 17h16"/><circle cx="8" cy="7" r="2"/><circle cx="15" cy="12" r="2"/><circle cx="10" cy="17" r="2"/>',
};
const tabs = { home: "ภาพรวม", chat: "สนทนา", create: "สร้าง", agent: "งานอัตโนมัติ", library: "กิจกรรม", settings: "ตั้งค่า" };
const details = {
  flux: ["image", "สร้างภาพจากข้อความ", "A tiny house in a misty forest at sunrise", "768 × 1024"],
  edit: ["edit", "แนบภาพแล้วบอกว่าต้องการแก้ตรงไหน", "Change the jacket to deep blue. Preserve the face and background.", "FLUX.2 Klein Edit"],
};
const state = { tab: Object.hasOwn(tabs, location.hash.slice(1)) ? location.hash.slice(1) : "home", recipe: "flux", info: null, library: "", queue: "", timer: null, reuse: null };
const chat = read("tandemforge.chat", { messages: [], pending: null });
const personaOptions = new Map();
let agentId = read("tandemforge.agent", null);

function read(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
function save(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* app remains usable */ }
}
function element(tag, text, cls) {
  const node = document.createElement(tag);
  if (text != null) node.textContent = text;
  if (cls) node.className = cls;
  return node;
}
function icon(name) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  node.setAttribute("viewBox", "0 0 24 24");
  node.setAttribute("aria-hidden", "true");
  node.innerHTML = paths[name];
  return node;
}
async function api(path, data) {
  const options = data === undefined ? {} : data instanceof Blob ? { method: "POST", body: data } : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
  };
  const response = await fetch("/api/" + path, options);
  const result = await response.json();
  if (!response.ok) {
    if (response.status === 401 && path !== "login") showLogin();
    const error = new Error(localMessage(result.error) || t("เชื่อมต่อแอปไม่สำเร็จ"));
    error.status = response.status;
    throw error;
  }
  return result;
}
function notice(text, error = false) {
  const box = $("notice");
  box.textContent = text;
  box.classList.toggle("error", error);
  box.hidden = !text;
}
function showLogin() {
  clearInterval(state.timer);
  $("shell").hidden = true;
  $("login").hidden = false;
}
function switchTab(tab, scroll = true) {
  if (!(tab in tabs)) return;
  state.tab = tab;
  history.replaceState(null, "", "#" + tab);
  $("top-tab").textContent = t(tabs[tab]);
  Object.keys(tabs).forEach((key) => {
    $(key).hidden = key !== tab;
    if (key === tab) $("nav-" + key).setAttribute("aria-current", "page");
    else $("nav-" + key).removeAttribute("aria-current");
  });
  if (scroll) window.scrollTo(0, 0);
}
function selectRecipe(key) {
  const recipe = state.info.recipes[key];
  state.recipe = key;
  $("recipe-title").textContent = t(recipe.label);
  $("recipe-model").textContent = recipe.model;
  $("recipe-help").textContent = t(details[key][1]);
  $("create-text").placeholder = details[key][2];
  $("recipe-detail").textContent = key === "flux" ? $("image-size").selectedOptions[0].textContent : details[key][3];
  $("prompt-label").textContent = t("คำบรรยาย");
  $("create-upload-wrap").hidden = !recipe.input;
  $("image-size-wrap").hidden = key !== "flux";
  for (const button of $("recipes").children) {
    button.setAttribute("aria-pressed", String(button.dataset.recipe === key));
  }
}
function buildControls() {
  $("nav").replaceChildren();
  for (const [key, title] of Object.entries(tabs)) {
    const button = element("button", null, "nav-button");
    button.id = "nav-" + key;
    button.dataset.tab = key;
    button.append(icon(key), element("span", t(title)));
    $("nav").append(button);
  }
  $("recipes").replaceChildren();
  $("recipe-count").textContent = Object.keys(state.info.recipes).length + t(" เวิร์กโฟลว์");
  for (const [key, recipe] of Object.entries(state.info.recipes)) {
    const button = element("button", null, "recipe");
    button.dataset.recipe = key;
    button.type = "button";
    button.append(icon(details[key][0]), element("strong", t(recipe.label)), element("small", recipe.model));
    $("recipes").append(button);
  }
  for (const id of ["chat-model", "agent-model"]) {
    $(id).replaceChildren();
    for (const [key, label] of Object.entries(state.info.models)) {
      $(id).append(new Option(label, key));
    }
    if (!$(id).options.length) $(id).add(new Option(t("ยังไม่มีโมเดล"), ""));
    $(id).value = state.info.models.qwen9 ? "qwen9" : $(id).options[0].value;
  }
  configureChatTasks();
  describeAgentModel();
  const picker = $("chat-persona");
  const selected = read("tandemforge.persona", "");
  picker.replaceChildren(new Option(t("ไม่ใช้ Persona"), ""));
  personaOptions.clear();
  for (const [category, entries] of Object.entries(state.info.personas || {})) {
    const group = element("optgroup");
    group.label = t(category);
    for (const entry of entries) {
      personaOptions.set(entry.id, entry);
      group.append(new Option(language === "en" ? entry.en_label : entry.label, entry.id));
    }
    picker.append(group);
  }
  picker.value = personaOptions.has(selected) ? selected : "";
  describePersona();
}
function describePersona() {
  const entry = personaOptions.get($("chat-persona").value);
  $("persona-description").textContent = (language === "en" ? entry?.en_description : entry?.description) || t("เลือกบทบาทเพื่อกำหนดรูปแบบคำตอบของข้อความถัดไป");
  const hints = $("persona-models");
  hints.replaceChildren();
  hints.hidden = !entry?.recommended_models?.length;
  if (hints.hidden) return;
  hints.append(element("span", t("โมเดลแนะนำ"), "hint"));
  for (const { id, edition } of entry.recommended_models) {
    if (!state.info.models[id]) continue;
    const pick = element("button", state.info.models[id] + " · " + edition, "text-button");
    pick.type = "button";
    pick.addEventListener("click", () => {
      selectChatModel(id);
    });
    hints.append(pick);
  }
}
function connection(info) {
  const box = $("connection");
  box.replaceChildren(element("span", null, "dot" + (info.comfy.online ? "" : " muted")),
    element("span", info.comfy.online ? t("ComfyUI ออนไลน์") : t("ComfyUI ออฟไลน์")));
  if (info.commit != null) box.title = t("ยอดจองหน่วยความจำ ") + info.commit + "%";
  const status = $("home-status");
  status.replaceChildren(
    element("span", t(info.chat_ready ? "เอนจินแชทพร้อม" : "รอตั้งค่าเอนจินแชท"), "status-chip"),
    element("span", t(info.comfy.online ? "ComfyUI ออนไลน์" : "ComfyUI ออฟไลน์"), "status-chip"),
  );
}

function gib(bytes) {
  return new Intl.NumberFormat(language, { maximumFractionDigits: 1 }).format(bytes / 2 ** 30) + " GiB";
}

async function showModelGuide() {
  const button = $("model-guide-scan");
  const results = $("model-guide-results");
  button.disabled = true;
  results.hidden = false;
  results.replaceChildren(element("p", t("กำลังตรวจสเปกบนเครื่อง…"), "hint"));
  try {
    const data = await api("model-guide");
    const spec = element("div", null, "guide-spec");
    spec.append(element("span", "RAM " + gib(data.ram) + " · " + t("ว่าง") + " " + gib(data.free_ram), "status-chip"));
    spec.append(element("span", data.gpu ? data.gpu.name + " · " + gib(data.gpu.dedicated) + " VRAM" :
      t("ไม่พบข้อมูล VRAM แยก"), "status-chip"));
    if (data.free_disk != null) spec.append(element("span", t("พื้นที่ว่างบนไดรฟ์โมเดล") + " " + gib(data.free_disk), "status-chip"));
    results.replaceChildren(spec, element("p", t("ประเมินจากสเปกที่ตรวจได้ การรองรับ GPU ขึ้นกับเอนจินและไดรเวอร์"), "hint"));
    if (data.low_free_ram) results.append(element("p", t("ตอนนี้ RAM ว่างน้อย ให้รอคิวหนักจบก่อนโหลดโมเดล"), "error"));
    if (!data.options.length) {
      results.append(element("p", t("ยังไม่มีรุ่นที่แนะนำตามสเปกและ RAM ว่างตอนนี้ ลองปิดโปรแกรมหนักแล้วตรวจใหม่"), "empty"));
      return;
    }
    const grid = element("div", null, "guide-grid");
    const tiers = { Compact: "ประหยัดที่สุด", Light: "ขนาดเล็ก", Balanced: "สมดุล", "Higher capacity": "รุ่นใหญ่ขึ้น" };
    const candidates = [...data.options].sort((a, b) => Number(b.id === data.recommended) - Number(a.id === data.recommended));
    for (const model of candidates) {
      const card = element("article", null, "guide-option");
      const badge = model.id === data.recommended ? t("แนะนำให้เริ่ม") :
        language === "en" ? model.tier : tiers[model.tier];
      card.append(element("p", badge, "eyebrow"), element("strong", model.name));
      const fit = model.mode === "gpu" ? "GPU · VRAM ≥ " + model.minimum_vram_gib + " GiB" :
        t("ใช้ CPU · ตั้ง GPU layers เป็น 0");
      const numbers = new Intl.NumberFormat(language);
      card.append(element("p", fit + " · RAM ≥ " + numbers.format(model.minimum_ram_gib) +
        " GiB · Context " + numbers.format(model.context), "hint"));
      card.append(element("p", t("ขนาดไฟล์") + " " + gib(model.bytes) + " · Apache 2.0", "hint"));
      if (model.installed) {
        card.append(element("span", t("ติดตั้งไฟล์แล้ว"), "guide-ready"));
        if (state.info.chat_ready && state.info.models[model.chat_id]) {
          const start = element("button", t("ใช้ในห้องสนทนา ↗"), "text-button");
          start.type = "button";
          start.addEventListener("click", () => {
            selectChatModel(model.chat_id);
            switchTab("chat");
            $("chat-text").focus();
          });
          card.append(start);
        }
      }
      else if (!model.disk_ok) card.append(element("span", t("ตรวจพื้นที่ว่างก่อนดาวน์โหลด"), "error"));
      else {
        const link = element("a", t("ดูไฟล์ต้นทาง ↗"), "text-button");
        link.href = model.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        card.append(link);
      }
      grid.append(card);
    }
    results.append(grid, element("p", t("วางไฟล์ GGUF ในโฟลเดอร์โมเดลที่ตั้งไว้ แล้วเปิด TandemForge ใหม่"), "hint"));
  } catch (error) {
    results.replaceChildren(element("p", error.message, "error"));
  } finally {
    button.disabled = false;
  }
}
function attachReuse(media, recipe) {
  state.reuse = media.path;
  $("create-image").value = "";
  $("reuse-name").textContent = media.name;
  $("reuse").hidden = false;
  selectRecipe(recipe);
  switchTab("create");
  $("create-form").scrollIntoView({ block: "start" });
}
function clearReuse() {
  state.reuse = null;
  $("reuse").hidden = true;
}
function describeJob(job) {
  return localMessage(job.phase) || ({ done: t("เสร็จแล้ว"), error: t("มีข้อผิดพลาด"), cancelled: t("ยกเลิกแล้ว") })[job.state] || t("กำลังทำงาน");
}
function mediaUrl(path) {
  return "/media/" + path.split("/").map(encodeURIComponent).join("/");
}
function mediaItem(media) {
  const card = element("div", null, "media-item");
  const view = element(media.kind === "image" ? "img" : media.kind);
  view.src = mediaUrl(media.path);
  if (media.kind === "image") {
    view.loading = "lazy";
    view.alt = t("ผลลัพธ์ ") + media.name;
  } else {
    view.preload = "metadata";
    view.controls = true;
    if (media.kind === "video") view.playsInline = true;
  }
  const actions = element("div", null, "media-actions");
  const download = element("a", t("ดาวน์โหลด ↓"), "secondary");
  download.href = view.src;
  download.download = media.name;
  actions.append(download);
  if (media.kind === "image") {
    for (const [label, key] of [[t("ใช้แก้ภาพ"), "edit"]]) {
      const button = element("button", label, "text-button");
      button.addEventListener("click", () => attachReuse(media, key));
      actions.append(button);
    }
  }
  card.append(view, actions);
  return card;
}
function isFinished(job) {
  return ["done", "error", "cancelled"].includes(job.state);
}
function confirmRemoval(message, label) {
  return new Promise((resolve) => {
    const dialog = element("dialog", null, "history-confirm");
    dialog.setAttribute("aria-label", message);
    const form = element("form");
    form.method = "dialog";
    const cancel = element("button", t("ยกเลิก"), "secondary");
    cancel.value = "cancel";
    cancel.autofocus = true;
    const confirm = element("button", label, "primary danger");
    confirm.value = "remove";
    form.append(cancel, confirm);
    dialog.append(element("p", message), form);
    dialog.addEventListener("close", () => {
      const approved = dialog.returnValue === "remove";
      dialog.remove();
      resolve(approved);
    }, { once: true });
    document.body.append(dialog);
    dialog.showModal();
  });
}

function deleteButton(remove, label = t("ลบประวัติ")) {
  const button = element("button", label, "text-button delete-history");
  button.type = "button";
  button.addEventListener("click", async () => {
    if (!await confirmRemoval(t("ลบประวัติรายการนี้ออกจาก TandemForge?"), label)) return;
    button.disabled = true;
    try {
      await remove();
      notice(t("ลบประวัติรายการนี้แล้ว"));
    } catch (error) {
      notice(error.message, true);
    } finally {
      button.disabled = false;
    }
  });
  return button;
}
function refreshJobs(jobs) {
  const recent = [...jobs.filter((job) => ["running", "queued"].includes(job.state)),
                  ...jobs.filter((job) => !["running", "queued"].includes(job.state))].slice(0, 4);
  const key = JSON.stringify(recent.map((job) => [job.id, job.state, job.phase]));
  if (state.queue !== key) {
    state.queue = key;
    $("queue-summary").replaceChildren();
    if (!recent.length) {
      const empty = element("div", null, "empty");
      empty.append(element("strong", t("คิวว่าง")), element("span", t("งานที่ส่งจะปรากฏที่นี่")));
      $("queue-summary").append(empty);
    }
    recent.forEach((job) => {
      const row = element("div", null, "queue-item");
      row.append(element("strong", t(job.label)), element("span", describeJob(job), "badge " + job.state));
      $("queue-summary").append(row);
    });
    $("home-queue").replaceChildren(...[...$("queue-summary").children].map((item) => item.cloneNode(true)));
  }
  const stamp = JSON.stringify(jobs);
  if (state.library === stamp || state.tab !== "library") return;
  state.library = stamp;
  $("library-list").replaceChildren();
  if (!jobs.length) $("library-list").append(element("p", t("ยังไม่มีงานในแอป ลองส่งงานจากแท็บสร้าง"), "empty"));
  for (const job of jobs) {
    const card = element("article", null, "panel job");
    const header = element("div", null, "section-head");
    header.append(element("h2", t(job.label)), element("span", describeJob(job), "badge " + job.state));
    card.append(header, element("p", job.text, "job-text"));
    if (job.error) card.append(element("p", localMessage(job.error), "error"));
    if (job.state === "queued") {
      const button = element("button", t("ยกเลิกงาน"), "text-button");
      button.addEventListener("click", async () => {
        try { await api("cancel", { id: job.id }); await pollJobs(); }
        catch (error) { notice(error.message, true); }
      });
      card.append(button);
    }
    if (job.result?.media) {
      const grid = element("div", null, "media-grid");
      grid.append(...job.result.media.map(mediaItem));
      card.append(grid);
    }
    if (isFinished(job)) {
      card.append(deleteButton(async () => {
        await api("delete-history", { id: job.id });
        card.remove();
        await pollJobs();
      }));
    }
    $("library-list").append(card);
  }
}
async function pollJobs() {
  const response = await api("jobs");
  refreshJobs(response.jobs);
}
function configureChatTasks() {
  const picker = $("chat-task");
  const tasks = Object.entries(state.info.chat_tasks || {});
  picker.replaceChildren(new Option(t("กำหนดเอง"), ""));
  for (const [id, task] of tasks) picker.add(new Option(t(task.label), id));
  $("chat-task-bar").hidden = !tasks.length;
  describeChatTask();
}

function describeChatTask() {
  const task = state.info.chat_tasks?.[$("chat-task").value];
  $("chat-task-help").textContent = task ? t(task.description) :
    t("เลือกโหมดเพื่อใช้ค่ากับข้อความที่ส่งจากหน้านี้ ค่าที่บันทึกไว้ยังใช้งานได้ในโหมดกำหนดเอง");
}

function selectChatModel(model, task = "") {
  if (state.info.models[model]) $("chat-model").value = model;
  $("chat-task").value = task;
  describeChatTask();
  preferencesUi.refreshVision();
}

function describeAgentModel() {
  const model = $("agent-model").value;
  const note = model === "gemma12" ? t("Gemma 12B เหมาะกับ Agent ที่เรียกเป็นครั้ง ๆ และโหลดเร็วกว่า 35B ในชุดทดสอบของเรา") :
    model === "qwen35" ? t("35B A3B เหมาะกับงานต่อเนื่องเมื่อโมเดลโหลดแล้ว และใช้ RAM มากกว่า Gemma 12B") : "";
  $("agent-model-help").textContent = note;
  $("agent-model-help").hidden = !note;
}

function chatView(phase = "", scroll = true) {
  const messages = $("messages");
  const position = messages.scrollTop;
  messages.replaceChildren();
  if (!chat.messages.length) messages.append(element("p", t("เริ่มแชทได้เลย เช่น ให้ช่วยร่างเรื่องหรืออธิบายโค้ด"), "empty"));
  for (let index = 0; index < chat.messages.length; index++) {
    const first = chat.messages[index];
    const next = chat.messages[index + 1];
    const pair = first.role === "user" && next?.role === "assistant";
    const turn = pair ? [first, chat.messages[++index]] : [first];
    const group = element("div", null, "chat-turn");
    for (const msg of turn) {
      const bubble = element("div", msg.content, "bubble " + msg.role);
      if (msg.reasoning) {
        const thoughts = element("details", null, "reasoning");
        thoughts.append(element("summary", t("ข้อความการคิด")), element("p", msg.reasoning));
        bubble.prepend(thoughts);
      }
      const persona = personaOptions.get(msg.persona);
      if (msg.role === "assistant" && msg.model) bubble.prepend(element("span", msg.model, "persona-label"));
      if (msg.role === "assistant" && persona) bubble.prepend(element("span", (language === "en" ? persona.en_label : persona.label), "persona-label"));
      group.append(bubble);
    }
    const jobId = first.jobId || (pair ? next.jobId : null);
    if (pair || !chat.pending || index < chat.messages.length - 1) {
      const actions = element("div", null, "chat-reply-actions");
      if (pair && !next.failed && navigator.clipboard?.writeText) {
        const copy = element("button", t("คัดลอกคำตอบ"), "text-button");
        copy.type = "button";
        copy.addEventListener("click", async () => {
          try {
            await navigator.clipboard.writeText(next.content);
            notice(t("คัดลอกแล้ว"));
          } catch {
            notice(t("คัดลอกไม่ได้ในเบราว์เซอร์นี้"), true);
          }
        });
        actions.append(copy);
      }
      actions.append(deleteButton(async () => {
        if (jobId) await api("delete-history", { id: jobId });
        chat.messages = chat.messages.filter((msg) => !turn.includes(msg) && (!jobId || msg.jobId !== jobId));
        save("tandemforge.chat", chat);
        chatView(chat.phase, false);
      }, pair ? t("ลบข้อความคู่นี้") : t("ลบข้อความนี้")));
      group.append(actions);
    }
    messages.append(group);
  }
  if (chat.pending) messages.append(element("div", localMessage(phase) || t("กำลังรอคำตอบ…"), "bubble"));
  $("chat-form").querySelector("button[type=submit]").disabled = Boolean(chat.pending) || !$("chat-model").value;
  $("new-chat").disabled = Boolean(chat.pending);
  messages.scrollTop = scroll ? messages.scrollHeight : position;
}
async function pollChat() {
  if (!chat.pending) return;
  const pending = chat.pending;
  let job;
  try {
    job = await api("jobs/" + pending);
  } catch (error) {
    if (error.status !== 404) throw error;
    if (chat.pending !== pending) return;
    chat.messages = chat.messages.filter((msg) => msg.jobId !== pending);
    chat.pending = null;
    save("tandemforge.chat", chat);
    chatView();
    return;
  }
  if (chat.pending !== pending) return;
  if (isFinished(job)) {
    const user = chat.messages.at(-1);
    if (user?.role === "user") user.jobId = job.id;
    chat.messages.push({ role: "assistant", content: job.result?.text || (t("ข้อผิดพลาด · ") + localMessage(job.error)),
                         reasoning: job.result?.reasoning, jobId: job.id, persona: user?.persona,
                         model: user?.model, failed: job.state !== "done" });
    chat.messages = chat.messages.slice(-80);
    chat.pending = null;
    save("tandemforge.chat", chat);
    chatView();
  } else if (job.phase !== chat.phase) {
    chat.phase = job.phase;
    chatView(job.phase);
  }
}
let shownAgent = "";
let shownAgentHistory = "";
function selectAgent(id) {
  agentId = id;
  save("tandemforge.agent", agentId);
  if (!id) {
    shownAgent = "";
    $("agent-result").hidden = true;
    $("agent-result").replaceChildren();
    $("agent-form").querySelector("button[type=submit]").disabled = !preferencesUi.effective().agent_enabled;
  }
}
async function pollAgentHistory() {
  if (state.tab !== "agent" || !$("agent-history").open) return;
  const { jobs } = await api("jobs?kind=agent");
  const stamp = JSON.stringify([agentId, jobs.map((job) => [job.id, job.state, job.phase])]);
  if (stamp === shownAgentHistory) return;
  shownAgentHistory = stamp;
  const list = $("agent-history-list");
  list.replaceChildren();
  if (!jobs.length) list.append(element("p", t("ยังไม่มีประวัติ Agent"), "empty"));
  for (const job of jobs) {
    const row = element("article", null, "agent-history-row");
    const open = element("button", job.text, "text-button agent-history-open");
    open.type = "button";
    if (job.id === agentId) open.setAttribute("aria-current", "true");
    open.addEventListener("click", async () => {
      selectAgent(job.id);
      try {
        await pollAgent();
        await pollAgentHistory();
        if (agentId === job.id) $("agent-result").scrollIntoView({ block: "start" });
      } catch (error) { notice(error.message, true); }
    });
    row.append(open, element("span", describeJob(job), "badge " + job.state));
    if (isFinished(job)) {
      row.append(deleteButton(async () => {
        await api("delete-history", { id: job.id });
        if (agentId === job.id) selectAgent(null);
        row.remove();
        await pollAgentHistory();
      }));
    }
    list.append(row);
  }
}
async function pollAgent() {
  if (!agentId) return;
  const selected = agentId;
  let job;
  try {
    job = await api("jobs/" + selected);
  } catch (error) {
    if (error.status !== 404) throw error;
    if (agentId === selected) selectAgent(null);
    return;
  }
  if (agentId !== selected) return;
  const access = preferencesUi.effective();
  const permissions = { status: access.agent_status, list: access.agent_read, read: access.agent_read,
                        write: access.agent_write, create: access.agent_create };
  const allowed = access.agent_enabled && permissions[job.result?.action];
  const stamp = JSON.stringify([job.id, job.state, job.phase, job.result, job.error, allowed, access.agent_enabled]);
  if (stamp === shownAgent) return;
  shownAgent = stamp;
  const panel = $("agent-result");
  panel.hidden = false;
  panel.replaceChildren(element("h2", job.result ? t("คำสั่งที่เสนอ") : t("สถานะ Agent")));
  const remove = isFinished(job) ? deleteButton(async () => {
    await api("delete-history", { id: job.id });
    if (agentId === job.id) selectAgent(null);
    await pollAgentHistory();
  }) : null;
  if (!job.result) {
    panel.append(element("p", localMessage(job.error) || describeJob(job), job.error ? "error" : "hint"));
    if (remove) panel.append(remove);
    $("agent-form").querySelector("button[type=submit]").disabled =
      !preferencesUi.effective().agent_enabled || job.state === "queued" || job.state === "running";
    return;
  }
  $("agent-form").querySelector("button[type=submit]").disabled = !preferencesUi.effective().agent_enabled;
  const plan = job.result;
  panel.append(element("p", t(plan.label) + (plan.file ? " · " + plan.file : "") +
    (plan.recipe ? " · " + t(state.info.recipes[plan.recipe].label) : "")));
  if (plan.text) panel.append(element("pre", plan.text));
  if (job.approved) {
    const result = plan.action === "read" ? plan.execution?.text : localMessage(plan.execution?.text);
    panel.append(element("pre", result || t("ส่งงานเข้าคิวแล้ว")));
    if (remove) panel.append(remove);
    return;
  }
  const button = element("button", t("อนุมัติให้ทำงาน"), "primary");
  button.disabled = !allowed;
  if (!allowed) panel.append(element("p", t("สิทธิ์สำหรับคำสั่งนี้ปิดอยู่ในหน้าตั้งค่า"), "hint"));
  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      await api("approve", { id: job.id });
      await pollAgent();
      await pollJobs();
    } catch (error) {
      button.disabled = false;
      panel.append(element("p", error.message, "error"));
    }
  });
  panel.append(button);
  if (remove) panel.append(remove);
}
async function showApp() {
  state.info = await api("info");
  buildControls();
  await preferencesUi.load(false, true);
  selectRecipe(state.recipe);
  connection(state.info);
  switchTab(state.tab, false);
  $("login").hidden = true;
  $("shell").hidden = false;
  chatView();
  clearInterval(state.timer);
  const tick = async () => {
    if (state.polling) return;
    state.polling = true;
    try { await Promise.all([pollJobs(), pollChat(), pollAgent(), pollAgentHistory(), preferencesUi.poll()]); }
    catch (error) { notice(error.message, true); }
    finally { state.polling = false; }
  };
  let rounds = 0;
  state.timer = setInterval(() => {
    tick();
    if (++rounds % 5 === 0) api("info").then(connection).catch(() => {});
  }, 2400);
  await tick();
}

function form(id, handle) {
  $(id).addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.currentTarget.querySelector("button[type=submit]");
    button.disabled = true;
    notice("");
    try { await handle(); }
    catch (error) { notice(error.message, true); }
    finally {
      if (id !== "chat-form" || !chat.pending) button.disabled = false;
    }
  });
}
async function upload(id) {
  const file = $(id).files[0];
  if (!file) return null;
  if (file.size > 16 * 1024 * 1024) throw new Error(t("ไฟล์ภาพต้องไม่เกิน 16 MB"));
  return (await api("upload", file)).image;
}
form("login-form", async () => {
  $("login-error").textContent = "";
  try {
    await api("login", { code: $("access-code").value });
    $("access-code").value = "";
    await showApp();
  } catch (error) { $("login-error").textContent = error.message; }
});
form("create-form", async () => {
  const recipe = state.recipe;
  const payload = { recipe, text: $("create-text").value };
  if (recipe === "flux") payload.size = $("image-size").value;
  if (state.info.recipes[recipe].input) {
    payload.image = await upload("create-image");
    payload.source = payload.image ? null : state.reuse;
    if (!payload.image && !payload.source) throw new Error(t("เลือกภาพต้นฉบับก่อนส่งงาน"));
  }
  await api("create", payload);
  notice(t("ส่งงานเข้าคิวแล้ว"));
  await pollJobs();
});
form("chat-form", async () => {
  const text = $("chat-text").value;
  const model = $("chat-model").value;
  const task = $("chat-task").value;
  const persona = $("chat-persona").value;
  const image = await upload("chat-image");
  const count = preferencesUi.effective(model).history_messages;
  const failures = new Set(chat.messages.filter((entry) => entry.failed).map((entry) => entry.jobId));
  const history = count ? chat.messages.filter((entry) => !failures.has(entry.jobId)).slice(-count)
    .map(({ role, content }) => ({ role, content: content.slice(0, 1800) })) : [];
  const job = await api("chat", { model, task, persona, text, image, history });
  chat.messages.push({ role: "user", content: text, jobId: job.id, persona, model: state.info.models[model] });
  chat.pending = job.id;
  save("tandemforge.chat", chat);
  $("chat-text").value = "";
  $("chat-image").value = "";
  chatView();
});
form("agent-form", async () => {
  const job = await api("agent", { model: $("agent-model").value, text: $("agent-text").value });
  selectAgent(job.id);
  await pollAgent();
});
$("clear-reuse").addEventListener("click", clearReuse);
$("agent-history").addEventListener("toggle", () => {
  pollAgentHistory().catch((error) => notice(error.message, true));
});
window.addEventListener("storage", (event) => {
  if (event.key !== "tandemforge.chat") return;
  const saved = read("tandemforge.chat", { messages: [], pending: null });
  Object.assign(chat, saved);
  chatView(chat.phase, false);
});
$("create-image").addEventListener("change", () => { if ($("create-image").files.length) clearReuse(); });
$("image-size").addEventListener("change", () => selectRecipe(state.recipe));
$("new-chat").addEventListener("click", () => {
  if (chat.pending) return;
  chat.messages = [];
  save("tandemforge.chat", chat);
  selectChatModel(preferencesUi.effective().chat_model);
  chatView();
});
$("chat-task").addEventListener("change", (event) => {
  const task = event.target.value;
  selectChatModel(state.info.chat_tasks?.[task]?.model || preferencesUi.effective().chat_model, task);
});
$("chat-model").addEventListener("change", () => selectChatModel($("chat-model").value));
$("agent-model").addEventListener("change", describeAgentModel);
$("chat-persona").addEventListener("change", (event) => {
  save("tandemforge.persona", event.target.value);
  describePersona();
});
$("chat-text").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing && preferencesUi.effective().enter_to_send) {
    event.preventDefault();
    if (!chat.pending && !$("chat-form").querySelector("button[type=submit]").disabled) $("chat-form").requestSubmit();
  }
});
document.addEventListener("click", (event) => {
  const recipe = event.target.closest("[data-recipe]");
  if (recipe) {
    selectRecipe(recipe.dataset.recipe);
    if (matchMedia("(max-width: 690px)").matches) $("create-form").scrollIntoView({ block: "start" });
  }
  const tab = event.target.closest("[data-tab]");
  if (tab) {
    switchTab(tab.dataset.tab);
    if (state.tab === "library") pollJobs().catch((error) => notice(error.message, true));
    if (state.tab === "agent") pollAgentHistory().catch((error) => notice(error.message, true));
  }
});
initLanguage();
preferencesUi.connect();
$("model-guide-scan").addEventListener("click", showModelGuide);
api("session").then((session) => session.authenticated ? showApp() : showLogin()).catch((error) => {
  showLogin();
  $("login-error").textContent = error.message;
});
if ("serviceWorker" in navigator && window.isSecureContext) navigator.serviceWorker.register("/sw.js").catch(() => {});
