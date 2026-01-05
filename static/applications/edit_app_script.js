
if (window.location.protocol === 'file:') {
    console.warn("Warning: This page is being loaded directly from your file system. Jinja2 templating will not work. Please run the Flask server (python app.py) and access the application via its HTTP address, e.g., http://YOUR_SERVER_IP:5000/ (like http://192.168.50.14:5000/).");
}

const dockerArgList = document.getElementById('dockerArgList');

const cancelModalContainerArgButton = document.getElementById('cancelModalContainerArgButton');
const closeModalContainerArgButton = document.getElementById('closeModalContainerArgButton');
const dockerContainerArgsListElement = document.getElementById('dockerContainerArgList');

const cancelModalPostStartupCmdButton = document.getElementById('cancelModalPostStartupCmdButton');
const closeModalPostStartupCmdButton = document.getElementById('closeModalPostStartupCmdButton');
const  dockerPostStartupCmdList = document.getElementById('dockerPostStartupCmdList');

const dockerEntrypointListElement = document.getElementById('dockerEntrypointList');
const cancelModalEntrypointButton = document.getElementById('cancelModalEntrypointButton');
const closeModalEntrypointButton = document.getElementById('closeModalEntrypointButton');

const cancelModalButton = document.getElementById('cancelModalButton');
const closeModalButton = document.getElementById('closeModalButton');

const argTypeRadios = document.querySelectorAll('input[name="argType"]');


// JSON Preview modal-related variables
const previewButton = document.getElementById('previewButton');
const jsonPreviewModal = document.getElementById('jsonPreviewModal');
const jsonOutput = document.getElementById('jsonOutput');
const copyJsonButton = document.getElementById('copyJsonButton');
const saveButton = document.getElementById('saveButton');

docker = app['docker'] || { docker: {} };
currentArgs = docker['args'] || [];
currentEntrypoint = docker['entrypoint'] || [];
currentContainerArgs = docker['container_args'] || [];
currentPostStartupCmds = docker['post-startup-cmds'] || [];

// --- Helper Functions ---

// This function is for showing any modal using the Bootstrap 5 API
function showModal(modalElement, inputElement = null) {
    if (!modalElement || !modalElement.classList.contains('modal')) {
        console.error(`Error: The modal element is undefined, null, or does not have the 'modal' class. Bootstrap modals require this class. Element: `, modalElement);
        return;
    }
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    if (inputElement) {
        inputElement.value = '';
    }
}

// This function is for hiding any modal using the Bootstrap 5 API
function hideModal(modalElement) {
    const modal = bootstrap.Modal.getInstance(modalElement);
    if (modal) {
        modal.hide();
    }
}

// Helper to escape HTML for display
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) {
        return map[m];
    });
}

// A custom alert function using a Bootstrap modal for consistency
function showAlert(message) {
    // Dynamically create a modal for the alert
    const modalId = 'customAlertModal';
    const existingModal = document.getElementById(modalId);
    if (existingModal) {
        existingModal.remove();
    }
    const alertModalHtml = `
        <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="customAlertModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="customAlertModalLabel">Notification</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        ${message}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Okay</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = alertModalHtml.trim();
    const alertModalElement = tempDiv.firstChild;
    document.body.appendChild(alertModalElement);

    const bsAlertModal = new bootstrap.Modal(alertModalElement);
    bsAlertModal.show();
}

// A custom confirm function using a Bootstrap modal for consistency
function showConfirm(message, onConfirm) {
    // Dynamically create a modal for the confirmation
    const modalId = 'customConfirmModal';
    const existingModal = document.getElementById(modalId);
    if (existingModal) {
        existingModal.remove();
    }
    const confirmModalHtml = `
        <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="customConfirmModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="customConfirmModalLabel">Confirmation</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        ${message}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="confirmActionBtn">Confirm</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = confirmModalHtml.trim();
    const confirmModalElement = tempDiv.firstChild;
    document.body.appendChild(confirmModalElement);

    const bsConfirmModal = new bootstrap.Modal(confirmModalElement);
    const confirmActionBtn = confirmModalElement.querySelector('#confirmActionBtn');

    confirmActionBtn.addEventListener('click', () => {
        onConfirm();
        bsConfirmModal.hide();
    });

    bsConfirmModal.show();
}

// --- Rendering Functions ---

