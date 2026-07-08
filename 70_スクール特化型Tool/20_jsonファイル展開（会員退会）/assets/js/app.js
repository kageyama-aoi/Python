let jsonData = null;
let currentIndex = 0;
let isExpandedGlobal = false;

const fileInput = document.getElementById("fileInput");
const tabsContainer = document.getElementById("tabs");
const output = document.getElementById("output");
const commonInfo = document.getElementById("commonInfo");
const fileName = document.getElementById("fileName");

fileInput.addEventListener("change", function (e) {
  const file = e.target.files[0];
  if (!file) return;
  if (fileName) fileName.textContent = file.name;

  const reader = new FileReader();
  reader.onload = function (evt) {
    jsonData = JSON.parse(evt.target.result);
    renderCommonInfo();
    initializeTabs();
  };
  reader.readAsText(file);
});

function renderCommonInfo() {
  if (!jsonData) return;

  const studentId = jsonData.student?.id ?? "-";
  const bankValue = jsonData.student?.bank_payment_type?.value ?? "-";
  const bankLabel =
    jsonData.student?.bank_payment_type?.value_meta?.options?.find(
      (o) => o.value === bankValue
    )?.label ?? "";
  const systemMonth = jsonData.context?.system_month ?? "-";

  commonInfo.style.display = "block";
  commonInfo.className = "card summary-card";
  commonInfo.innerHTML = `
    <div class="summary-title">共通情報</div>
    <div class="summary-grid">
      <div class="metric">
        <div class="metric-label">student.id</div>
        <div class="metric-value">${studentId}</div>
      </div>
      <div class="metric">
        <div class="metric-label">bank_payment_type</div>
        <div class="metric-value">${bankValue}${bankLabel ? ` (${bankLabel})` : ""}</div>
      </div>
      <div class="metric">
        <div class="metric-label">system_month</div>
        <div class="metric-value">${systemMonth}</div>
      </div>
    </div>
  `;
}

function initializeTabs() {
  tabsContainer.innerHTML = "";

  (jsonData.courses ?? []).forEach((course, index) => {
    const tab = document.createElement("div");
    tab.className = "tab" + (index === 0 ? " active" : "");
    tab.textContent = course.event_name ?? `course_${index + 1}`;
    tab.onclick = () => switchTab(index);
    tabsContainer.appendChild(tab);
  });

  renderCourse(0);
}

function switchTab(index) {
  currentIndex = index;
  document.querySelectorAll(".tab").forEach((tab, i) => {
    tab.classList.toggle("active", i === index);
  });
  renderCourse(index);
}

function renderCourse(index) {
  const course = (jsonData.courses ?? [])[index];
  if (!course) return;

  output.innerHTML = "";

  output.appendChild(createCourseSummaryCard(course));
  output.appendChild(createRouteDiagramCard(course));

  const timeline = document.createElement("div");
  timeline.className = "timeline";

  (course.conditions ?? []).forEach((cond) => {
    timeline.appendChild(createTimelineItem(cond));
  });

  output.appendChild(timeline);

  if (isExpandedGlobal) {
    expandAll();
  } else {
    collapseAll();
  }
}

function createCourseSummaryCard(course) {
  const card = document.createElement("div");
  card.className = "card summary-card";

  const summary = countCourseSummary(course.conditions ?? []);
  const inputSnapshot = buildInputSnapshotHtml(course);

  card.innerHTML = `
    <div class="summary-title">${course.event_name ?? "コース"} / 処理サマリー</div>
    <div class="summary-grid">
      <div class="metric">
        <div class="metric-label">実行ロジック</div>
        <div class="metric-value">${summary.executed}</div>
      </div>
      <div class="metric">
        <div class="metric-label">対象判定あり</div>
        <div class="metric-value">${summary.target}</div>
      </div>
      <div class="metric">
        <div class="metric-label">更新レコード合計</div>
        <div class="metric-value">${summary.updated}</div>
      </div>
      <div class="metric">
        <div class="metric-label">main_root / final_employment_month</div>
        <div class="metric-value">${course.precondition?.main_root?.value ?? "-"} / ${course.precondition?.final_employment_month?.value ?? "-"}</div>
      </div>
    </div>
    ${inputSnapshot}
  `;

  return card;
}

