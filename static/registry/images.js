document.addEventListener('DOMContentLoaded', function () {

    const imageList = document.getElementById('image-list');

    function createImageListItem(name) {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        const content = document.createElement('div');
        content.className = 'd-flex align-items-center gap-2';
        content.textContent = name;
        li.appendChild(content);
        li.addEventListener('click', () => {
            handleImageSelection(li, name);
        });
        return li;
    }

    function createTagListItem(imageName, tag) {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex align-items-center justify-content-between';

        const content = document.createElement('div');
        content.className = 'd-flex gap-5';

        const tagDiv = document.createElement('div');
        tagDiv.textContent = tag;
        tagDiv.className = 'fw-bold';
        tagDiv.style.width = '100px';
        content.appendChild(tagDiv);

        const actions = document.createElement('div');
        actions.className = 'd-flex gap-2';

        const detailsContainer = renderButtonContainer( "Details", "btn-outline-primary", () => window.showDetails(imageName, tag))
        detailsContainer.style.width = '100px';
        actions.appendChild(detailsContainer);

        docker_url="192.168.50.15:5000/" + imageName + ":" + tag
        const copyContainer = renderButtonContainer( "Copy URL", "btn-outline-secondary",  () => navigator.clipboard.writeText(docker_url))
        actions.appendChild(copyContainer);


        const deleteContainer = renderButtonContainer( "Delete", "btn-outline-danger", () => deleteTag(imageName, tag, info.digest))
        deleteContainer.style.width = '100px';
        actions.appendChild(deleteContainer);

        li.appendChild(content);
        li.appendChild(actions);

        return li;
    }

    function handleImageSelection(selectedLi, itemName) {
        const currentSelected = imageList.querySelector('.bg-primary.text-white');
        if (currentSelected) {
            currentSelected.classList.remove('bg-primary', 'text-white');
        }
        selectedLi.classList.add('bg-primary', 'text-white');

        if (currentSelected) {
            currentSelected.classList.remove('selected');
        }
        selectedLi.classList.add('selected');
        updateImageDetails(itemName);
    }

    function updateImageDetails(imageName) {

        const tagsList = document.getElementById("tag-list");
        tagsList.innerHTML = `<li class="list-group-item d-flex justify-content-center align-items-center text-muted"><p>Loading...</p></li>`


        const getImageVersionsUrl = `${getImageTagsBaseUrl}?image_name=${encodeURIComponent(imageName)}`;
        fetch(getImageVersionsUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(tags => {
                tagsList.innerHTML = "";
                Object.values(tags)
                    .forEach(tag => {
                        tagsList.appendChild(createTagListItem(imageName, tag));
                    });
                return;
            })
            .catch(error => {
                console.error('Fetch error:', error);
            });

        imageDetails = document.getElementById("image-name")
        imageDetails.textContent = imageName
    }

    function parseTag(tag) {
        const clean = tag.replace(/^v/, "");
        return clean.split(".").map(s => Number.isNaN(Number(s)) ? s : Number(s));
    }

    function deleteTag(imageName, tag, digest) {
        const url = new URL(deleteTagBaseUrl, window.location.origin);
        url.searchParams.append('image_name', imageName);
        url.searchParams.append('tag', tag);
        url.searchParams.append('digest', digest);

        fetch(url, { method: 'DELETE' })
            .then(res => {
                window.location.href = getIndexBaseUrl
            })
            .catch(err => console.error('Error deleting tag:', err));

        // TODO:
        // To clean up the hanging image after all tags are deleted,  call
        // docker exec -it registry bin/registry garbage-collect /etc/distribution/config.yml
    }


    function renderImageList() {
        images.forEach( image => {
            imageList.appendChild(createImageListItem(image))
        });
    }

    renderImageList();

});