function createItemRenderer(listType) {
    return (item, index) => {
        switch (listType) {
            case 'docker-args':
                if (item.length === 2) { // Use strict equality (===)
                    argTypeDisplay = item[0];
                    argValue = item[1];
                } else {
                    argValue = item[0];
                    argTypeDisplay = null; // Use null instead of None
                }

                return `
                    <input type="checkbox" data-index="${index}">
                    <div class="d-flex align-items-center">
                        <span class="badge bg-secondary me-2">${argTypeDisplay !== null ? argTypeDisplay : ''}</span>
                        <span>${argValue}</span>
                    </div>
                `;
            case 'post-startup-cmds':
                return `
                    <input type="checkbox" data-index="${index}" data-key="${escapeHtml(item.key)}">
                    <span class="text-break">${escapeHtml(item.value)}</span>
                `;
            case 'entrypoint':
            case 'container-args':
            default:
                return `
                    <input type="checkbox" data-index="${index}">
                    <span class="text-break">${escapeHtml(item)}</span>
                `;
        }
    };
}

function renderList(listElement, dataArray, type, x) {
    listElement.innerHTML = '';

    itemRenderer = createItemRenderer(type)
    if (!Array.isArray(dataArray) || dataArray.length === 0) {
        const emptyListItem = document.createElement('li');
        emptyListItem.className = 'list-group-item text-center text-muted';
        emptyListItem.id = type + '-placeholder';
        emptyListItem.textContent = 'No ' + type + ' added yet.';
        listElement.appendChild(emptyListItem);
        return;
    }
    
    dataArray.forEach((item, index) => {
        const listItem = document.createElement('li');
        listItem.className = 'list-group-item d-flex align-items-center gap-2';
        listItem.innerHTML = itemRenderer(item, index);
        listElement.appendChild(listItem);
    });
}

function preProcessArgsList(args) {
    const processedList = [];
    let i = 0;
    while (i < args.length) {
        const currentArg = String(args[i]);

        if (currentArg.startsWith("--user") || currentArg.startsWith("--device")) {
            processedList.push([currentArg]);
            i += 1;
        } else if (currentArg.startsWith('-')) {
            // This is the key fix for flags
            if (i + 1 < args.length) {
                processedList.push([currentArg, String(args[i + 1])]); // Added String() conversion
                i += 2;
            } else {
                // Handle flags at the end of the list
                processedList.push([currentArg]);
                i += 1;
            }
        } else {
            processedList.push([currentArg]);
            i += 1;
        }
    }
    return processedList;
}

function renderArgList() {
    const processedArgs = preProcessArgsList(currentArgs);

    renderList(
        dockerArgList,
        processedArgs,
        'docker-args'
    );
    updateJsonInput('dockerArgsJsonInput', processedArgs);
}

function renderEntrypointList() {
    renderList(
        dockerEntrypointListElement,
        currentEntrypoint,
        'entrypoint'
    );
    updateJsonInput('dockerEntrypointJsonInput', currentEntrypoint);
}

function renderContainerArgsList() {
    renderList(
        dockerContainerArgsListElement,
        currentContainerArgs
    );
    updateJsonInput('dockerContainerArgsJsonInput', currentContainerArgs);
}

function renderPostStartupCmdsList() {
    renderList(
        dockerPostStartupCmdList,
        currentPostStartupCmds,
        'post-startup-cmds'
    );
    updateJsonInput('dockerPostStartupCmdsJsonInput', currentPostStartupCmds);
}

function updateJsonInput(elementId, data) {
    const inputElement = document.getElementById(elementId);
    if (inputElement) {
        inputElement.value = JSON.stringify(data);
    }
}

function getApplicationJsonFromDiv(divId) {
    const mainDiv = document.getElementById(divId);
    if (!mainDiv) {
        console.error(`Could not find a div with the ID: ${divId}`);
        return null;
    }

    const applicationData = {};
    const inputs = mainDiv.querySelectorAll('input');
    inputs.forEach(input => {
        if (input.name) {
            if (input.type === 'checkbox') {
                applicationData[input.name] = input.checked;
            } else {
                applicationData[input.name] = input.value;
            }
        }
    });

    return applicationData;
}

function getCheckedHosts() {
    const hostCheckboxes = document.querySelectorAll('input[name="hosts"]');
    const checkedHosts = Array.from(hostCheckboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);
    return checkedHosts;
}

function getArrayFromList(listId, isArgs=false) {
    const listElement = document.getElementById(listId);
    if (!listElement) {
        console.error(`Could not find a list with the ID: ${listId}`);
        return null;
    }
    const listItems = listElement.querySelectorAll('li');
    let values = []
    if ( isArgs ) {
        listItems.forEach(item => {
            values = [...values,...item.textContent.trim().split(/\s+/)]
        });
    } else {
        values = Array.from(listItems)
            .filter(item => !item.id.includes('placeholder'))
            .map(item => item.textContent.trim());
    }
    return values;
}

