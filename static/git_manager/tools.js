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

        let html = '<ul id="git-changes" class="list-group">';
        changes.forEach((change, index) => {
            const statusClass = getStatusBadgeClass(change.working_tree || change.index);
            const statusText = (change.working_tree !== 'unchanged') ? change.working_tree : change.index;

            html += `
                <li class="list-group-item d-flex align-items-center">

                    <input class="form-check-input me-3 file-checkbox"
                               type="checkbox"
                               value="${change.path}"
                               data-status="${statusText}"
                               id="file-${index}"
                               checked>
                    <label class="form-check-label d-flex justify-content-between w-100" for="file-${index}">
                        <span class="text-truncate" style="max-width: 80%;" title="${change.path}">
                            ${change.path}
                        </span>
                        <span class="badge ${statusClass}">${statusText}</span>
                    </label>
                </li>
            `;
        });
        html += '</ul>';
        gitChangesContainer.innerHTML = html;
    }

    function getStatusBadgeClass(status) {
        switch (status.toLowerCase()) {
            case 'modified': return 'bg-warning text-dark';
            case 'added': return 'bg-success';
            case 'untracked': return 'bg-info text-dark';
            case 'deleted': return 'bg-danger';
            case 'renamed': return 'bg-primary';
            default: return 'bg-secondary';
        }
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
     * DIFF
     */
    diffBtn.addEventListener('click', async () => {
        const checkedBoxes = document.querySelectorAll('.file-checkbox:checked');
        const selectedFiles = Array.from(checkedBoxes).map(cb => cb.value);
        const payload = {
            files: selectedFiles,
            timestamp: new Date().toISOString()
        };
        try {
            const response = await fetch(`/git_manager/diff`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (result.success) {
                renderDiffResults(result.diff_data);
                if (result.status_data) {
                    renderChanges();
                }
            } else {
                alert("Error: " + (result.error || "Request failed"));
            }
        } catch (err) {
            console.error("Error sending file list:", err);
        }
    });


    /**
     * Staged
     */
    stagedBtn.addEventListener('click', async () => {
        try {
            const response = await fetch(`/git_manager/staged`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const result = await response.json();
            if (result.success) {
                renderCommitDiff(result.staged_data);
                if (result.status_data) {
                    renderChanges();
                }
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
        if (!confirm("WARNING: This will delete all uncommitted changes. Proceed?")) return;
        const payload = {
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

    function renderCommitDiff(rawOutput) {
        const container = document.getElementById('diff-results');
        if (!rawOutput) {
            container.innerHTML = '<div class="alert alert-info">No staged changes to show.</div>';
            return;
        }

        const diffSplitIndex = rawOutput.indexOf('\ndiff --git');

        let headerText = "";
        let diffContent = "";

        if (diffSplitIndex !== -1) {
            headerText = rawOutput.substring(0, diffSplitIndex);
            diffContent = rawOutput.substring(diffSplitIndex);
        } else {
            // If there's no diff (e.g. an empty commit), just show the header
            headerText = rawOutput;
        }

        /*
        //Could rebuild this so it just shows the list of commits or something...
        let html = `
            <div class="card mb-3 bg-dark-subtle border-secondary">
                <div class="card-header bg-dark text-muted small">Commit Metadata</div>
                <div class="card-body font-monospace small text-light">
                    ${headerText.trim().replace(/\n/g, '<br>')}
                </div>
            </div>
            <h2 class="h5 mb-3 text-secondary">Committed Changes</h2>
        `;
        */

        const fileDiffs = diffContent.split('\ndiff --git').filter(Boolean);
        let html = "<br><h3>Staged Changes</h3><br>";
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

    function renderDiffResults(diffData) {
        const container = document.getElementById('diff-results');

        if (!diffData || diffData.length === 0) {
            container.innerHTML = '<div class="alert alert-warning">No diff data returned.</div>';
            return;
        }

        let html = "<br><h3>Uncommitted Changes</h3><br>";

        diffData.forEach(res => {
            if (res.stdout) {
                // TODO:  This could fail because the file is deleted or something?
                const fileName = res.stdout.split('\n')[0].split(" ")[3].replace("b/","")
                // Escape HTML and split into lines to add color classes
                const lines = res.stdout.split('\n').map(line => {
                    let className = 'diff-line';

                    if (line.startsWith('+') && !line.startsWith('+++')) {
                        className += ' diff-added';
                    } else if (line.startsWith('-') && !line.startsWith('---')) {
                        className += ' diff-removed';
                    } else if (line.startsWith('@@')) {
                        className += ' diff-header';
                    }
                    return `<div class="${className}">${escapeHtml(line)}</div>`;
                }).join('');
                html += `
                    <div class="card mb-3">
                        <div class="card-header py-1 bg-primary-subtle text-white border-secondary shadow-sm">
                            <medium>Git Diff Output - ${fileName}</medium>
                        </div>
                        <div class="card-body p-0"> <pre class="m-0" style="white-space: pre-wrap; font-size: 0.85rem;"><code>${lines}</code></pre>
                        </div>
                    </div>`;
            }
        });

        container.innerHTML = html;
        container.scrollIntoView({ behavior: 'smooth' });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    renderChanges();

});
