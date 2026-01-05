
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

window.loadFile = async function(path) {
    console.log("Attempting to load:", path);
    currentPath = path;


    try {
        const response = await fetch(`/jinja/get-generated-file?path=${encodeURIComponent(path)}`);
        if (!response.ok) throw new Error("Fetch failed");

        const text = await response.text();
        //initEditor(text);
        console.log(text)
        document.getElementById("preview-box").innerText = text;

        //document.getElementById("current-filename").innerText = path;


    } catch (err) {
        console.error("loadFile Error:", err);
    }


    /*
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
    */

};


document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById('file-tree-container');

    console.log("Generated files:", generated_files);


    if (container && typeof generated_files !== 'undefined') {
        container.innerHTML = createTreeHTML(generated_files);

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
});
