
function showFlashMessage(message, category = 'success') {
    const container = document.querySelector('.container.mt-3');
    if (!container) {
        console.error('Could not find the main content container.');
        return;
    }

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${category}`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.textContent = message;

    // Insert the alert at the top of the container
    container.prepend(alertDiv);

    setTimeout(() => {
        alertDiv.classList.add('fade-out'); // Add a fade-out class
        alertDiv.addEventListener('transitionend', () => alertDiv.remove());
    }, 4000);
}


function reorderCallback() {
    const key_order = Array.from(applicationListElement.querySelectorAll('li'))
        .map(li => li.textContent.trim().replace("ManageEdit", ""));

    fetch(reorderUrlBase, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(key_order),
    })
        .then(response => {
            if (!response.ok) {
                // If the response is not OK, we can still parse the JSON for an error message
                return response.json().then(errorData => {
                    throw new Error(errorData.message || 'Network response was not ok');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Success:', data);
            if (data.status === 'success' && data.message) {
                showFlashMessage(data.message, 'success');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showFlashMessage(error.message, 'danger');
        });
}


async function invokeApi(url, method, data, redirectUrl) {
    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        console.log(response)
        if (response.ok) {
            const result = await response.json();
            console.log(result.message);
            window.location.href = redirectUrl

        } else {
            const errorResult = await response.json();
            console.error('Error:', errorResult.message);
            // You might need to create a function to display these flash messages
            // displayFlashMessage(errorResult.message, 'error');
        }
    } catch (error) {
        console.error('Network Error:', error);
        // displayFlashMessage('Failed to connect to the server.', 'error');
    }
}


async function getData(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || 'Request failed');
    }

    return await response.json();
}


function copyToClipboard(text, contentName) {

    navigator.clipboard.writeText(text)
        .then(() => {
            alert(`${contentName} copied to clipboard!`);
        })
        .catch(err => {
            console.error("Failed to copy ${contentName}:", err);
            alert("Failed to copy ${contentName}. Check browser permissions.");
        });
}

function createListItem(name, type, options = {}) {
    // Correctly set the draggable property
    const li = document.createElement('li');
    li.draggable = true;
    li.className = 'list-group-item d-flex justify-content-between align-items-center';

    const content = document.createElement('div');
    content.className = 'd-flex align-items-center gap-2';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.name = type + '_entries';
    checkbox.value = name;
    checkbox.className = 'form-check-input me-1';

    const span = document.createElement('span');
    span.textContent = name;

    content.appendChild(checkbox);
    content.appendChild(span);
    li.appendChild(content);

    // Create a container for the buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'd-flex gap-2';

    // Conditionally create and append buttons based on options
    if (options.manageCallback) {
        const manageButton = document.createElement('button');
        manageButton.className = 'btn btn-sm btn-outline-primary';
        manageButton.textContent = 'Manage';
        manageButton.addEventListener('click', function(event) {
            event.preventDefault();
            options.manageCallback();
        });
        buttonContainer.appendChild(manageButton);
    }

    if (options.editCallback) {
        const editButton = document.createElement('button');
        editButton.className = 'btn btn-sm btn-outline-success'
        editButton.textContent = 'Edit';
        editButton.addEventListener('click', function(event) {
            event.preventDefault();
            options.editCallback();
        });
        buttonContainer.appendChild(editButton);
    }

    li.appendChild(buttonContainer);

    return li;
}

function setupDragDrop(listName, onDropCallback = null) {

    let draggedItem = null;
    const listElement = document.getElementById(listName);

    listElement.addEventListener('dragstart', (e) => {
        console.log("Start drag")
        draggedItem = e.target;
        setTimeout(() => {
            e.target.classList.add('dragging');
        }, 0);
    });

    listElement.addEventListener('dragover', (e) => {
        e.preventDefault();
        const afterElement = getDragAfterElement(listElement, e.clientY);
        const currentElement = afterElement ? afterElement : listElement.lastElementChild;
        const existingHighlight = listElement.querySelector('.drop-highlight');
        if (existingHighlight) {
            existingHighlight.classList.remove('drop-highlight');
        }
        if (currentElement && draggedItem && currentElement !== draggedItem) {
            currentElement.classList.add('drop-highlight');
        }
    });

    listElement.addEventListener('dragleave', (e) => {
        const existingHighlight = listElement.querySelector('.drop-highlight');
        if (existingHighlight) {
            existingHighlight.classList.remove('drop-highlight');
        }
    });

    listElement.addEventListener('drop', (e) => {
        e.preventDefault();
        const dropTarget = e.target;
        const afterElement = getDragAfterElement(listElement, e.clientY);

        if (draggedItem && draggedItem !== dropTarget) {
            if (afterElement) {
                listElement.insertBefore(draggedItem, afterElement);
            } else {
                listElement.appendChild(draggedItem);
            }
        }

        draggedItem.classList.remove('dragging');
        const existingHighlight = listElement.querySelector('.drop-highlight');
        if (existingHighlight) {
            existingHighlight.classList.remove('drop-highlight');
        }

        if (onDropCallback && typeof onDropCallback === 'function') {
            onDropCallback(listElement);
        }
        draggedItem = null;
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('li:not(.dragging)')];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function getcamelCase(word) {
    return word.charAt(0).toLowerCase() + word.slice(1)
}


function renderButtonContainer(text, buttonType, onClick) {
    const container = document.createElement('div');
    container.style.width = '100px';
    const button = document.createElement('button');
    button.className = 'btn btn-sm w-100 ' + buttonType;
    button.textContent = text;
    button.style.whiteSpace = 'nowrap';
    button.addEventListener('click', onClick);
    container.appendChild(button);
    return container;
}

