document.addEventListener('DOMContentLoaded', function () {
    let currentImage = null
    let currentTag = null
    const modalEl = document.getElementById('detailsModal');
    const detailsModal = new bootstrap.Modal(modalEl);

    window.showDetails = function(image_name, tag) {
        currentImage = image_name
        currentTag = tag
        detailsModal.show();     // show modal
    }

    async function renderDetails(){

        const imageList = document.getElementById("imagesList");
        imageList.innerHTML = ""

        const imageTagInfo = document.getElementById("imageTagInfo");
        imageTagInfo.innerHTML = "";

        imageList.appendChild(createTagImageListItemHeader())
        const getTagDetailsUrl = `${getTagDetailsBaseUrl}?image_name=${encodeURIComponent(currentImage)}&tag=${encodeURIComponent(currentTag)}`;
        fetch(getTagDetailsUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(response => {
                console.log( response['type'], response['image_name'], response['tag']);
                response['images'].forEach(image => {
                    console.log(image);
                    imageList.appendChild(createTagImageListItem(image))
                })
            })
            .catch(error => {
                console.error('Fetch error:', error);
            });
    }

    function createTagImageListItemHeader() {
        inputs = {
            "arch": "Arch",
            "os": "OS",
            "digest": "Digest",
            "size": "Size"
        }
        return createTagImageListItem(inputs, true)
    }

    function createTagImageListItem(image, header=false) {

        let textClass = "fw-normal"
        if (header) {
            textClass = "fw-bold"
        }

        const li = document.createElement('li');
        li.className = 'list-group-item d-flex align-items-center justify-content-between';

        const content = document.createElement('div');
        content.className = 'd-flex gap-5';

        const archDiv = document.createElement('div');
        archDiv.textContent = image['arch'];
        archDiv.className = textClass;
        archDiv.style.width = '100px';
        content.appendChild(archDiv);

        const osDiv = document.createElement('div');
        osDiv.textContent = image['os'];
        osDiv.className = textClass;
        osDiv.style.width = '100px';
        content.appendChild(osDiv);

        const sizeDiv = document.createElement('div');
        sizeDiv.textContent = image['size'];
        sizeDiv.className = textClass;
        sizeDiv.style.width = '100px';
        content.appendChild(sizeDiv);
        li.appendChild(content);

        if (! header) {
            const actions = document.createElement('div');
            actions.className = 'd-flex gap-2';

            const infoContainer = renderButtonContainer("Info", "btn-outline-primary", () => showTagImageInfo(image))
            infoContainer.style.width = '100px';
            actions.appendChild(infoContainer);

            const deleteContainer = renderButtonContainer("Delete", "btn-outline-danger", () => deleteTagImage(image))
            deleteContainer.style.width = '100px';
            actions.appendChild(deleteContainer);
            li.appendChild(actions);
        }


        return li;
    }



    function showTagImageInfo(image) {
        imageTagInfo = document.getElementById("imageTagInfo");
        console.log(image)

        const manifest = image['digest'];
        // TODO:  I think this is where we call that blob api ...
        //getArchitectureManifestDetailsBaseUrl
        const getArchitectureManifestDetailsUrl = `${getArchitectureManifestDetailsBaseUrl}?image_name=${encodeURIComponent(currentImage)}&tag=${encodeURIComponent(currentTag)}&manifest=${encodeURIComponent(manifest)}`;


        fetch(getArchitectureManifestDetailsUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(response => {
                console.log(response)

                addInfoDivElement("Built", response["built"])
                addInfoDivElement("Cmd", JSON.stringify(response["cmd"]))
                addInfoDivElement("Entrypoint", response["entrypoint"])
                addInfoDivElement("Env", response["env"])
                addInfoDivElement("Exposed Ports", response["exposed_ports"])
                addInfoDivElement("Labels", response["labels"])
                addInfoDivElement("User", response["user"])
                addInfoDivElement("Working Dir", response["working_dir"])



            })
            .catch(error => {
                console.error('Fetch error:', error);
            });
    }

    function addInfoDivElement(label, data) {
        const imageTagInfo = document.getElementById("imageTagInfo");

        // 1. Create a Row container
        const rowWrapper = document.createElement("div");
        rowWrapper.className = "row g-2 mb-2 align-items-stretch w-100 m-0";

        // 2. Label Column (1/3 width)
        const labelCol = document.createElement("div");
        labelCol.className = "col-4";
        const labelBox = document.createElement("div");
        labelBox.className = "p-2 border rounded fw-bold h-100";
        labelBox.textContent = label;
        labelCol.appendChild(labelBox);

        // 3. Text Column (2/3 width)
        const textCol = document.createElement("div");
        textCol.className = "col-8";
        const textBox = document.createElement("div");
        textBox.className = "p-2 border rounded h-100 text-break";

        // --- ARRAY CHECK LOGIC ---
        if (Array.isArray(data)) {
            // If it's an array, create a div for each entry
            data.forEach((item, index) => {
                const line = document.createElement("div");
                line.textContent = item;

                // Add a separator line for everything except the last item
                if (index < data.length - 1) {
                    line.className = "border-bottom pb-1 mb-1";
                }
                textBox.appendChild(line);
            });
        } else {
            // Fallback for simple strings
            textBox.textContent = data;
        }

        // 4. Assemble
        textCol.appendChild(textBox);
        rowWrapper.appendChild(labelCol);
        rowWrapper.appendChild(textCol);

        imageTagInfo.appendChild(rowWrapper);
    }

    function deleteTagImage(image) {
        // TODO:  I think we have to pass the config digest or something.  not 100% clear...
    }



    modalEl.addEventListener('show.bs.modal', renderDetails);
});
