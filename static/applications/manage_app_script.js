document.addEventListener('DOMContentLoaded', () => {
    const hostListElement = document.getElementById('hostList');

    function createListItem(name, logging_config) {

        const li = document.createElement('li');
        li.className = 'list-group-item p-0 border-0';

        const content = document.createElement('div');
        content.className = 'card mb-3';

        const details = document.createElement("details");
        details.className = 'w-100';
        details.setAttribute('open', '');
        content.appendChild(details);

        const summary = document.createElement("summary");
        summary.className = 'card-header';
        summary.textContent = name;
        details.appendChild(summary);

        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        details.appendChild(cardBody);

        const textAndButtonsContainer = document.createElement('div');
        textAndButtonsContainer.className = 'd-flex justify-content-between align-items-center mb-2';
        cardBody.appendChild(textAndButtonsContainer, name);

        const span = document.createElement('span');
        span.textContent = "Manage " + application_config['name'] + " on " + name + ".";
        span.className = 'card-text';
        textAndButtonsContainer.appendChild(span);

        addMangementButtons(textAndButtonsContainer, name, logging_config);

        const outputBody = document.createElement('div');
        outputBody.className = 'card-body border';
        cardBody.appendChild(outputBody);
        outputBody.textContent = 'Output...';
        outputBody.setAttribute('data-host-name', name);
        outputBody.style.height = '400px';
        outputBody.style.overflowY = 'scroll';
        outputBody.style.whiteSpace = 'pre-wrap'

        li.appendChild(content);
        return li;
    }

    function addMangementButtons(container, hostName, logging_config) {

        console.log(logging_config)

        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'd-flex gap-2';
        container.appendChild(buttonContainer);

        button = createButton('View Logs', 'btn btn-sm btn-outline-info', function(event) {
            event.preventDefault();
            followLogs(event, app_name, hostName);
        })
        buttonContainer.appendChild(button)

        if ( logging_config ) {
            if ( logging_config.global_toggle ) {
                button = createButton('Toggle Log Level', 'btn btn-sm btn-outline-light', function (event) {
                    event.preventDefault();
                    toggleLogLevel(event, app_name, hostName);
                })
                buttonContainer.appendChild(button)
            }
            if ( logging_config.process_toggles ) {
                button = createDropdownButton('Toggle Log Level', 'btn btn-sm btn-outline-light', app_name, hostName, logging_config.process_toggles, )
                buttonContainer.appendChild(button)
            }
        }

        button = createButton('Restart', 'btn btn-sm btn-outline-warning', function(event) {
            event.preventDefault();
            restartApplication(event, app_name, hostName);
        })
        buttonContainer.appendChild(button)

        button = createButton('Deploy', 'btn btn-sm btn-outline-danger', function(event) {
            event.preventDefault();
            upgradeApplication(event, app_name, hostName, application_config);
        })
        buttonContainer.appendChild(button)
    }

    function createButton(name, classes, evenListener) {
        const button = document.createElement('button');
        button.className = classes;
        button.textContent = name;
        button.addEventListener('click', evenListener);
        return button
    }

    function createDropdownButton(name, classes, appName, hostName, options) {

        const dropdownDiv = document.createElement("div");
        dropdownDiv.className = "dropdown";

        const btn = document.createElement("button");
        btn.className = "btn btn-sm btn-outline-light dropdown-toggle";
        btn.type = "button";
        btn.id = "dropdownMenuButton";
        btn.setAttribute("data-bs-toggle", "dropdown");
        btn.setAttribute("aria-expanded", "false");
        btn.textContent = name;

        const menu = document.createElement("ul");
        menu.className = "dropdown-menu";
        menu.setAttribute("aria-labelledby", "dropdownMenuButton");

        options.forEach(opt => {
            const li = document.createElement("li");
            const a = document.createElement("a");
            a.className = "dropdown-item";
            a.href = "#";
            a.textContent = opt;

            a.onclick = (e) => {
                e.preventDefault();
                console.log("Selected:", opt);
                toggleLogLevel(e, app_name, hostName, opt)
            };

            li.appendChild(a);
            menu.appendChild(li);
        });

        dropdownDiv.appendChild(btn);
        dropdownDiv.appendChild(menu);
        return dropdownDiv
    }

    function renderHosts() {
        hostListElement.innerHTML = '';
        console.log(application_config)
        application_config['hosts'].forEach(host => {
            const li = createListItem(host, application_config.logging_config);
            hostListElement.appendChild(li);
        });
    }

    async function upgradeApplication(event, app_name, hostName, application_config) {
        console.log("Upgrading " + app_name + " on " + hostName + "...");
        const getContainerVersionsUrl = `${getContainerVersionsBaseUrl}?app=${encodeURIComponent(app_name)}&url=${encodeURIComponent(application_config.docker_url)}&version_pattern=${encodeURIComponent(application_config.version_pattern)}`;
        fetch(getContainerVersionsUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(optionsList => {
                console.log("Options list:", optionsList);
                return showUpgradeVersionSelectionModal(optionsList);
            })
            .then(selectedVersion => {
                console.log("Selected version:", selectedVersion);
                if (selectedVersion === null) {
                    return;
                }
                const streamUrl = `${deployAppVersionBaseUrl}?host=${encodeURIComponent(hostName)}&container=${encodeURIComponent(app_name)}&version=${encodeURIComponent(selectedVersion)}`;
                console.log(streamUrl)
                fetchStreamedResponse(event, "upgrade", streamUrl)
            })
            .catch(error => {
                console.error('Fetch error:', error);
            });
    }
    
    function restartApplication(event, app_name, hostName) {
        let userChoice = confirm("Are you sure you want to restart " + app_name + " on " + hostName + "?");
        if (userChoice) {
            console.log("Restarting " + app_name + " on " + hostName + "...");
            const streamUrl = `${streamRestartBaseUrl}?host=${encodeURIComponent(hostName)}&container=${encodeURIComponent(app_name)}`;
            fetchStreamedResponse(event, "restart", streamUrl)
        } else {
            console.log("Cancelled restarting " + app_name + " on " + hostName + ".");
        }
    }

    function toggleLogLevel(event, appName, hostName, processName) {
        let streamUrl = `${toggleLogLevelBaseUrl}?host=${encodeURIComponent(hostName)}&container=${encodeURIComponent(appName)}`;
        if (processName) {
            streamUrl = streamUrl + `&process=${encodeURIComponent(processName)}`
        }
        fetchStreamedResponse(event, "logs", streamUrl)
    }

    function fetchStreamedResponse(event, type, streamUrl) {

        const cardBody = event.target.closest('.card-body');
        const outputBody = cardBody.querySelector('.card-body.border');
        outputBody.textContent = `Streaming ${type}...\n\n`;
        fetch(streamUrl)
            .then(response => {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                function read() {
                    reader.read().then(({ done, value }) => {
                        if (done) {
                            outputBody.textContent += '\nStream finished.';
                            return;
                        }

                        const chunk = decoder.decode(value, { stream: true });
                        outputBody.textContent += chunk;
                        outputBody.scrollTop = outputBody.scrollHeight;

                        read();
                    }).catch(error => {
                        outputBody.textContent += `\nError: ${error.message}`;
                    });
                }
                read();
            })
            .catch(error => {
                outputBody.textContent = `Error connecting to proxied ${type} command stream: ${error.message}`;
            });
    }

    function showUpgradeVersionSelectionModal(optionsList) {
        return new Promise((resolve, reject) => {
            const modalElement = document.getElementById('selectModal');
            const selectElement = document.getElementById('selectOptions');
            const okButton = document.getElementById('modalOkBtn');
            const bsModal = new bootstrap.Modal(modalElement);

            console.log("Options list:", optionsList);
            // Clear previous options and populate the dropdown
            selectElement.innerHTML = '';
            optionsList.forEach(item => {
                const option = document.createElement('option');
                option.value = item;
                option.textContent = item;
                selectElement.appendChild(option);
            });

            // Event listeners for the buttons
            okButton.onclick = () => {
                const selectedValue = selectElement.value;
                bsModal.hide();
                resolve(selectedValue);
            };

            // Handle cancel/dismiss actions
            modalElement.addEventListener('hidden.bs.modal', function onModalHidden(event) {
                // Check if the promise has already been resolved by the OK button
                // If not, it means the user closed the modal via the "Cancel" button or X
                if (okButton.onclick) {
                    resolve(null);
                }
                // Clean up the event listener to prevent memory leaks
                modalElement.removeEventListener('hidden.bs.modal', onModalHidden);
            });

            bsModal.show();
        });
    }

    renderHosts();
    

});
