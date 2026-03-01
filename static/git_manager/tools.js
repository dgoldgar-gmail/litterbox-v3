/**
 * Handles the rendering and interaction for the Git Management UI.
 */
document.addEventListener('DOMContentLoaded', () => {
    const gitChangesContainer = document.getElementById('git-changes');
    const gitForm = document.getElementById('git-form');

    // Non-submit buttons
    const commitBtn = document.getElementById('commit');
    const pushBtn = document.getElementById('push');
    const diffBtn = document.getElementById('diff');
    const stagedBtn = document.getElementById('staged');
    const pullBtn = document.getElementById('pull');
    const checkoutBtn = document.getElementById('checkout');
    const resetBtn = document.getElementById('reset');

    // This data is injected into the window object by the template
    let changes = statusData["changes"] || { changes: [] };

    /**
     * Renders the list of changed files as checkboxes
     */
    function renderChanges() {
        if (!changes || changes.length === 0) {
            gitChangesContainer.innerHTML = '<div class="alert alert-info">No changes detected. Repository is clean.</div>';
            return;
        }

        /*
        console.log(statusData['branch'])
        console.log(statusData['is_dirty'])
        console.log(statusData['staged'])
        console.log(statusData['staged_diff'])
        console.log(statusData['unstaged'])
        console.log(statusData['unstaged_diff'])
        console.log(statusData['untracked'])
         */

        gitChangesContainer.innerHTML = ""; // clear previous content

        const ul = document.createElement("ul");
        ul.id = "git-changes";
        ul.classList.add("list-group");

        ul.appendChild(createDiffListHeaderRow())

        document.getElementById("title").innerHTML =
            `Manage GIT Repository (${statusData.branch})`;

        statusData.unstaged.forEach((change, index) => {
            const li = createDiffListItem("unstaged", change, index);
            ul.appendChild(li);
        });
        statusData.untracked.forEach((change, index) => {
            const li = createDiffListItem("untracked", change, index);
            ul.appendChild(li);
        });
        statusData.staged.forEach((change, index) => {
            const li = createDiffListItem("staged", change, index);
            ul.appendChild(li);
        });

        gitChangesContainer.appendChild(ul);

        renderDiff("Unstaged Changes", statusData['unstaged_diff'])
        renderDiff("Staged Changes", statusData['staged_diff'])

    }

    function createDiffListHeaderRow() {

        // --- Header row ---
        const headerLi = document.createElement("li");
        headerLi.classList.add("list-group-item", "d-flex", "align-items-center", "fw-bold");

        // Select All checkbox
        const selectAllCheckbox = document.createElement("input");
        selectAllCheckbox.type = "checkbox";
        selectAllCheckbox.classList.add("form-check-input", "me-3");
        selectAllCheckbox.id = "select-all-files";

        // Optional: clicking this checks/unchecks all file checkboxes
        selectAllCheckbox.addEventListener("change", (e) => {
            document.querySelectorAll(".file-checkbox").forEach(cb => {
                cb.checked = e.target.checked;
            });
        });

        // File path column
        const filePathSpan = document.createElement("span");
        filePathSpan.classList.add("flex-grow-1");
        filePathSpan.textContent = "File Path";

        // Status column
        const statusSpan = document.createElement("span");
        statusSpan.textContent = "Status";

        headerLi.appendChild(selectAllCheckbox);
        headerLi.appendChild(filePathSpan);
        headerLi.appendChild(statusSpan);

       return headerLi;
    }

    function createDiffListItem(type, change, index) {

        let change_type = null;
        let change_path = null;

        if ( type == "unstaged" ) {
            change_type = change.split(":")[0]
            change_path = change.split(":")[1].trim()
        } else if ( type == "untracked" ) {
            change_type = "A"
            change_path = change.trim()
        } else if ( type == "staged" ) {
            change_type = 'S'
            change_path = change.split(":")[1].trim()
        }

        const li = document.createElement("li");
        li.className = "list-group-item d-flex align-items-center";

        const checkbox = document.createElement("input");
        checkbox.className = "form-check-input me-3 file-checkbox";
        checkbox.type = "checkbox";
        checkbox.value = change_path;
        checkbox.dataset.status = change_type;
        checkbox.id = `file-${index}`;
        checkbox.checked = false;

        const label = document.createElement("label");
        label.className = "form-check-label d-flex justify-content-between w-100";
        label.setAttribute("for", `file-${index}`);

        const pathSpan = document.createElement("span");
        pathSpan.className = "text-truncate";
        pathSpan.style.maxWidth = "80%";
        pathSpan.title = change_path;
        pathSpan.textContent = change_path;

        const badgeSpan = document.createElement("span");

        badgeSpan.classList.add( "badge", "rounded")
        if ( change_type == "M" ) {
            badgeSpan.classList.add("bg-warning", "text-dark");
            badgeSpan.textContent = "modified";
        } else if ( change_type == "D" ) {
            badgeSpan.classList.add("bg-danger", "text-dark");
            badgeSpan.textContent = "deleted";
        } else if ( change_type == "A" ) {
            badgeSpan.classList.add("bg-success", "text-dark");
            badgeSpan.textContent = "added";
        } else if ( change_type == "S" ) {
            badgeSpan.classList.add("bg-info", "text-dark");
            badgeSpan.textContent = "staged";
        }

        label.appendChild(pathSpan);
        label.appendChild(badgeSpan);

        li.appendChild(checkbox);
        li.appendChild(label);

        return li;
    }

    /**
     * Commit
     */
    commitBtn.addEventListener('click', async (e) => {

        const message = prompt("Enter a commit message:", "Update via Web UI");
        if (message === null) {
            console.log("User cancelled the push.");
            return;
        }
        if (message.trim() === "") {
            alert("You must provide a commit message to proceed.");
            return;
        }

        const checkedBoxes = document.querySelectorAll('.file-checkbox:checked');
        const selectedFiles = Array.from(checkedBoxes).map(cb => ({
            path: cb.value,
            status: cb.dataset.status
        }));
        const payload = {
            files: selectedFiles,
            timestamp: new Date().toISOString()
        };
        try {
            const response = await fetch(`/git_manager/commit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (result.success) {
                console.log("Committed successfully");
                clearDiffResults();
                renderChanges();
            } else {
                alert("Error: " + (result.error || "Request failed"));
            }
        } catch (err) {
            console.error("Error sending file list:", err);
        }
    });

    pushBtn.addEventListener('click', async (e) => {

        if (!confirm("Push committed changes to origin/main?")) return;

        const payload = {
            timestamp: new Date().toISOString()
        };
        try {
            const response = await fetch(`/git_manager/push`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (result.success) {
                console.log("Pushed successfully");
                clearDiffResults();
                renderChanges();
            } else {
                alert("Error: " + (result.error || "Request failed"));
            }
        } catch (err) {
            console.error("Error sending file list:", err);
        }
    });

    /**
     * PULL
     */
    pullBtn.addEventListener('click', async () => {
        if (!confirm("Pull latest changes from origin/main?")) return;
        const payload = {
            timestamp: new Date().toISOString()
        };
        try {
            const response = await fetch(`/git_manager/pull`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            console.log(result)
            if (result.success) {
                console.log("Pulled successfully");
                clearDiffResults();
                renderChanges();
            } else {
                alert("Error: " + (result.error || "Request failed"));
            }
        } catch (err) {
            console.error("Error sending file list:", err);
        }
    });

    /**
     * CHECKOUT
     */
    checkoutBtn.addEventListener('click', async () => {
        if (!confirm("WARNING: This will delete uncommitted changes to the selected files. Proceed?")) return;

        const checkedBoxes = document.querySelectorAll('.file-checkbox:checked');
        const selectedFiles = Array.from(checkedBoxes).map(cb => ({
            path: cb.value,
            status: cb.dataset.status
        }));

        const payload = {
            files: selectedFiles,
            timestamp: new Date().toISOString()
        };

        try {
            const response = await fetch(`/git_manager/checkout`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            console.log(result)
            if (result.success) {
                console.log("Checked out successfully");
                clearDiffResults();
                renderChanges();
            } else {
                alert("Error: " + (result.error || "Request failed"));
            }
        } catch (err) {
            console.error("Error sending file list:", err);
        }
    });

    /**
     * RESET
     */
    resetBtn.addEventListener('click', async () => {
        if (!confirm("DANGER: This will delete all uncommitted and staged changes. Proceed?")) return;
        const payload = {
            timestamp: new Date().toISOString()
        };
        try {
            const response = await fetch(`/git_manager/reset`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            console.log(result)
            if (result.success) {
                console.log("Reset out successfully");
                clearDiffResults();
                renderChanges();
            } else {
                alert("Error: " + (result.error || "Request failed"));
            }
        } catch (err) {
            console.error("Error sending file list:", err);
        }
    });

    function clearDiffResults() {
        const container = document.getElementById('diff-results');
        container.innerHTML = '';
    }

    function renderDiff(type, rawOutput) {
        console.log(type)
        const container = document.getElementById(type.toLowerCase().replace(" ", "-"));

        if (!rawOutput) {
            container.innerHTML = '<div class="alert alert-info">No ' + type + ' to show.</div>';
            return;
        }

        console.log(rawOutput)
        const diffSplitIndex = rawOutput.indexOf('diff --git');
        console.log(diffSplitIndex)

        let headerText = "";
        let diffContent = "";

        if (diffSplitIndex !== -1) {
            headerText = rawOutput.substring(0, diffSplitIndex);
            diffContent = rawOutput.substring(diffSplitIndex);
        } else {
            // If there's no diff (e.g. an empty commit), just show the header
            headerText = rawOutput;
        }

        const fileDiffs = diffContent.split('\ndiff --git').filter(Boolean);
        let html = "<br><h3>" + type + "</h3><br>";
        fileDiffs.forEach(diff => {
            const fullDiff = 'diff --git' + diff;
            const lines = fullDiff.split('\n');

            // Find filename: Look for the b/filename in the first line
            const fileMatch = lines[0].match(/b\/(.+)$/);
            const fileName = fileMatch ? fileMatch[1] : "Multiple Files";

            html += `
                <div class="card mb-3 bg-transparent border-secondary shadow-sm">
                    <div class="card-header bg-dark text-info border-secondary py-1 d-flex justify-content-between">
                        <small class="font-monospace">${fileName}</small>
                    </div>
                    <div class="card-body p-0">
                        <pre class="m-0 p-2 small" style="overflow-x: auto; background-color: #0d1117; color: #c9d1d9;"><code>`;

            lines.forEach(line => {
                let color = 'inherit';
                // Simple color logic for Git diffs
                if (line.startsWith('+') && !line.startsWith('+++')) color = '#3fb950'; // Green
                else if (line.startsWith('-') && !line.startsWith('---')) color = '#f85149'; // Red
                else if (line.startsWith('@@')) color = '#d2a8ff'; // Purple

                const escapedLine = line
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;");

                html += `<div style="color: ${color}; white-space: pre;">${escapedLine || ' '}</div>`;
            });

            html += `</code></pre></div></div>`;
        });

        container.innerHTML = html;
    }

    renderChanges();

});