// --- Main Form Logic ---
function getApplicationJsonFromForm() {
    const application_json = getApplicationJsonFromDiv("main-fields");
    application_json.name = document.getElementById('name').value;
    application_json.live = document.getElementById('live').checked;
    application_json.managed = document.getElementById('managed').checked;
    application_json.notify_version = document.getElementById('notify_version').checked;
    application_json.hosts = getCheckedHosts();

    const docker_config = {};
    docker_config.image = document.getElementById('docker_image').value;
    application_json.docker = docker_config;

    docker_config.args = getArrayFromList('dockerArgsList', true);
    docker_config.entrypoint = getArrayFromList('dockerEntrypointList');
    docker_config.container_args = getArrayFromList('dockerContainerArgList');
    docker_config.post_startup_cmds = getArrayFromList('dockerPostStartupCmdsList');

    return application_json;
}

// --- Modal Logic ---

function updateArgPlaceholder() {
    const selectedType = document.querySelector('input[name="argType"]:checked').value;
    if (selectedType === 'volume') {
        argValueInput.placeholder = '/host/path:/container/path';
    } else if (selectedType === 'env') {
        argValueInput.placeholder = 'KEY=VALUE';
    } else if (selectedType === 'add-host') {
        argValueInput.placeholder = 'hostname:IP_address';
    } else if (selectedType === 'device') {
        argValueInput.placeholder = '/dev/device:/dev/device';
    } else { // freeform
        argValueInput.placeholder = 'any_freeform_argument';
    }
}

function addArgumentFromModal() {
    const selectedType = document.querySelector('input[name="argType"]:checked').value;
    const value = argValueInput.value.trim();
    if (!value) {
        showAlert('Please enter a value for the argument.');
        return;
    }
    currentArgs.push({ type: selectedType, value: value });
    renderArgList();
    hideModal(addArgModal);
}

function addEntrypointFromModal() {
    const value = entrypointValueInput.value.trim();
    if (!value) {
        showAlert('Please enter an entrypoint command.');
        return;
    }
    currentEntrypoint.push(value);
    renderEntrypointList();
    hideModal(addEntrypointModal);
}

function addContainerArgFromModal() {
    const value = containerArgValueInput.value.trim();
    if (!value) {
        showAlert('Please enter a container argument.');
        return;
    }
    currentContainerArgs.push(value);
    renderContainerArgsList();
    hideModal(addContainerArgModal);
}

function addPostStartupCmdFromModal() {
    const value = postStartupCmdValueInput.value.trim();
    if (!value) {
        showAlert('Please enter a post-startup command.');
        return;
    }
    currentPostStartupCmds.push({ key: Date.now().toString(), value: value });
    renderPostStartupCmdsList();
    hideModal(addPostStartupCmdModal);
}


function deleteSelectedItems(listElement, dataArray, renderFunction) {
    const checkboxes = listElement.querySelectorAll('input[type="checkbox"]:checked');
    const indexesToDelete = Array.from(checkboxes).map(cb => parseInt(cb.dataset.index)).sort((a, b) => b - a);

    if (indexesToDelete.length === 0) {
        return;
    }

    showConfirm('Are you sure you want to delete the selected items?', () => {
        indexesToDelete.forEach(index => {
            dataArray.splice(index, 1);
        });
        renderFunction();
    });
}

function showJsonPreviewModal() {
    if (jsonOutput) {
        jsonOutput.textContent = JSON.stringify(getApplicationJsonFromForm(), null, 2);
    }
}

async function copyJsonToClipboard() {
    const textToCopy = jsonOutput.textContent;
    try {
        await navigator.clipboard.writeText(textToCopy);
        showAlert('JSON copied to clipboard!');
    } catch (err) {
        const tempInput = document.createElement('textarea');
        tempInput.value = textToCopy;
        document.body.appendChild(tempInput);
        tempInput.select();
        try {
            document.execCommand('copy');
            showAlert('JSON copied to clipboard!');
        } catch (execErr) {
            console.error('Failed to copy text using execCommand: ', execErr);
            showAlert('Failed to copy JSON. Please copy it manually.');
        } finally {
            document.body.removeChild(tempInput);
        }
    }
}