function buildInputSnapshotHtml(course) {
  const rows = [];
  const pre = course?.precondition ?? {};

  for (const key of Object.keys(pre)) {
    const item = pre[key];
    if (!item || typeof item !== "object") continue;

    if ("value" in item) {
      const value = item.value ?? "-";
      const note = item?.value_meta?.note ?? "";
      const label = resolveOptionLabel(item, value);
      rows.push({
        key,
        value: `${value}${label ? ` (${label})` : ""}`,
        note,
      });
    }

    if ("input_month" in item) {
      rows.push({
        key: `${key}.input_month`,
        value: item.input_month ?? "-",
        note: "判定に使用した入力月",
      });
    }
  }

  if (rows.length === 0) return "";

  const body = rows
    .map(
      (r) => `
      <div class="input-row">
        <div class="input-key">${escapeHtml(r.key)}</div>
        <div class="input-value">${escapeHtml(String(r.value))}</div>
        <div class="input-note">${escapeHtml(r.note || "")}</div>
      </div>
    `
    )
    .join("");

  return `
    <div class="input-panel">
      <div class="input-title">入力スナップショット（このコースで判定に使った値）</div>
      <div class="input-table">
        <div class="input-row input-head">
          <div>入力キー</div>
          <div>値</div>
          <div>意味</div>
        </div>
        ${body}
      </div>
    </div>
  `;
}

function resolveOptionLabel(item, value) {
  const options = item?.value_meta?.options;
  if (!Array.isArray(options)) return "";
  const matched = options.find((o) => o?.value === value);
  return matched?.label ?? "";
}

function createTimelineItem(cond) {
  const item = document.createElement("div");
  item.className = "timeline-item";

  const node = document.createElement("div");
  node.className = "node";
  node.innerHTML = `<span class="material-symbols-outlined">${selectNodeIcon(cond)}</span>`;

  if (cond.result?.has_target === "Y") {
    node.classList.add("target");
  } else if (cond.executed === "Y") {
    node.classList.add("executed");
  }

  const card = document.createElement("div");
  card.className = "card logic-card";

  const badges = buildBadges(cond);
  const reason = buildReason(cond);
  const noteHtml = buildNoteSection(cond);

  card.innerHTML = `
    <div class="logic-head">
      <div class="logic-name">${cond.logic_no ?? "-"} ${cond.logic_name ?? "(名称なし)"}</div>
      <div class="badges">${badges}</div>
    </div>
    <div class="reason">${reason}</div>
    ${noteHtml}
  `;

  const actionRow = document.createElement("div");
  actionRow.className = "action-row";

  if (cond.route_scope) {
    const detailToggle = createToggleButton("判定スコープを表示", "判定スコープを閉じる");
    const detailBox = document.createElement("div");
    detailBox.className = "detail-box";
    detailBox.innerHTML = `<strong>Route Scope</strong><br/>${formatObject(cond.route_scope)}`;

    detailToggle.addEventListener("click", () => {
      toggleSection(detailToggle, detailBox);
    });

    actionRow.appendChild(detailToggle);
    card.appendChild(actionRow);
    card.appendChild(detailBox);
  }

  if (cond.child_logic) {
    const childToggle = createToggleButton("子ロジック分岐を表示", "子ロジック分岐を閉じる");
    const childContent = document.createElement("div");
    childContent.className = "child-content";

    const label = document.createElement("div");
    label.className = "child-label";
    label.textContent = "child_logic";

    childContent.appendChild(label);
    childContent.appendChild(createTimelineItem(cond.child_logic));

    childToggle.addEventListener("click", () => {
      toggleSection(childToggle, childContent);
    });

    actionRow.appendChild(childToggle);
    if (!card.contains(actionRow)) card.appendChild(actionRow);
    card.appendChild(childContent);
  }

  item.appendChild(node);
  item.appendChild(card);
  return item;
}

function countCourseSummary(conditions) {
  const stack = [...conditions];
  const result = { executed: 0, target: 0, updated: 0 };

  while (stack.length > 0) {
    const cond = stack.pop();
    if (!cond) continue;

    if (cond.executed === "Y") result.executed += 1;
    if (cond.result?.has_target === "Y") result.target += 1;

    const updated = Number(cond.update?.updated_records ?? 0);
    if (!Number.isNaN(updated)) result.updated += updated;

    if (cond.child_logic) stack.push(cond.child_logic);
  }

  return result;
}

