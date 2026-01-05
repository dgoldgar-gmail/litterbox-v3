document.addEventListener('DOMContentLoaded', function() {

    const applicationListElement = document.getElementById('applicationsList');
    const addApplicationButton = document.getElementById('addApplicationButton');
    const previewButton = document.getElementById('previewButton');

    setupDragDrop("applicationsList", reorderCallback)


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

    function renderApplications() {
        currentApplications.forEach(app => {
            let appName = app.name
            const li = createListItem(appName, 'application', {
                editCallback: function () {
                    const url = editApplicationUrlBase.replace('__NAME__', appName);
                    window.location.href = url;
                }, manageCallback: function () {
                    const url = manageApplicationUrlBase.replace('__NAME__', appName);
                    window.location.href = url;
                }
            });

            applicationListElement.appendChild(li);
        });
    }

    addApplicationButton.addEventListener('click', () => {
        console.log('addApplicationButton clicked');
        window.location.href = addApplicationUrlBase.replace("__NAME__", "new_application");
    });

    previewButton.addEventListener('click' , () => {
        console.log("Clicked preview button...")
        const previewModal = new bootstrap.Modal(document.getElementById('previewModal'));
        jsonOutput = document.getElementById("jsonPreview")
        const jsonString = JSON.stringify(currentApplications, null, 2);
        jsonOutput.textContent = jsonString;
        previewModal.show();
    });

    renderApplications();

});