// --- Initial Render and Event Listeners ---
document.addEventListener('DOMContentLoaded', () => {
    // Initial render of lists
    renderArgList();
    renderEntrypointList();
    renderContainerArgsList();
    renderPostStartupCmdsList();

    // Event listeners for Docker Arguments
    if (addArgButton) {
        addArgButton.addEventListener('click', () => {
            if (addArgModal) {
                showModal(addArgModal);
            }
            if (document.getElementById('argTypeVolume')) {
                document.getElementById('argTypeVolume').checked = true;
            }
            updateArgPlaceholder();
        });
    }
    if (addArgModalButton) addArgModalButton.addEventListener('click', addArgumentFromModal);
    if (cancelModalButton) cancelModalButton.addEventListener('click', () => hideModal(addArgModal));
    if (closeModalButton) closeModalButton.addEventListener('click', () => hideModal(addArgModal));
    if (deleteSelectedArgsButton) deleteSelectedArgsButton.addEventListener('click', () => deleteSelectedItems(dockerArgList, currentArgs, renderArgList));
    argTypeRadios.forEach(radio => {
        radio.addEventListener('change', updateArgPlaceholder);
    });

    // Event listeners for Docker Entrypoint
    if (addEntrypointButton) addEntrypointButton.addEventListener('click', () => showModal(addEntrypointModal, entrypointValueInput));
    if (addEntrypointModalButton) addEntrypointModalButton.addEventListener('click', addEntrypointFromModal);
    if (cancelModalEntrypointButton) cancelModalEntrypointButton.addEventListener('click', () => hideModal(addEntrypointModal));
    if (closeModalEntrypointButton) closeModalEntrypointButton.addEventListener('click', () => hideModal(addEntrypointModal));
    if (deleteSelectedEntrypointsButton) deleteSelectedEntrypointsButton.addEventListener('click', () => deleteSelectedItems(dockerEntrypointListElement, currentEntrypoint, renderEntrypointList));

    // Event listeners for Container Arguments
    if (addContainerArgButton) addContainerArgButton.addEventListener('click', () => showModal(addContainerArgModal, containerArgValueInput));
    if (addContainerArgModalButton) addContainerArgModalButton.addEventListener('click', addContainerArgFromModal);
    if (cancelModalContainerArgButton) cancelModalContainerArgButton.addEventListener('click', () => hideModal(addContainerArgModal));
    if (closeModalContainerArgButton) closeModalContainerArgButton.addEventListener('click', () => hideModal(addContainerArgModal));
    if (deleteSelectedContainerArgsButton) deleteSelectedContainerArgsButton.addEventListener('click', () => deleteSelectedItems(dockerContainerArgListElement, currentContainerArgs, renderContainerArgsList));

    // Event listeners for Post-Startup Commands
    if (addPostStartupCmdButton) addPostStartupCmdButton.addEventListener('click', () => showModal(addPostStartupCmdModal, postStartupCmdValueInput));
    if (addPostStartupCmdModalButton) addPostStartupCmdModalButton.addEventListener('click', addPostStartupCmdFromModal);
    if (cancelModalPostStartupCmdButton) cancelModalPostStartupCmdButton.addEventListener('click', () => hideModal(addPostStartupCmdModal));
    if (closeModalPostStartupCmdButton) closeModalPostStartupCmdButton.addEventListener('click', () => hideModal(addPostStartupCmdModal));
    if (deleteSelectedPostStartupCmdsButton) deleteSelectedPostStartupCmdsButton.addEventListener('click', () => deleteSelectedItems(dockerPostStartupCmdList, currentPostStartupCmds, renderPostStartupCmdsList));

    // Event listeners for JSON Preview Modal
    if (previewButton && jsonPreviewModal) {
        previewButton.addEventListener('click', () => {
            showJsonPreviewModal();
            showModal(jsonPreviewModal);
        });
        closeJsonPreviewButton.addEventListener('click', () => hideModal(jsonPreviewModal));
        copyJsonButton.addEventListener('click', copyJsonToClipboard);
    } else {
        console.warn('JSON preview functionality is disabled or elements were not found.');
    }

    saveButton.addEventListener('click', async function() {
        nameInputElement = document.getElementById('name')
        if ( nameInputElement.value == "" ) {
            alert('Name is required.');
            return;
        }
        if ( nameInputElement.value.includes(" ") ) {
            alert('Name cannot contain spaces.');
            return
        }
        application_json = getApplicationJsonFromForm();
        console.log(application_json)
        if (isEditMode) {
            url = saveApplicationBaseurl
            method = 'PUT';
        } else {
            url = saveApplicationBaseurl;
            method = 'POST';
        }
        await invokeApi(url, method, application_json, indexBaseUrl);
    });

    updateJsonInput('dockerArgsJsonInput', currentArgs);
    updateJsonInput('dockerEntrypointJsonInput', currentEntrypoint);
    updateJsonInput('dockerContainerArgsJsonInput', currentContainerArgs);
    updateJsonInput('dockerPostStartupCmdsJsonInput', currentPostStartupCmds);
});