function buildBadges(cond) {
  const list = [];
  const noteStatus = getBusinessNoteStatus(cond);

  if (noteStatus.written) {
    list.push('<span class="badge badge-note-ok"><span class="material-symbols-outlined">sticky_note_2</span>NOTE WRITTEN</span>');
  } else {
    list.push('<span class="badge badge-note-skip"><span class="material-symbols-outlined">note_stack</span>NOTE SKIPPED</span>');
  }

  if (cond.executed === "Y") {
    list.push('<span class="badge badge-ok"><span class="material-symbols-outlined">task_alt</span>EXECUTED</span>');
  } else {
    list.push('<span class="badge badge-skip"><span class="material-symbols-outlined">do_not_disturb_on</span>NOT EXECUTED</span>');
  }

  if (cond.result?.has_target === "Y") {
    list.push('<span class="badge badge-target"><span class="material-symbols-outlined">my_location</span>TARGET</span>');
  }

  const updated = Number(cond.update?.updated_records ?? 0);
  if (updated > 0) {
    list.push(`<span class="badge badge-update"><span class="material-symbols-outlined">sync_alt</span>UPDATED ${updated}</span>`);
  }

  return list.join("");
}

function buildReason(cond) {
  const parts = [];
  const noteStatus = getBusinessNoteStatus(cond);

  parts.push(noteStatus.written ? "業務ノートあり。" : "業務ノートはスキップ。");

  parts.push(cond.executed === "Y" ? "実行済みロジックです。" : "このロジックは未実行です。");

  if (cond.result?.has_target === "Y") {
    parts.push("対象判定あり。");
  } else {
    parts.push("対象判定なし。");
  }

  const updated = Number(cond.update?.updated_records ?? 0);
  if (updated > 0) {
    parts.push(`更新レコードは ${updated} 件です。`);
  }

  return parts.join(" ");
}

function buildNoteSection(cond) {
  const notes = extractNotes(cond);
  const status = notes.length > 0 ? "記載あり" : "スキップ";
  const statusClass = notes.length > 0 ? "note-status-ok" : "note-status-skip";

  const body =
    notes.length > 0
      ? notes
          .map((note) => `<span class="note-chip"><span class="material-symbols-outlined">sticky_note_2</span>${escapeHtml(note)}</span>`)
          .join("")
      : '<div class="note-empty">このロジックでは業務ノートは未記載です。</div>';

  return `
    <div class="note-section">
      <div class="note-head">
        <div class="note-title">業務ノート</div>
        <span class="note-status ${statusClass}">${status}</span>
      </div>
      <div class="note-list">${body}</div>
    </div>
  `;
}

function getBusinessNoteStatus(cond) {
  const notes = extractNotes(cond);
  return {
    written: notes.length > 0,
    count: notes.length,
  };
}

function createRouteDiagramCard(course) {
  const card = document.createElement("div");
  card.className = "card route-card";

  const graph = buildRouteGraph(course.conditions ?? []);

  if (graph.topOrder.length === 0) {
    card.innerHTML = `
      <div class="summary-title">ルート図（条件付き遷移）</div>
      <div class="route-empty">表示できるロジックがありません。</div>
    `;
    return card;
  }

  const mainFlow = graph.topOrder
    .map((id, index) => {
      const node = graph.nodesById.get(id);
      if (!node) return "";
      const arrow = index < graph.topOrder.length - 1 ? '<span class="route-arrow-main">→</span>' : "";
      return `${buildRouteNodeHtml(node, "route-node")}${arrow}`;
    })
    .join("");

  const branchRows = graph.branchEdges
    .map((edge) => {
      const fromNode = graph.nodesById.get(edge.from);
      const toNode = graph.nodesById.get(edge.to);
      if (!fromNode || !toNode) return "";
      const label = edge.label ? `<span class="route-branch-label">${escapeHtml(edge.label)}</span>` : "";
      return `
        <div class="route-branch route-branch-${edge.type}">
          ${buildRouteNodeHtml(fromNode, "route-node-mini")}
          <span class="route-arrow-branch">↳</span>
          ${label}
          ${buildRouteNodeHtml(toNode, "route-node-mini")}
        </div>
      `;
    })
    .join("");

  card.innerHTML = `
    <div class="summary-title">ルート図（条件付き遷移）</div>
    <div class="route-main">${mainFlow}</div>
    ${branchRows ? `<div class="route-branches">${branchRows}</div>` : ""}
  `;
  return card;
}

