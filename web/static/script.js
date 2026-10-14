"use strict";

const state = { mode: "unknown", fixture: false };

function clear(node) {
    node.replaceChildren();
}

function setBusy(form, busy, activeLabel, idleLabel) {
    const button = form.querySelector('button[type="submit"]');
    button.disabled = busy;
    button.querySelector(".btn-text").textContent = busy ? activeLabel : idleLabel;
    button.querySelector(".loading-spinner").hidden = !busy;
}

function addIcon(target, kind) {
    const icon = document.createElement("span");
    icon.className = `message-icon message-icon-${kind}`;
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = kind === "error" ? "!" : "✓";
    target.appendChild(icon);
}

function showError(anchor, message) {
    document.getElementById(`${anchor.id}Error`)?.remove();
    const error = document.createElement("div");
    error.id = `${anchor.id}Error`;
    error.className = "error-message";
    error.setAttribute("role", "alert");
    addIcon(error, "error");
    const text = document.createElement("span");
    text.className = "error-text";
    text.textContent = String(message);
    error.appendChild(text);
    anchor.insertAdjacentElement("afterend", error);
}

function setMode(mode, fixture) {
    state.mode = mode;
    state.fixture = fixture;
    const badge = document.getElementById("modeBadge");
    badge.dataset.mode = mode;
    document.getElementById("modeLabel").textContent = fixture
        ? "FICTIONAL FIXTURE · PROVIDER-FREE"
        : "LIVE MODE · PROVIDER REQUIRED";
    document.getElementById("fixtureNotice").hidden = !fixture;
    document.querySelectorAll(".result-mode").forEach((node) => {
        node.textContent = fixture ? "fictional fixture" : "live provider";
    });
}

function renderAnswer(target, value) {
    clear(target);
    const text = document.createElement("p");
    text.className = "answer-text";
    text.textContent = String(value);
    target.appendChild(text);
}

function createCodeBlock(code, language) {
    const wrapper = document.createElement("div");
    wrapper.className = "code-block";
    const header = document.createElement("div");
    header.className = "code-header";
    const label = document.createElement("span");
    label.className = "code-language";
    label.textContent = language || "code";
    const copy = document.createElement("button");
    copy.className = "copy-btn";
    copy.type = "button";
    copy.textContent = "Copy";
    copy.addEventListener("click", async () => {
        await navigator.clipboard.writeText(String(code));
        copy.textContent = "Copied";
        window.setTimeout(() => { copy.textContent = "Copy"; }, 1200);
    });
    header.append(label, copy);
    const pre = document.createElement("pre");
    const codeNode = document.createElement("code");
    codeNode.textContent = String(code);
    pre.appendChild(codeNode);
    wrapper.append(header, pre);
    return wrapper;
}

async function errorFrom(response) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
        const data = await response.json();
        return data.detail || data.error || `Request failed (${response.status})`;
    }
    return (await response.text()) || `Request failed (${response.status})`;
}

async function initializeMode() {
    try {
        const response = await fetch("/health", { headers: { Accept: "application/json" } });
        if (!response.ok) throw new Error(`Health check failed (${response.status})`);
        const data = await response.json();
        setMode(data.mode, Boolean(data.fixture));
    } catch (error) {
        setMode("unknown", false);
        showError(document.getElementById("modeBadge"), error.message);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initializeMode();
    const askForm = document.getElementById("askForm");
    const answer = document.getElementById("answer");
    const answerContent = document.getElementById("answerContent");
    askForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (askForm.nextElementSibling?.id === "askFormError") askForm.nextElementSibling.remove();
        setBusy(askForm, true, "Retrieving…", "Ask question");
        try {
            const response = await fetch("/api/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json", Accept: "text/plain" },
                body: JSON.stringify({ question: document.getElementById("question").value, language: "python" })
            });
            if (!response.ok) throw new Error(await errorFrom(response));
            renderAnswer(answerContent, await response.text());
            answer.hidden = false;
            answer.scrollIntoView({ behavior: "smooth", block: "nearest" });
        } catch (error) {
            answer.hidden = true;
            showError(askForm, error.message || "Unable to retrieve guidance");
        } finally {
            setBusy(askForm, false, "Retrieving…", "Ask question");
        }
    });

    const generateForm = document.getElementById("generateForm");
    const generateResult = document.getElementById("generateResult");
    const codeOutput = document.getElementById("codeOutput");
    generateForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (generateForm.nextElementSibling?.id === "generateFormError") generateForm.nextElementSibling.remove();
        setBusy(generateForm, true, "Generating…", "Generate code");
        try {
            const response = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json", Accept: "application/json" },
                body: JSON.stringify({
                    task: document.getElementById("prompt").value,
                    language: document.getElementById("language").value,
                    framework: document.getElementById("framework").value
                })
            });
            if (!response.ok) throw new Error(await errorFrom(response));
            const data = await response.json();
            clear(codeOutput);
            codeOutput.appendChild(createCodeBlock(data.code, document.getElementById("language").value));
            generateResult.hidden = false;
            generateResult.scrollIntoView({ behavior: "smooth", block: "nearest" });
        } catch (error) {
            generateResult.hidden = true;
            showError(generateForm, error.message || "Unable to generate code");
        } finally {
            setBusy(generateForm, false, "Generating…", "Generate code");
        }
    });
});
