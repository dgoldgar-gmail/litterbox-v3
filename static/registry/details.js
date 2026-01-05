document.addEventListener('DOMContentLoaded', function () {
    let detailsInfo = null;
    const modalEl = document.getElementById('detailsModal');
    const detailsModal = new bootstrap.Modal(modalEl);

    window.showDetails = function(info) {
        detailsInfo = info;      // store info for modal JS
        detailsModal.show();     // show modal
    }

    async function renderDetails() {
        console.log(detailsInfo)
        const data = await getData(getTagBlobBaseUrl, detailsInfo)
        const ul = document.getElementById('platformsList');
        while (ul != null && ul.firstChild) {
            ul.removeChild(ul.firstChild);
        }


        data.forEach(d => {
            const li = createListItem(d.architecture, "tag");
            const btn = document.createElement('button');
            btn.textContent = 'Info';
            btn.className = 'btn btn-outline-info';
            btn.addEventListener('click', () => {
                console.log(d);

            });
            li.appendChild(btn);
            ul.appendChild(li);
        });
        //console.log(data)
    }
    modalEl.addEventListener('show.bs.modal', renderDetails);
});