function buildRouteNodeHtml(node, className) {
  const classes = [
    className,
    node.executed === "Y" ? "is-executed" : "is-skipped",
    node.hasTarget === "Y" ? "is-target" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return `<span class="${classes}">${escapeHtml(node.logicNo)} ${escapeHtml(node.logicName)}</span>`;
}

function buildRouteGraph(conditions) {
  const nodesById = new Map();
  const topOrder = [];
  const branchEdges = [];
  const nameToId = new Map();

  let previousTopId = null;

  function walk(cond, path, parentId = null) {
    if (!cond || typeof cond !== "object") return;

    const id = `logic_${path.join("_")}`;
    const logicName = cond.logic_name ?? id;
    const logicNo = cond.logic_no ?? "-";

    nodesById.set(id, {
      id,
      logicName,
      logicNo,
      executed: cond.executed ?? "N",
      hasTarget: cond.result?.has_target ?? "N",
    });

    if (!nameToId.has(logicName)) {
      nameToId.set(logicName, id);
    }

    if (path.length === 1) {
      topOrder.push(id);
      if (previousTopId) {
        branchEdges.push({
          type: "sequence",
          from: previousTopId,
          to: id,
          label: "次ルート",
        });
      }
      previousTopId = id;
    }

    if (parentId) {
      branchEdges.push({
        type: "child",
        from: parentId,
        to: id,
        label: buildBranchConditionLabel(cond),
      });
    }

    const dependsOn = cond?.route_scope?.depends_on;
    if (typeof dependsOn === "string" && dependsOn.trim()) {
      const fromId = nameToId.get(dependsOn.trim());
      if (fromId) {
        branchEdges.push({
          type: "depends",
          from: fromId,
          to: id,
          label: buildBranchConditionLabel(cond),
        });
      }
    }

    if (cond.child_logic) {
      walk(cond.child_logic, [...path, 1], id);
    }
  }

  (conditions ?? []).forEach((cond, index) => {
    walk(cond, [index + 1], null);
  });

  const visualBranchEdges = branchEdges.filter((edge) => edge.type !== "sequence");
  return { nodesById, topOrder, branchEdges: visualBranchEdges };
}

function buildBranchConditionLabel(cond) {
  const scope = cond?.route_scope;
  if (!scope || typeof scope !== "object") return "分岐";

  const labels = [];
  if (scope.depends_on) labels.push(`depends_on=${scope.depends_on}`);
  if (scope.has_target) labels.push(`has_target=${scope.has_target}`);

  return labels.length > 0 ? labels.join(" / ") : "分岐";
}

function extractNotes(cond) {
  const notes = [];
  const push = (value) => {
    if (typeof value !== "string") return;
    const trimmed = value.trim();
    if (!trimmed) return;
    if (!notes.includes(trimmed)) notes.push(trimmed);
  };

  push(cond?.note);
  push(cond?.meta?.note);
  push(cond?.update?.meta?.note);
  push(cond?.create?.meta?.note);
  push(cond?.result?.meta?.note);
  push(cond?.route_scope?.meta?.note);

  return notes;
}

function selectNodeIcon(cond) {
  if (Number(cond.update?.updated_records ?? 0) > 0) return "sync_alt";
  if (cond.result?.has_target === "Y") return "my_location";
  if (cond.executed === "Y") return "task_alt";
  return "radio_button_unchecked";
}

function createToggleButton(closedText, openedText) {
  const button = document.createElement("button");
  button.className = "toggle";
  button.dataset.closedText = closedText;
  button.dataset.openedText = openedText;
  button.dataset.opened = "false";
  button.innerHTML =
    '<span class="material-symbols-outlined">expand_more</span><span class="toggle-label"></span>';
  setToggleVisual(button, false);
  return button;
}

function toggleSection(toggle, section) {
  const isOpen = section.style.display === "block";
  section.style.display = isOpen ? "none" : "block";
  setToggleVisual(toggle, !isOpen);
}

function setToggleVisual(toggle, opened) {
  const icon = toggle.querySelector(".material-symbols-outlined");
  const label = toggle.querySelector(".toggle-label");
  toggle.dataset.opened = opened ? "true" : "false";
  if (icon) icon.textContent = opened ? "expand_less" : "expand_more";
  if (label) label.textContent = opened ? toggle.dataset.openedText : toggle.dataset.closedText;
}

function expandAll() {
  isExpandedGlobal = true;
  document.querySelectorAll(".detail-box, .child-content").forEach((el) => {
    el.style.display = "block";
  });
  document.querySelectorAll(".toggle").forEach((btn) => {
    setToggleVisual(btn, true);
  });
}

function collapseAll() {
  isExpandedGlobal = false;
  document.querySelectorAll(".detail-box, .child-content").forEach((el) => {
    el.style.display = "none";
  });
  document.querySelectorAll(".toggle").forEach((btn) => {
    setToggleVisual(btn, false);
  });
}

function formatObject(obj) {
  if (typeof obj === "string") return obj;

  let html = "";
  for (const key in obj) {
    html += `${key} : ${JSON.stringify(obj[key])}<br/>`;
  }
  return html;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

window.expandAll = expandAll;
window.collapseAll = collapseAll;
