(function () {
  const context = window.__WIZARD_CONTEXT__ || {};
  const state = {
    caseDir: null,
    currentStep: 1,
    candidate: context.candidate || {},
    inspect: null,
    scan: null,
    exportSummary: null,
  };

  const stepTitles = {
    1: "创建病例",
    2: "放入资料",
    3: "检查资料",
    4: "开始整理",
    5: "校对结果",
    6: "导出结果",
  };
  const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024;

  function byId(id) {
    return document.getElementById(id);
  }

  function setStatus(text) {
    const el = byId("step-status");
    if (el) el.textContent = text;
  }

  function renderStep() {
    Object.entries(stepTitles).forEach(([step, title]) => {
      const numericStep = Number(step);
      const panel = document.querySelector(`[data-step-panel="${numericStep}"]`);
      const chip = document.querySelector(`[data-step-chip="${numericStep}"]`);
      if (panel) {
        panel.classList.toggle("is-active", numericStep === state.currentStep);
      }
      if (chip) {
        chip.classList.toggle("is-active", numericStep === state.currentStep);
      }
    });

    const title = byId("step-title");
    if (title) title.textContent = stepTitles[state.currentStep] || "创建病例";
  }

  function goToStep(step) {
    state.currentStep = step;
    renderStep();
  }

  function setCaseState(text) {
    const el = byId("wizard-case-state");
    if (el) el.textContent = text;
  }

  function setFileState(text) {
    const el = byId("wizard-file-state");
    if (el) el.textContent = text;
  }

  function setScanState(text) {
    const el = byId("wizard-scan-state");
    if (el) el.textContent = text;
  }

  function escapeHtml(text) {
    return String(text)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function formatBytes(size) {
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }

  function encodeBytes(bytes) {
    let binary = "";
    const chunkSize = 0x8000;
    for (let i = 0; i < bytes.length; i += chunkSize) {
      const chunk = bytes.subarray(i, i + chunkSize);
      binary += String.fromCharCode.apply(null, chunk);
    }
    return btoa(binary);
  }

  async function readFileAsBase64(file) {
    const buffer = await file.arrayBuffer();
    return encodeBytes(new Uint8Array(buffer));
  }

  function renderInspect(summary) {
    const output = byId("inspect-output");
    if (!output) return;

    const categoryBlocks = (summary.categories || [])
      .map((item) => {
        const children = item.children
          ? `<div class="mini-tags">${Object.entries(item.children)
              .map(([name, count]) => `<span>${name}: ${count}</span>`)
              .join("")}</div>`
          : "";
        return `
          <article class="inspect-card">
            <div class="inspect-card-head">
              <strong>${item.label}</strong>
              <span>${item.count}</span>
            </div>
            ${children}
          </article>
        `;
      })
      .join("");

    const missing = (summary.missing_categories || [])
      .map((key) => `<span class="warn-chip">${key}</span>`)
      .join("");

    output.innerHTML = `
      <div class="inspect-overview">
        <div class="inspect-stat">
          <span>总文件数</span>
          <strong>${summary.total_files || 0}</strong>
        </div>
        <div class="inspect-stat">
          <span>分类数</span>
          <strong>${(summary.categories || []).length}</strong>
        </div>
      </div>
      <div class="inspect-grid-inner">${categoryBlocks}</div>
      <div class="inspect-missing">
        <span class="section-label">缺失提醒</span>
        <div class="tag-row">${missing || "<span class='muted'>暂无缺失</span>"}</div>
      </div>
    `;
    renderFileLists(summary.files || []);
  }

  function categoryOptions(selected) {
    const options = (context.rawCategories || []).flatMap((category) => {
      if (Array.isArray(category.children)) {
        return category.children.map((child) => {
          const key = `${category.key}/${child}`;
          return `<option value="${escapeHtml(key)}" ${
            selected === key ? "selected" : ""
          }>${escapeHtml(category.label)} / ${escapeHtml(child)}</option>`;
        });
      }
      return `<option value="${escapeHtml(category.key)}" ${
        selected === category.key ? "selected" : ""
      }>${escapeHtml(category.label)}</option>`;
    });
    return options.join("");
  }

  function renderFileLists(files) {
    const uploadList = byId("upload-file-list");
    const inspectList = byId("inspect-file-list");
    const rows = (files || []).map((file) => {
      const path = escapeHtml(file.relative_path);
      const name = escapeHtml(file.name);
      const category = escapeHtml(file.category_key);
      const size = formatBytes(Number(file.size_bytes || 0));
      return `
        <article class="file-row">
          <div class="file-row-top">
            <div>
              <strong>${name}</strong>
              <div class="file-meta">${path}<br>当前分类：${category} · ${size}</div>
            </div>
            <div class="file-actions">
              <select data-reassign-target="${path}">
                ${categoryOptions(file.category_key)}
              </select>
              <button class="secondary-btn" type="button" data-reassign-button="${path}">改分类</button>
              <button class="danger-btn" type="button" data-delete-button="${path}">删除</button>
            </div>
          </div>
        </article>
      `;
    });

    const html = rows.length ? `<div class="file-list">${rows.join("")}</div>` : "还没有上传文件。";
    if (uploadList) uploadList.innerHTML = rows.length ? html : `<div class="file-list-empty">${html}</div>`;
    if (inspectList) inspectList.innerHTML = rows.length ? html : `<div class="file-list-empty">${html}</div>`;

    bindFileActionButtons();
  }

  function renderScanResult(payload) {
    const output = byId("scan-output");
    const candidate = byId("candidate-json");
    if (!output) return;

    const manifest = payload.manifest || {};
    const failed = (manifest.failed_mineru_files || [])
      .map((item) => `<li>${item.file_path}: ${item.reason}</li>`)
      .join("");

    output.innerHTML = `
      <div class="process-stats">
        <div><span>已处理</span><strong>${manifest.processed_count || 0}</strong></div>
        <div><span>MinerU 成功</span><strong>${manifest.mineru_processed_count || 0}</strong></div>
        <div><span>失败</span><strong>${manifest.failed_mineru_count || 0}</strong></div>
      </div>
      <div class="process-paths">
        <div><span>manifest</span><code>${payload.manifest_path || ""}</code></div>
        <div><span>candidate</span><code>${payload.candidate_case_path || ""}</code></div>
      </div>
      <ul class="failure-list">${failed || "<li>暂无失败文件</li>"}</ul>
    `;

    if (candidate) {
      candidate.textContent = JSON.stringify(payload.candidate_case || {}, null, 2);
    }
  }

  function renderCandidate(payload) {
    const candidate = byId("candidate-json");
    if (candidate) {
      candidate.textContent = JSON.stringify(payload.candidate || {}, null, 2);
    }
  }

  function renderExportSummary(payload) {
    const output = byId("export-output");
    if (!output) return;

    const groups = Object.entries(payload.exports || {})
      .map(([name, info]) => {
        const status = info.exists ? "已生成" : "未生成";
        return `
          <article class="export-card">
            <strong>${name}</strong>
            <span>${status}</span>
            <code>${info.path}</code>
          </article>
        `;
      })
      .join("");

    output.innerHTML = `
      <div class="export-grid-inner">${groups}</div>
      <p class="muted">候选结构已准备好后，可进一步接入 ca199_toolbox 的展示页。</p>
    `;
  }

  async function createCase() {
    const input = byId("case-name");
    const caseName = input ? input.value.trim() : "";
    if (!caseName) {
      setStatus("请输入病例名称");
      return;
    }

    const response = await fetch("/api/wizard/init", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_name: caseName }),
    });
    if (!response.ok) {
      setStatus("病例初始化失败");
      return;
    }

    const payload = await response.json();
    state.caseDir = payload.case_dir;
    setStatus(`病例已创建：${caseName}`);
    setCaseState(`当前病例：${caseName}`);
    const root = byId("case-root");
    const workspace = byId("workspace-dir");
    if (root && payload.case_dir) {
      const parts = payload.case_dir.split("/");
      parts.pop();
      root.textContent = parts.join("/") || payload.case_dir;
    }
    if (workspace) workspace.textContent = state.caseDir;
    setFileState("资料尚未检查");
    setScanState("等待整理");
    goToStep(2);
    await refreshInspect();
  }

  async function refreshInspect() {
    if (!state.caseDir) {
      setStatus("请先创建病例");
      return;
    }

    const url = new URL("/api/wizard/inspect", window.location.origin);
    url.searchParams.set("case_dir", state.caseDir);
    const response = await fetch(url);
    if (!response.ok) {
      setStatus("检查资料失败");
      return;
    }

    const payload = await response.json();
    state.inspect = payload;
    renderInspect(payload);
    setFileState(`已识别 ${payload.total_files || 0} 个文件`);
    setStatus("资料检查已刷新");
    goToStep(3);
  }

  async function uploadToCategory(categoryKey) {
    if (!state.caseDir) {
      setStatus("请先创建病例");
      return;
    }

    const input = document.querySelector(`[data-file-input="${categoryKey}"]`);
    if (!(input instanceof HTMLInputElement) || !input.files || !input.files.length) {
      setStatus("请选择要上传的文件");
      return;
    }

    const files = Array.from(input.files);
    for (const file of files) {
      if (file.size > MAX_UPLOAD_SIZE_BYTES) {
        setStatus(`文件过大：${file.name} 超过 10MB`);
        return;
      }
    }

    const failures = [];
    for (const file of files) {
      const contentBase64 = await readFileAsBase64(file);
      const response = await fetch("/api/wizard/upload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_dir: state.caseDir,
          category_key: categoryKey,
          filename: file.name,
          content_base64: contentBase64,
        }),
      });
      if (!response.ok) {
        failures.push(file.name);
      }
    }

    input.value = "";
    if (failures.length) {
      setStatus(`部分上传失败：${failures.join("、")}`);
    } else {
      setStatus(`已上传 ${files.length} 个文件到 ${categoryKey}`);
    }
    setFileState(`已上传 ${files.length} 个文件`);
    await refreshInspect();
    goToStep(2);
  }

  async function deleteFile(relativePath) {
    if (!state.caseDir) return;
    const response = await fetch("/api/wizard/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_dir: state.caseDir, relative_path: relativePath }),
    });
    if (!response.ok) {
      setStatus("删除文件失败");
      return;
    }
    setStatus(`已删除 ${relativePath}`);
    await refreshInspect();
    goToStep(3);
  }

  async function reassignFile(relativePath) {
    if (!state.caseDir) return;
    const select = document.querySelector(`[data-reassign-target="${CSS.escape(relativePath)}"]`);
    if (!(select instanceof HTMLSelectElement)) return;
    const response = await fetch("/api/wizard/reassign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        case_dir: state.caseDir,
        relative_path: relativePath,
        category_key: select.value,
      }),
    });
    if (!response.ok) {
      setStatus("改分类失败");
      return;
    }
    setStatus(`已更新分类：${relativePath}`);
    await refreshInspect();
    goToStep(3);
  }

  async function runScan() {
    if (!state.caseDir) {
      setStatus("请先创建病例");
      return;
    }

    setStatus("正在整理，请稍候");
    setScanState("整理中");
    goToStep(4);

    const response = await fetch("/api/wizard/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_dir: state.caseDir }),
    });
    if (!response.ok) {
      setStatus("整理失败");
      setScanState("整理失败");
      return;
    }

    const payload = await response.json();
    state.scan = payload;
    renderScanResult(payload);
    setScanState(`整理完成：${payload.manifest?.processed_count || 0} 个文件`);
    setStatus("整理完成");
    goToStep(5);
  }

  async function loadCandidate() {
    const response = await fetch("/api/wizard/candidate");
    if (!response.ok) return;
    const payload = await response.json();
    state.candidate = payload.candidate || {};
    renderCandidate(payload);
    setStatus("候选结构已刷新");
    goToStep(5);
  }

  async function loadExportSummary() {
    if (!state.caseDir) {
      setStatus("请先创建病例");
      return;
    }

    const url = new URL("/api/wizard/export-summary", window.location.origin);
    url.searchParams.set("case_dir", state.caseDir);
    const response = await fetch(url);
    if (!response.ok) {
      setStatus("导出摘要读取失败");
      return;
    }

    const payload = await response.json();
    state.exportSummary = payload;
    renderExportSummary(payload);
    setStatus("导出摘要已刷新");
    goToStep(6);
  }

  function bindUploadButtons() {
    document.querySelectorAll("[data-upload-button]").forEach((button) => {
      if (!(button instanceof HTMLButtonElement)) return;
      const categoryKey = button.getAttribute("data-upload-button");
      if (!categoryKey) return;
      button.addEventListener("click", () => uploadToCategory(categoryKey));
    });
  }

  function bindFileActionButtons() {
    document.querySelectorAll("[data-delete-button]").forEach((button) => {
      if (!(button instanceof HTMLButtonElement)) return;
      const relativePath = button.getAttribute("data-delete-button");
      if (!relativePath) return;
      button.onclick = () => deleteFile(relativePath);
    });
    document.querySelectorAll("[data-reassign-button]").forEach((button) => {
      if (!(button instanceof HTMLButtonElement)) return;
      const relativePath = button.getAttribute("data-reassign-button");
      if (!relativePath) return;
      button.onclick = () => reassignFile(relativePath);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindUploadButtons();
    renderStep();
    setStatus("请先创建病例");
  });

  window.caseWizard = {
    goToStep,
    createCase,
    refreshInspect,
    runScan,
    loadCandidate,
    loadExportSummary,
    deleteFile,
    reassignFile,
  };
})();
