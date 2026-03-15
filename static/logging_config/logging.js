document.addEventListener('DOMContentLoaded', () => {
    const numCols = 3;
    const chunkSize = Math.ceil(loggers.length / numCols);

    for (let i = 0; i < numCols; i++) {
        const colContainer = document.getElementById(`loggers-col-${i + 1}`);

        if (!colContainer) continue;

        colContainer.innerHTML = '';

        const start = i * chunkSize;
        const chunk = loggers.slice(start, start + chunkSize);

        const table = document.createElement('table');
        table.className = 'table table-hover table-bordered table-sm align-middle mb-0';
        table.style.tableLayout = 'fixed';
        table.style.fontSize = '12px';

        table.innerHTML = `
            <thead class="table-dark text-center">
                <tr>
                    <th style="width: 50%;">Name</th>
                    <th title="Error"   style="width: 12.5%;">E</th>
                    <th title="Warning" style="width: 12.5%;">W</th>
                    <th title="Info"    style="width: 12.5%;">I</th>
                    <th title="Debug"   style="width: 12.5%;">D</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;

        const tbody = table.querySelector('tbody');

        chunk.forEach((item, index) => {
            const isInfo  = item.eff_level === 'INFO'    || item.level === 'INFO';
            const isDebug = item.eff_level === 'DEBUG'   || item.level === 'DEBUG';
            const isError = item.eff_level === 'ERROR'   || item.level === 'ERROR';
            const isWarn  = item.eff_level === 'WARNING' || item.level === 'WARNING';

            const globalIndex = start + index;
            const groupName = `level-${globalIndex}`;

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="text-truncate px-2" title="${item.name}">
                    ${item.name}
                </td>
                <td class="text-center">
                    <input class="form-check-input mt-0" type="radio" name="${groupName}" value="ERROR" id="e-${globalIndex}" ${isError ? 'checked' : ''}>
                </td>
                <td class="text-center">
                    <input class="form-check-input mt-0" type="radio" name="${groupName}" value="WARNING" id="w-${globalIndex}" ${isWarn ? 'checked' : ''}>
                </td>
                <td class="text-center">
                    <input class="form-check-input mt-0" type="radio" name="${groupName}" value="INFO" id="i-${globalIndex}" ${isInfo ? 'checked' : ''}>
                </td>
                <td class="text-center">
                    <input class="form-check-input mt-0" type="radio" name="${groupName}" value="DEBUG" id="d-${globalIndex}" ${isDebug ? 'checked' : ''}>
                </td>
            `;
            tbody.appendChild(tr);
        });
        colContainer.appendChild(table);
    }

    document.getElementById('apply-button').addEventListener('click', async () => {
        const updatedLoggers = loggers.map((item, index) => {
            // Find the radio button that is checked in this specific row's group
            const selectedRadio = document.querySelector(`input[name="level-${index}"]:checked`);

            return {
                name: item.name,
                level: selectedRadio ? selectedRadio.value : item.level // Fallback to current level if none selected
            };
        });

        console.log("Collected Data:", JSON.stringify(updatedLoggers, null, 2));

        const response = await fetch('/setup/update_loggers', {
            method: 'PUT', // Changed from POST
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedLoggers)
        });
    });
});