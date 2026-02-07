/**
 * This function is called by images.js after the
 * Flask template has been injected into the DOM.
 */
window.initAndShowDetailsModal = function(imageName, tag) {
    console.log("Initializing details for:", imageName, tag);

    const modalEl = document.getElementById('detailsModal');
    const imageList = document.getElementById("imagesList");
    const imageTagInfo = document.getElementById("imageTagInfo");

    if (!modalEl || !imageList) {
        console.error("Required modal elements not found in DOM.");
        return;
    }

    const detailsModal = new bootstrap.Modal(modalEl);

    async function renderDetails() {
        imageList.innerHTML = "";
        imageTagInfo.innerHTML = "";

        imageList.appendChild(createTagImageListItemHeader());

        const url = `${getTagDetailsBaseUrl}?image_name=${encodeURIComponent(imageName)}&tag=${encodeURIComponent(tag)}`;

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();

            if (data.images && Array.isArray(data.images)) {
                data.images.forEach(image => {
                    imageList.appendChild(createTagImageListItem(image));
                });
            }
        } catch (error) {
            console.error('Fetch error:', error);
            imageList.innerHTML = `<li class="list-group-item text-danger">Error loading data.</li>`;
        }
    }

    function createTagImageListItemHeader() {
        const headerData = { "arch": "Arch", "os": "OS", "size": "Size" };
        return createTagImageListItem(headerData, true);
    }

    function createTagImageListItem(image, header = false) {
        const textClass = header ? "fw-bold" : "fw-normal";
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex align-items-center justify-content-between';

        const content = document.createElement('div');
        content.className = 'd-flex gap-5';

        ['arch', 'os', 'size'].forEach(key => {
            const div = document.createElement('div');
            div.textContent = image[key] || "N/A";
            div.className = textClass;
            div.style.width = '100px';
            content.appendChild(div);
        });

        li.appendChild(content);

        if (!header) {
            const actions = document.createElement('div');
            actions.className = 'd-flex gap-2';

            // Assuming renderButtonContainer is defined globally or elsewhere
            actions.appendChild(renderButtonContainer("Info", "btn-outline-primary", () => showTagImageInfo(image)));
            actions.appendChild(renderButtonContainer("Delete", "btn-outline-danger", () => {}));
            li.appendChild(actions);
        }
        return li;
    }

    function showTagImageInfo(image) {
        const manifest = image['digest'];
        const url = `${getArchitectureManifestDetailsBaseUrl}?image_name=${encodeURIComponent(imageName)}&tag=${encodeURIComponent(tag)}&manifest=${encodeURIComponent(manifest)}`;

        fetch(url)
            .then(response => response.json())
            .then(response => {
                imageTagInfo.innerHTML = ""; // Clear old info
                addInfoDivElement("Built", response["built"])
                addInfoDivElement("Cmd", JSON.stringify(response["cmd"]))
                addInfoDivElement("Entrypoint", response["entrypoint"])
                addInfoDivElement("Env", response["env"])
                addInfoDivElement("Exposed Ports", response["exposed_ports"])
                addInfoDivElement("Labels", response["labels"])
                addInfoDivElement("User", response["user"])
                addInfoDivElement("Working Dir", response["working_dir"])
            });
    }

    function addInfoDivElement(label, data) {
        const rowWrapper = document.createElement("div");
        rowWrapper.className = "row g-2 mb-2 align-items-stretch w-100 m-0";
        rowWrapper.innerHTML = `
            <div class="col-4"><div class="p-2 border rounded fw-bold h-100">${label}</div></div>
            <div class="col-8"><div class="p-2 border rounded h-100 text-break">${Array.isArray(data) ? data.join(', ') : data}</div></div>
        `;
        imageTagInfo.appendChild(rowWrapper);
    }

    renderDetails();
    detailsModal.show();
};