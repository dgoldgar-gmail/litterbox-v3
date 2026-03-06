/**
 * Handles the rendering and interaction for the Git Management UI.
 */
document.addEventListener('DOMContentLoaded', () => {
    const gitChangesContainer = document.getElementById('git-changes');
    const gitForm = document.getElementById('git-form');

    // Non-submit buttons
    const commitBtn = document.getElementById('commit');
    const pushStandardBtn = document.getElementById('push-standard');
    const pushForceBtn = document.getElementById('push-force');

    const squashBtn = document.getElementById('squash')
    const checkoutBranchBtn = document.getElementById('branch-checkout')
    const createBranchBtn = document.getElementById('branch-create')

    const resetSoftBtn = document.getElementById('reset-soft')
    const resetFilesBtn = document.getElementById('reset-files')
    const resetHardBtn = document.getElementById('reset-hard')

    const checkStaged = document.getElementById("check-staged")
    const checkUnstaged = document.getElementById("check-unstaged")
    const checkCommitted = document.getElementById("check-committed")
    const checkLog = document.getElementById("check-log")

    /**
     * Renders the list of changed files as checkboxes
     */
    function renderChanges() {

        gitChangesContainer.innerHTML = ""; // clear previous content

        const ul = document.createElement("ul");
        ul.id = "git-changes";
        ul.classList.add("list-group");

        ul.appendChild(createDiffListHeaderRow())

        document.getElementById("title").innerHTML =
            `Manage GIT Repository (${data.branch})`;

        data.unstaged.forEach((change, index) => {
            const li = createDiffListItem("unstaged", change, index);
            ul.appendChild(li);
        });
        data.untracked.forEach((change, index) => {
            const li = createDiffListItem("untracked", change, index);
            ul.appendChild(li);
        });
        data.staged.forEach((change, index) => {
            const li = createDiffListItem("staged", change, index);
            ul.appendChild(li);
        });

        gitChangesContainer.appendChild(ul);

        renderLogs()
        renderDiff("Unstaged Changes", data['unstaged_diff'])
        renderDiff("Staged Changes", data['staged_diff'])
        renderDiff("Committed Changes", data['committed_diff'])
    }

    function createDiffListHeaderRow() {

        // --- Header row ---
        const headerLi = document.createElement("li");
        headerLi.classList.add("list-group-item", "d-flex", "align-items-center", "fw-bold", "z-3", "sticky-top", "list-group-item-info", "text-white",);

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

    function clearDiff(container_name) {
        const container = document.getElementById(container_name);
        container.innerHTML = '';
    }

    function clearDiffs() {
        containers = ["staged-changes", "unstaged-changes", "committed-changes", "git-log-section"]
        containers.forEach(container_name => {
            clearDiff(container_name)
        })
    }

    function renderDiff(type, rawOutput) {

        let checkOptionName = "check-" +  type.toLowerCase().split(" ")[0]
        let checkOption = document.getElementById( checkOptionName)
        let containerName = type.toLowerCase().replace(" ", "-")
        if ( ! checkOption.checked ) {
            console.log(type, "is not enabled for display.")
            clearDiff(containerName)
            return;
        }

        console.log(type, "is enabled for display.")

        console.log(rawOutput)

        const container = document.getElementById(containerName);

        if (!rawOutput) {
            container.innerHTML = '<div class="alert alert-info">No ' + type + ' to show.</div>';
            return;
        } else if ( rawOutput == "No upstream branch found.") {
            container.innerHTML = '<div class="alert alert-info">No upstream branch found.</div>';
            return;
        }

        //console.log(rawOutput)
        const diffSplitIndex = rawOutput.indexOf('diff --git');
        //console.log(diffSplitIndex)

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

    async function issueGitCommand(command, payload, onSuccess, onError) {
        try {
            const response = await fetch(`/git_manager/${command}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (result.success) {
                data = result['status_data']
                onSuccess(result)
                clearDiffs();
                renderChanges();
            } else {
                onError(result.error)
            }
        } catch (err) {
            console.error("Error sending file list:", err);
        }
    }

    commitBtn.addEventListener('click', async (e) => {

        let message = await showGenericModal({
            mode: 'git-commit-message',
            title: 'Commit Changes'
        });
        if (  message === null  || message.trim() === "" ) {
            await showGenericModal('ok', 'You must provide a commit message to proceed!')
            return;
        }

        const checkedBoxes = document.querySelectorAll('.file-checkbox:checked');
        const selectedFiles = Array.from(checkedBoxes).map(cb => ({
            path: cb.value,
            status: cb.dataset.status
        }));
        const payload = {
            files: selectedFiles,
            message: message,
            timestamp: new Date().toISOString()
        };
        issueGitCommand("commit", payload, (result) => {
            console.log(result)
            const commit_result = result['commit_result']
            showGenericModal({
                mode: 'ok',
                title: 'Committed successfully!',
                info: ["author:  " + commit_result['author'],
                       "hash:  "   + commit_result['hash'],
                       "message: " + commit_result['message']
                ]
            } )
        }, (error) => {
            showGenericModal({ mode:'ok', title: "Error: " + error } )
        });
    });

    squashBtn.addEventListener('click', async () => {
        let message = await showGenericModal({ mode: 'git-commit-message', title: 'Squash changes' } );
        if (  message === null  || message.trim() === "" ) {
            await showGenericModal( { mode: 'ok', title: 'You must provide a commit message to proceed!' } )
            return;
        }

        const payload = {
            timestamp: new Date().toISOString(),
            message: message
        };
        issueGitCommand("squash", payload, (result) => {
            console.log(result);
            showGenericModal({
                mode: 'ok',
                title: 'Squashed successfully!',
                info: [
                    'History rewrite completed.',
                    'Use the force push button to continue.',
                ]
            } )
        }, (error) => {
            showGenericModal({ mode: 'ok', title: "Error: " + error })
        });
    });

    resetSoftBtn.addEventListener('click', async () => {
        callReset("soft")
    });

    resetFilesBtn.addEventListener('click', async () => {
        callReset("files")
    });

    resetHardBtn.addEventListener('click', async () => {
        callReset("hard")
    });

    function callReset(mode) {

        genericModal({
            mode: 'ok',
            title: 'Reset not yet implemented!'
        })

        const payload = {
            timestamp: new Date().toISOString()
        };

        if ( mode == "files" ) {
            const selectedFiles = Array.from(document.querySelectorAll('.file-checkbox:checked'))
                .map(cb => cb.value);
            payload['mode'] = "files"
            payload['files'] = selectedFiles
            // TODO:  Each of these confirms should get replaced with genericModal...
            if (!confirm("Reset changes to files?", selectedFiles )) return;
        } else if ( mode == "hard" ) {
            payload['mode'] = "hard"
            if (!confirm("Reset all?" )) return;
        } else {
            payload['mode'] = "soft"
            if (!confirm("Unstage all changes?" )) return;
        }
        console.log("I'd issue", "reset", payload)


        /* TODO:  Issue dangerous git commands...
        issueGitCommand("reset", payload, (result) => {
            //console.log("Committed successfully");
            // TODO:  generic ok modal...
        }, (error) => {
            alert("Error: " + error);
        });
         */
    }

    pushStandardBtn.addEventListener('click', async (e) => {
        callPush(false)
    });

    pushForceBtn.addEventListener('click', async (e) => {
        callPush(true)
    });

    async function callPush(force) {
        let pushType = "standard-push"
        if ( force ) {
            pushType = "force-push"
        }

        if ( ! await showGenericModal({ mode: 'confirm-push', title: `Confirm ${pushType} Push` }) ) return;

        const payload = {
            timestamp: new Date().toISOString(),
            force: force
        };
        issueGitCommand("push", payload, (result) => {
            console.log(result)
            const push_results = result['push_results'][0]
            console.log(push_results)
            showGenericModal({
                mode: 'ok',
                title: 'Pushed successfully!',
                info: [
                    "branch: " + push_results['branch'],
                    "forced: " + push_results['forced'],
                    "success: " + push_results['success'],
                    "summary: " + push_results['summary']
                ]
            } )
        }, (error) => {
            showGenericModal({ mode: 'ok', title: "Error: " + error } )
        });
    }

    checkoutBranchBtn.addEventListener('click', async (e) => {
        callCheckoutBranch(false)
    });

    createBranchBtn.addEventListener('click', async (e) => {
        callCheckoutBranch(true)
    });

    async function populateBranchDropdown() {
        const dropdown = document.getElementById('branch-dropdown');

        dropdown.innerHTML = ''; // Clear old ones
        data['branches'].forEach(branch => {
            const opt = document.createElement('option');
            opt.value = branch;
            opt.textContent = branch;
            dropdown.appendChild(opt);
        });
    }

    async function showGenericModal({mode, title, message, info= []}) {

        return new Promise((resolve) => {
            const modalEl = document.getElementById('selection-modal');
            const confirmBtn = document.getElementById('confirm-button');

            const modalHeader = modalEl.querySelector('.modal-header');
            const modalFooter = modalEl.querySelector('.modal-footer');

            // Probably move this stuff for resetting the modal to it's own method
            const cancelBtn = modalEl.querySelector('.modal-footer [data-bs-dismiss="modal"]');
            [ 'modal-text-group', 'branch-select-group', 'message-input-group', 'modal-info-group' ].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.classList.add('d-none');
            });

            document.getElementById('modal-text-content').classList.remove('text-danger', 'text-success', 'text-info');

            document.getElementById('modal-text-content').innerHTML = "";
            document.getElementById('modal-info-content').innerHTML = "";

            confirmBtn.textContent = "Confirm";
            confirmBtn.className = "btn btn-primary"; // Reset color
            cancelBtn.classList.remove('d-none');
            if (modalHeader) modalHeader.classList.remove('border-0');
            if (modalFooter) modalFooter.classList.remove('border-0');

            document.getElementById('generic-modal-title').textContent = title;

            if (mode === 'ok') {
                if (modalHeader) modalHeader.classList.add('border-0');
                if (modalFooter) modalFooter.classList.add('border-0');
                document.getElementById('modal-text-group').classList.remove('d-none');
                document.getElementById('modal-text-content').textContent = message;
                confirmBtn.textContent = "OK";
                cancelBtn.classList.add('d-none');

                if (info && info.length > 0) {
                    const infoGroup = document.getElementById('modal-info-group');
                    const infoContent = document.getElementById('modal-info-content');
                    infoGroup.classList.remove('d-none');
                    infoContent.innerHTML = info.join('<br>');
                }
            } else if (mode === 'confirm') {
                document.getElementById('modal-text-group').classList.remove('d-none');
                document.getElementById('modal-text-content').textContent = message;
            } else if (mode === 'branch-select') {
                document.getElementById('branch-select-group').classList.remove('d-none');
                populateBranchDropdown();
            } else if (mode === 'branch-create') {
                document.getElementById('message-label').textContent = "Branch Name";
                document.getElementById('message-input-group').classList.remove('d-none');
                document.getElementById('message-input').placeholder = "e.g. test-branch";
            } else if (mode === 'git-commit-message') {
                document.getElementById('message-label').textContent = "Commit Message";
                document.getElementById('message-input-group').classList.remove('d-none');
                const input = document.getElementById('message-input');
                input.value = "";
                input.placeholder = "Enter commit message...";
            } else if (mode == 'confirm-push') {
                document.getElementById('modal-text-group').classList.remove('d-none');
                if (title.toLowerCase().includes("force")) {
                    document.getElementById('modal-text-content').textContent = message || "Are you sure you want to force push?";
                    document.getElementById('modal-text-content').classList.add('text-danger');
                    confirmBtn.className = "btn btn-danger"; // Visual warning for force push
                } else {
                    document.getElementById('modal-text-content').textContent = message || "Push changes to remote?";
                }
            }
            const modalInstance = new bootstrap.Modal(modalEl);
            confirmBtn.onclick = () => {
                let result = true;
                if (mode === 'branch-select') result = document.getElementById('branch-dropdown').value;
                if (mode === 'branch-create' || mode === 'git-commit-message') {
                    result = document.getElementById('message-input').value.trim();
                }
                modalInstance.hide();
                resolve(result);
            };
            modalEl.addEventListener('hidden.bs.modal', () => resolve(null), { once: true });
            modalInstance.show();
        });
    }

    async function callCheckoutBranch(create) {
        let selectedBranch = ""; // Renamed for clarity

        if (create) {
            selectedBranch = await showGenericModal({ mode: 'branch-create', title: 'Create Branch' } );
        } else {
            selectedBranch = await showGenericModal({ mode: 'branch-select', title: 'Checkout Branch' } );
        }

        // Only proceed if we got a value (not null/empty)
        if (selectedBranch) {
            const payload = {
                timestamp: new Date().toISOString(),
                branch_name: selectedBranch, // Changed from branchName to selectedBranch
                create: create
            };

            issueGitCommand("checkout", payload, (result) => {
                console.log(result)
                showGenericModal({
                    mode: 'ok',
                    title: 'Checked out successfully!',
                    info: [ 'Switched to branch ' + selectedBranch ]
                } )
            }, (err) => {
                showGenericModal( { mode: 'ok', title: "Error: " + error } )
            });
        }
    }

    function renderLogs( ) {
        let logs = data['log']
        let checkOptionName = "check-log"
        let checkOption = document.getElementById( checkOptionName)
        let containerName = "git-log-section"
        if ( ! checkOption.checked ) {
            console.log("Log is not enabled for display.")
            clearDiff(containerName)
            return;
        }

        console.log("Rendering logs", logs)
        const container = document.getElementById(containerName);

        const header = document.createElement('h3');
        header.className = "d-flex justify-content-between align-items-center mb-3 mt-2";
        header.textContent = "Git Log";

        const countBadge = document.createElement('span');
        countBadge.className = "badge rounded-pill bg-secondary small";
        countBadge.style.fontSize = "0.8rem";
        countBadge.textContent = `${logs.length} commits`;
        header.appendChild(countBadge);

        const ul = document.createElement('ul');
        ul.className = 'git-log-list list-group';

        logs.forEach(log => {
            ul.appendChild(createLogListItem(log));
        });

        container.replaceChildren(header, ul);

    }

    function createLogListItem(commit, index) {
        const { hash, author, date, message, refs } = commit;

        const li = document.createElement("li");
        li.className = "list-group-item list-group-item-action d-flex align-items-center py-2 px-3";
        li.style.gap = "15px";
        li.dataset.hash = hash;

        // 1. Hash (Left)
        const hashSpan = document.createElement("span");
        hashSpan.className = "badge bg-secondary-subtle text-secondary font-monospace border";
        hashSpan.style.width = "85px";
        hashSpan.textContent = hash;

        // 2. Author
        const authorSpan = document.createElement("span");
        authorSpan.className = "text-muted text-truncate";
        authorSpan.style.width = "120px";
        authorSpan.textContent = author;

        // 3. Message + Refs (The "Meat")
        const msgContainer = document.createElement("div");
        msgContainer.className = "flex-grow-1 text-truncate d-flex align-items-center gap-2";

        // Add the message text
        const msgText = document.createElement("span");
        msgText.className = "fw-medium";
        msgText.textContent = message;
        msgContainer.appendChild(msgText);

        // Add Ref Badges if they exist
        if (refs && refs.length > 0) {
            refs.forEach(refName => {
                const refBadge = document.createElement("span");
                // Highlight 'origin/' refs differently if you like
                const isRemote = refName.includes('origin/');
                refBadge.className = `badge ${isRemote ? 'bg-success-subtle text-success' : 'bg-primary-subtle text-primary'} border small`;
                refBadge.style.fontSize = "0.7rem";
                refBadge.textContent = refName;
                msgContainer.appendChild(refBadge);
            });
        }

        // 4. Date (Right)
        const dateSpan = document.createElement("span");
        dateSpan.className = "text-muted small text-end";
        dateSpan.style.width = "140px";
        dateSpan.textContent = date;

        li.append(hashSpan, authorSpan, msgContainer, dateSpan);
        return li;
    }


    checkStaged.addEventListener("change", () => {
            renderChanges();
    });

    checkUnstaged.addEventListener("change", () => {
        renderChanges();
    });

    checkCommitted.addEventListener("change", () => {
        renderChanges();
    });

    checkLog.addEventListener("change", () => {
        renderLogs();
    });

    renderChanges();

});
