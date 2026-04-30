"use strict";

const questionEl = document.getElementById("question");
const submitBtn = document.getElementById("submit-btn");
const pipelineEl = document.getElementById("pipeline");
const stepsEl = document.getElementById("steps");
const reportSection = document.getElementById("report-section");
const reportOutput = document.getElementById("report-output");
const copyBtn = document.getElementById("copy-btn");

let rawMarkdown = "";
let renderTimer = null;

// Example queries
document.querySelectorAll(".example-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    questionEl.value = btn.dataset.query;
    questionEl.focus();
  });
});

// Ctrl+Enter to submit
questionEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    startResearch();
  }
});

submitBtn.addEventListener("click", startResearch);

copyBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(rawMarkdown).then(() => {
    copyBtn.textContent = "Copied!";
    setTimeout(() => (copyBtn.textContent = "Copy report"), 2000);
  });
});

function addStep(text, state = "running") {
  const div = document.createElement("div");
  div.className = `step ${state}`;
  div.innerHTML = `
    <div class="step-icon">${state === "done" ? "✓" : state === "error" ? "✕" : ""}</div>
    <div class="step-text">${escapeHtml(text)}</div>`;
  stepsEl.appendChild(div);
  return div;
}

function updateLastStep(text, state) {
  const steps = stepsEl.querySelectorAll(".step");
  if (!steps.length) return;
  const last = steps[steps.length - 1];
  last.className = `step ${state}`;
  last.querySelector(".step-icon").textContent =
    state === "done" ? "✓" : state === "error" ? "✕" : "";
  if (text) last.querySelector(".step-text").textContent = text;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function scheduleRender() {
  if (renderTimer) clearTimeout(renderTimer);
  renderTimer = setTimeout(() => {
    reportOutput.innerHTML = marked.parse(rawMarkdown);
    reportOutput.classList.add("cursor");
  }, 50);
}

function handleEvent(type, content) {
  switch (type) {
    case "status":
      addStep(content);
      break;

    case "queries": {
      updateLastStep("Planning complete", "done");
      const queryStep = document.createElement("div");
      queryStep.className = "step done";
      queryStep.innerHTML = `
        <div class="step-icon">✓</div>
        <div class="step-text">
          Search queries planned
          <div class="query-tags">${content
            .map((q) => `<span class="query-tag">${escapeHtml(q)}</span>`)
            .join("")}</div>
        </div>`;
      stepsEl.appendChild(queryStep);
      break;
    }

    case "search_complete": {
      const label = content.error
        ? `Search failed: ${content.error}`
        : `"${content.query}" — ${content.source_count} source(s) found`;
      const state = content.error ? "error" : "done";
      addStep(label, state);
      break;
    }

    case "report_start":
      updateLastStep("Synthesis in progress…", "running");
      reportSection.style.display = "block";
      rawMarkdown = "";
      reportOutput.innerHTML = "";
      reportOutput.classList.add("cursor");
      break;

    case "report_chunk":
      rawMarkdown += content;
      scheduleRender();
      break;

    case "done":
      if (renderTimer) clearTimeout(renderTimer);
      reportOutput.innerHTML = marked.parse(rawMarkdown);
      reportOutput.classList.remove("cursor");
      updateLastStep("Report generated", "done");
      submitBtn.disabled = false;
      submitBtn.textContent = "Research";
      break;

    case "error":
      updateLastStep(content, "error");
      reportOutput.classList.remove("cursor");
      submitBtn.disabled = false;
      submitBtn.textContent = "Research";
      break;
  }
}

async function startResearch() {
  const question = questionEl.value.trim();
  if (!question) {
    questionEl.focus();
    return;
  }

  // Reset UI
  submitBtn.disabled = true;
  submitBtn.textContent = "Researching…";
  stepsEl.innerHTML = "";
  reportOutput.innerHTML = "";
  rawMarkdown = "";
  pipelineEl.style.display = "block";
  reportSection.style.display = "none";

  try {
    const response = await fetch("/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      addStep(`Request failed: ${err.detail || response.statusText}`, "error");
      submitBtn.disabled = false;
      submitBtn.textContent = "Research";
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE messages (terminated by \n\n)
      const parts = buffer.split("\n\n");
      buffer = parts.pop(); // last part may be incomplete

      for (const part of parts) {
        for (const line of part.split("\n")) {
          if (line.startsWith("data: ")) {
            try {
              const { type, content } = JSON.parse(line.slice(6));
              handleEvent(type, content);
            } catch {
              // ignore malformed lines
            }
          }
        }
      }
    }
  } catch (err) {
    addStep(`Connection error: ${err.message}`, "error");
    submitBtn.disabled = false;
    submitBtn.textContent = "Research";
  }
}
