"use strict";

const preferencesUi = (() => {
  let current;
  let scope = "global";
  let testId;
  let testedScope;
  const drafts = new Map();

  function effective(model = "global") {
    return { ...current?.defaults, ...current?.global, ...current?.models[model] };
  }

  function apply(previous) {
    const values = effective();
    document.documentElement.dataset.theme = values.theme;
    if (state.info.models[values.chat_model] && (!previous || previous.chat_model !== values.chat_model)) selectChatModel(values.chat_model);
    if (state.info.models[values.agent_model] && (!previous || previous.agent_model !== values.agent_model)) $("agent-model").value = values.agent_model;
    $("agent-form").querySelector("button[type=submit]").disabled = !values.agent_enabled || !$("agent-model").value;
    describeAgentModel();
    refreshVision();
  }

  function refreshVision() {
    const model = $("chat-model").value;
    const allowed = effective(model).vision;
    const hasProjector = state.info.image_models?.includes(model);
    const ready = allowed && hasProjector;
    $("chat-attachment").hidden = !ready;
    if (!ready) $("chat-image").value = "";
    const note = $("chat-vision-note");
    note.hidden = !model || Boolean(ready);
    note.textContent = allowed ? t("โมเดลนี้ต้องมีไฟล์ตัวอ่านภาพที่ตรงกันก่อนแนบภาพ") :
      t("การแนบภาพถูกปิดสำหรับโมเดลนี้");
  }

  function status(text, error = false) {
    const label = $("settings-status");
    label.textContent = text;
    label.classList.toggle("error", error);
  }

  function selectedPreset() {
    return current.presets?.find((preset) => preset.id === $("settings-preset").value);
  }

  function describePreset() {
    const preset = selectedPreset();
    $("settings-preset-apply").disabled = !preset;
    $("settings-preset-help").textContent = t(preset?.description) || t("เลือกชุดตามงานเพื่อใส่ค่าในฟอร์ม");
  }

  function collect() {
    const values = {};
    for (const input of $("settings-groups").querySelectorAll("[data-setting]")) {
      if (input.disabled) continue;
      const key = input.dataset.setting;
      values[key] = input.type === "checkbox" ? input.checked : input.type === "number" ? input.valueAsNumber : input.value;
    }
    return values;
  }

  function stored() {
    return scope === "global" ? effective() : current.models[scope] || {};
  }

  function dirty() {
    const values = collect();
    const saved = stored();
    return Object.keys(values).length !== Object.keys(saved).length ||
      Object.keys(values).some((key) => values[key] !== saved[key]);
  }

  function control(field, value) {
    const { key, kind } = field;
    let input;
    if (kind === "choice" || kind === "model") {
      input = element("select");
      const choices = kind === "model" ? state.info.models : field.choices;
      for (const [id, label] of Array.isArray(choices) ? choices.map((x) => [x, x]) : Object.entries(choices)) {
        input.add(new Option(t(label), id));
      }
      if (kind === "model" && !input.options.length) input.add(new Option(t("ยังไม่มีโมเดล"), value));
      input.value = kind === "model" && !state.info.models[value] ? input.options[0].value : value;
    } else if (kind === "text") {
      input = element("textarea");
      input.rows = key === "system_prompt" ? 3 : 2;
      input.maxLength = field.max;
      input.value = value;
    } else {
      input = element("input");
      if (kind === "bool") {
        input.type = "checkbox";
        input.checked = value;
      } else {
        input.type = "number";
        input.required = true;
        input.min = field.min;
        input.max = field.max;
        input.step = kind === "int" ? 1 : "any";
        input.value = Number.isFinite(value) ? value : "";
      }
    }
    input.id = "pref-" + key;
    input.dataset.setting = key;
    return input;
  }

  function draw(reveal = []) {
    const root = $("settings-groups");
    const open = new Set([...root.querySelectorAll("details[open]")].map((section) => section.dataset.title));
    if (!root.childElementCount) open.add("ทั่วไป");
    root.replaceChildren();
    const values = drafts.get(scope) || stored();
    const inherited = effective();
    for (const [title, fields] of Object.entries(current.schema)) {
      const visible = fields.filter((field) => scope === "global" || !field.global_only);
      if (!visible.length) continue;
      const group = element("details", null, "panel settings-group");
      group.dataset.title = title;
      group.open = open.has(title) || visible.some((field) => reveal.includes(field.key));
      const summary = element("summary");
      summary.append(element("strong", t(title)), element("span", visible.length + t(" ตัวเลือก")));
      const grid = element("div", null, "settings-grid");
      for (const field of visible) {
        const customized = scope === "global" || Object.hasOwn(values, field.key);
        const row = element("div", null, "setting-row" + (field.kind === "text" ? " setting-wide" : ""));
        const label = element("label", t(field.label));
        label.htmlFor = "pref-" + field.key;
        const input = control(field, customized ? values[field.key] : inherited[field.key]);
        input.disabled = !customized;
        if (field.hint) {
          const hint = element("p", t(field.hint), "hint");
          hint.id = input.id + "-help";
          input.setAttribute("aria-describedby", hint.id);
          row.append(label, hint);
        } else row.append(label);
        row.append(input);
        if (scope !== "global") {
          const customize = element("label", null, "setting-override");
          const checkbox = element("input");
          checkbox.type = "checkbox";
          checkbox.checked = customized;
          checkbox.setAttribute("aria-label", t("ปรับเฉพาะโมเดล · ") + t(field.label));
          checkbox.addEventListener("change", () => {
            input.disabled = !checkbox.checked;
            if (checkbox.checked) input.focus();
            else if (field.kind === "bool") input.checked = inherited[field.key];
            else input.value = inherited[field.key];
            status(dirty() ? t("มีการแก้ไขที่ยังไม่ได้บันทึก") : t("ค่าปัจจุบัน"));
          });
          customize.append(checkbox, element("span", t("ปรับเฉพาะโมเดล")));
          row.append(customize);
        }
        grid.append(row);
      }
      group.append(summary, grid);
      root.append(group);
    }
    $("settings-scope-help").textContent = scope === "global"
      ? t("ใช้เป็นค่าเริ่มต้นร่วมกัน ค่าที่บันทึกมีผลกับงานที่ส่งหลังจากนี้")
      : t("ตัวเลือกที่ไม่ได้เปิดปรับเฉพาะโมเดลจะใช้ค่ากลาง");
    $("settings-reset").textContent = scope === "global" ? t("คืนค่าเริ่มต้น") : t("ใช้ค่ากลางทั้งหมด");
    status(dirty() ? t("มีการแก้ไขที่ยังไม่ได้บันทึก") : t("ค่าปัจจุบัน"));
  }

  async function load(reset = false, initial = false) {
    const previous = current && !initial ? effective() : null;
    current = await api("settings");
    if (reset) drafts.clear();
    const selector = $("settings-scope");
    selector.replaceChildren(new Option(t("ค่ากลาง"), "global"));
    for (const [key, label] of Object.entries(state.info.models)) selector.add(new Option(label, key));
    selector.value = scope;
    const presets = $("settings-preset");
    const previousPreset = presets.value;
    presets.replaceChildren(new Option(t("เลือกชุดค่าตามงาน"), ""));
    for (const preset of current.presets || []) presets.add(new Option(t(preset.label), preset.id));
    if (current.presets?.some((preset) => preset.id === previousPreset)) presets.value = previousPreset;
    describePreset();
    apply(previous);
    draw();
  }

  function connect() {
    $("settings-preset").addEventListener("change", describePreset);
    $("settings-preset-apply").addEventListener("click", () => {
      const preset = selectedPreset();
      if (!preset) return;
      drafts.set(scope, { ...collect(), ...preset.values });
      draw(Object.keys(preset.values));
      status(dirty() ? t("ใส่ค่าชุดนี้ในฟอร์มแล้ว · ตรวจค่าแล้วกดบันทึก") : t("ชุดนี้ตรงกับค่าที่บันทึกอยู่"));
    });
    $("settings-scope").addEventListener("change", () => {
      if (dirty()) drafts.set(scope, collect());
      else drafts.delete(scope);
      scope = $("settings-scope").value;
      draw();
    });
    $("settings-form").addEventListener("input", () => {
      status(dirty() ? t("มีการแก้ไขที่ยังไม่ได้บันทึก") : t("ค่าปัจจุบัน"));
    });
    $("settings-form").addEventListener("invalid", (event) => {
      const group = event.target.closest("details");
      if (group) group.open = true;
    }, true);
    $("settings-reset").addEventListener("click", () => {
      drafts.set(scope, scope === "global" ? current.defaults : {});
      draw();
    });
    $("settings-reload").addEventListener("click", () => {
      load(true).then(() => status(t("โหลดค่าล่าสุดแล้ว"))).catch((error) => status(error.message, true));
    });
    $("settings-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = event.submitter;
      const saving = scope;
      button.disabled = true;
      $("settings-scope").disabled = true;
      $("settings-preset-apply").disabled = true;
      try {
        const previous = effective();
        current = await api("settings", { scope: saving, values: collect(), revision: current.revision });
        drafts.delete(saving);
        apply(previous);
        draw();
        status(t("บันทึกแล้ว · ใช้กับงานถัดไป"));
      } catch (error) {
        status(error.message, true);
      } finally {
        button.disabled = false;
        $("settings-scope").disabled = false;
        describePreset();
      }
    });

    $("settings-test").addEventListener("click", async () => {
      const output = $("settings-test-result");
      const button = $("settings-test");
      button.disabled = true;
      output.hidden = false;
      output.textContent = t("กำลังส่งข้อความทดสอบ…");
      try {
        const model = scope === "global" ? $("chat-model").value : scope;
        testedScope = state.info.models[model];
        testId = (await api("chat", { model, text: t("ตอบเพียงคำว่า พร้อม") })).id;
      } catch (error) {
        output.textContent = error.message;
        button.disabled = false;
      }
    });
  }

  async function poll() {
    if (!testId) return;
    const job = await api("jobs/" + testId);
    const output = $("settings-test-result");
    if (job.state === "done" || job.state === "error" || job.state === "cancelled") {
      testId = null;
      $("settings-test").disabled = false;
      output.textContent = testedScope + " · " + (job.result?.text || localMessage(job.error) || t("ยกเลิกแล้ว"));
      if (job.result?.tokens != null) output.textContent += " · " + job.result.tokens + t(" โทเคน");
    } else output.textContent = testedScope + " · " + describeJob(job);
  }

  return { connect, load, effective, refreshVision, poll };
})();
