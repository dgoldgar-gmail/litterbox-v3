

document.addEventListener('DOMContentLoaded', () => {

    const el = (tag, className = '', text = '', parent = null) => {
        const e = document.createElement(tag);
        if (className) e.className = className;
        if (text) e.textContent = text;
        if (parent) parent.appendChild(e);
        return e;
    };

    function getClassNamesFor(field, status) {
        const isReady = status === 'ready';

        if (field === "status") {
            return isReady
                ? 'badge border border-success text-success'
                : 'badge border border-danger text-danger';
        }

        if (field === "user") {
            return isReady
                ? 'rounded-circle bg-success me-2'
                : 'rounded-circle bg-danger me-2'
        }
    }

    function createSessionItem(name, details) {
        const li = el('li', 'list-group-item list-group-item-action bg-dark text-white border-secondary d-flex align-items-center py-2');

        const userCol = el('div', 'col-2 d-flex align-items-center', '', li);

        el('div', getClassNamesFor("user", details.status), '', userCol).style.cssText = 'width: 8px; height: 8px;';

        el('span', 'fw-bold', name, userCol);

        el('div', 'col-2 text-secondary small', details.created, li);

        el('div', 'col-2 text-info small', details.updated, li);

        el('div', 'col-3 text-truncate pe-2', details.reason, li);

        const statusCol = el('div', 'col-3 text-end', '', li);
        el('span', getClassNamesFor("status", details.status), details.status.toUpperCase(), statusCol);

        li.addEventListener('click', () => {
            if ( details.status === "locked" ) {
                console.log("Initiating unlock for..." + name)
                openSessionModal(name, details.status);
            } else {
                console.log(name + " already unlocked.")
                openSessionModal(name, details.status)

            }
        })


        return li;
    }

    function renderSessions() {
        const container = document.getElementById("sessions");
        container.replaceChildren(); // High-performance way to clear the list

        // Create Header Row
        const header = el('div', 'list-group-item bg-dark text-uppercase fw-bold text-secondary small d-flex border-secondary');
        const cols = ['User', 'Created', 'Updated', 'Reason', 'Status'];
        const widths = ['col-2', 'col-2', 'col-2', 'col-3', 'col-3 text-end'];

        cols.forEach((text, i) => {
            const colClass = widths[i];
            el('div', colClass, text, header);
        });

        container.appendChild(header);

        // Create Data Rows
        Object.entries(data).forEach(([name, details]) => {
            console.log(name, details)
            container.appendChild(createSessionItem(name, details));
        });
    }

    function openSessionModal(name, status) {
        const modalEl = document.getElementById('session-modal');

        // Check if there is an existing instance, otherwise create one
        let modal = bootstrap.Modal.getInstance(modalEl);
        if (!modal) {
            modal = new bootstrap.Modal(modalEl);
        }
        const body = document.getElementById('session-modal-body');
        const submitBtn = document.getElementById('session-modal-submit');
        const title = document.getElementById('session-modal-title');

        if ( status === "ready" ) {
            title.textContent = `Synch photos for: ${name}`;
        } else {
            title.textContent = `Authenticate: ${name}`;
        }

        body.innerHTML = '';

        if ( status === "ready" ) {
            title.textContent = `Synch photos for: ${name}`;
            el('p', '', 'This session is ready. Would you like to synch photos?', body);

            submitBtn.textContent = 'Synch';
            submitBtn.onclick = () => synchPhotos(modal);
        } else if  (status === 'awaiting_2fa') {
            title.textContent = `Authenticate: ${name}`;
            // State: We need the 6-digit code
            el('p', '', 'Enter the 6-digit code sent to your Apple device:', body);
            const input = el('input', 'form-control bg-dark text-white border-secondary text-center fs-4', '', body);
            input.type = 'text';
            input.placeholder = '000000';
            input.maxLength = 6;

            submitBtn.textContent = 'Verify Code';
            submitBtn.onclick = () => handleAuthSubmit(name, 'mfa', input.value, modal);
        } else {
            title.textContent = `Authenticate: ${name}`;
            // State: Locked or Initial
            el('p', '', 'This session is locked. Would you like to request an MFA code from Apple?', body);

            submitBtn.textContent = 'Request Code';
            submitBtn.onclick = () => handleAuthSubmit(name, 'login', null, modal);
        }
        modal.show();
    }

    async function handleAuthSubmit(user, action, code, modalInstance) {
        const endpoint = action === 'mfa' ? '/icloud/auth/mfa' : '/icloud/auth/login';

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user, code })
            });

            const result = await response.json();

            // KEY FIX: Update the local 'data' variable with fresh state from Python
            if (result.sessions) {
                data = result.sessions;
            }

            if (result.status === 'NEEDS_MFA') {
                modalInstance.hide();
                // Wait for backdrop to clear before re-opening for the code input
                setTimeout(() => {
                    openAuthModal(user, 'awaiting_2fa');
                    renderSessions(); // Update list to show 'AWAITING_2FA' badge
                }, 300);

            } else if (result.status === 'READY') {
                modalInstance.hide();
                renderSessions(); // This will now find 'READY' in the updated 'data'
            } else {
                alert('Error: ' + result.message);
            }
        } catch (err) {
            console.error('Auth failed', err);
        }
    }

    async function synchPhotos(modalInstance) {
        // TODO:  maybe kick off the synch and show progress?
        console.log("Call synch photos here...")
        modalInstance.hide();
    }

    renderSessions()
});