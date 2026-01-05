// We use a specific esm.sh feature to bundle all dependencies into one single
// executable instance. This prevents the "Unrecognized extension" error by
// ensuring only one copy of @codemirror/state exists in memory.
import {
    EditorView,
    basicSetup
} from "https://esm.sh/codemirror@6.0.1?bundle";

import {
    EditorState
} from "https://esm.sh/@codemirror/state@6.0.0?bundle";

import {
    html
} from "https://esm.sh/@codemirror/lang-html@6.0.0?deps=@codemirror/state@6.0.0";

import {
    oneDark
} from "https://esm.sh/@codemirror/theme-one-dark@6.0.0?deps=@codemirror/state@6.0.0";

console.log("editor.js (CodeMirror 6 Module) initialized");

let editorView = null;
let currentPath = "";

function createTreeHTML(items, parentPath = "") {
    let htmlStr = '<div class="list-group list-group-flush">';
    items.forEach(item => {
        const path = parentPath ? `${parentPath}/${item.name}` : item.name;
        if (item.type === "folder") {
            htmlStr += `
                <details class="ms-2">
                    <summary class="list-group-item list-group-item-action fw-bold border-0 p-1">
                        📁 ${item.name}
                    </summary>
                    ${createTreeHTML(item.children, path)}
                </details>`;
        } else {
            htmlStr += `
                <button type="button" class="list-group-item list-group-item-action file-item border-0 py-1 ps-3"
                        data-path="${path}">
                    📄 ${item.name}
                </button>`;
        }
    });
    htmlStr += '</div>';
    return htmlStr;
}

function initEditor(initialContent = "") {
    const target = document.getElementById("cm-editor-target");
    if (!target) {
        console.error("Editor target div '#cm-editor-target' not found!");
        return;
    }

    if (editorView) {
        // Update content of existing instance
        editorView.dispatch({
            changes: { from: 0, to: editorView.state.doc.length, insert: initialContent }
        });
    } else {
        try {
            // Note: We use the extensions array directly.
            // The ?deps= flag above ensures html() uses the same state as EditorState.
            editorView = new EditorView({
                state: EditorState.create({
                    doc: initialContent,
                    extensions: [
                        basicSetup,
                        html(),
                        oneDark,
                        EditorView.lineWrapping,
                        EditorView.theme({
                            "&": { height: "100%", minHeight: "300px" },
                            ".cm-scroller": { overflow: "auto" },
                            ".cm-content": { padding: "10px 0" }
                        })
                    ]
                }),
                parent: target
            });
            console.log("CodeMirror instance created successfully");
        } catch (e) {
            console.error("CodeMirror Initialization Failed:", e);
            // Fallback UI so the user isn't stuck if CDN is being difficult
            target.innerHTML = `<textarea id="fallback-editor" class="form-control bg-dark text-white" style="height: 600px; font-family: monospace; border: none; outline: none;">${initialContent}</textarea>`;
        }
    }
}

window.loadFile = async function(path) {
    console.log("Attempting to load:", path);
    currentPath = path;

    const modalEl = document.getElementById('editorModal');
    if (window.bootstrap) {
        const bsModal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
        bsModal.show();

        // Force CM6 to recalculate size after modal animation
        const refresh = () => {
            if (editorView) {
                editorView.requestMeasure();
                editorView.focus();
            }
        };
        modalEl.addEventListener('shown.bs.modal', refresh, { once: true });
        // Small backup timeout in case 'shown' fires oddly
        setTimeout(refresh, 100);
    }

    try {
        const response = await fetch(`/jinja/get-template?path=${encodeURIComponent(path)}`);
        if (!response.ok) throw new Error("Fetch failed");

        const text = await response.text();
        initEditor(text);

        document.getElementById("current-filename").innerText = path;
        document.getElementById("save-btn").disabled = false;
    } catch (err) {
        console.error("loadFile Error:", err);
    }
};

window.saveFile = async function() {
    if (!currentPath) return;

    let content = "";
    if (editorView && editorView.state) {
        content = editorView.state.doc.toString();
    } else {
        const fallback = document.getElementById("fallback-editor");
        if (fallback) content = fallback.value;
    }

    const saveBtn = document.getElementById("save-btn");
    const originalText = saveBtn.innerText;

    saveBtn.disabled = true;
    saveBtn.innerText = "Saving...";

    try {
        const response = await fetch('/jinja/save-template', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: currentPath, content: content })
        });

        if (response.ok) {
            saveBtn.innerText = "Saved!";
            setTimeout(() => {
                saveBtn.innerText = originalText;
                saveBtn.disabled = false;
            }, 2000);
        }
    } catch (err) {
        console.error("Save error:", err);
        saveBtn.innerText = "Error!";
        setTimeout(() => {
            saveBtn.innerText = originalText;
            saveBtn.disabled = false;
        }, 2000);
    }
};

document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById('file-tree-container');

    console.log("Template files:", window.template_files);


    if (container && typeof window.template_files !== 'undefined') {
        container.innerHTML = createTreeHTML(window.template_files);

        container.addEventListener('click', (e) => {
            const btn = e.target.closest('.file-item');
            if (btn) {
                const path = btn.getAttribute('data-path');
                document.querySelectorAll('.file-item').forEach(i => i.classList.remove('active', 'bg-primary-subtle'));
                btn.classList.add('active', 'bg-primary-subtle');

                window.loadFile(path);
            }
        });
    }

    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', window.saveFile);
    }
});
