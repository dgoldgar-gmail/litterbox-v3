// Get references to all your elements
const nginxContainer = document.getElementById("nginx-select-container");
const nginxSelect = document.getElementById("nginx-select");
const resolverSelection = document.getElementById("resolver-select");
const resultBox = document.getElementById("result-box");

// Get button references using their new IDs
const generateButton = document.getElementById("generate-button");
const copyButton = document.getElementById("copy-button");
const saveButton = document.getElementById("save-button");

const fileTreeContainer = document.getElementById("file-tree-container");

// The 'files' and 'generateUrl' variables are globally available from the template's <script> block
const nginxOptions = template_files
    .filter(f => f.startsWith("nginx_") && f.endsWith(".j2"))
    .map(f => f.slice(6, -3));

function resetNginxOptions() {
    nginxSelect.innerHTML = '<option disabled selected>Select config</option>';
}

function populateNginxOptions() {
    resetNginxOptions();
    nginxOptions.forEach(opt => {
        const option = document.createElement("option");
        option.value = opt;
        option.textContent = opt;
        nginxSelect.appendChild(option);
    });
}

function submitGenerate() {
    const resolverType = resolverSelection.value;
    const nginxConfig = nginxSelect.value;

    // Validation check: If Nginx is selected but no config is chosen, alert the user and stop.
    if (resolverType === "nginx" && nginxConfig === "Select config") {
        alert("Please select an Nginx config file.");
        return; // This stops the function from continuing
    }

    console.log("Setting resolverType to " + resolverType);
    console.log("Setting nginxConfig to " + nginxConfig);

    localStorage.setItem('resolverType', resolverType);
    localStorage.setItem('nginxConfig', nginxConfig);

    const params = new URLSearchParams();
    params.append("templateType", resolverType);
    if (resolverType === "nginx") {
        params.append("nginxConfig", nginxConfig);
    }

    window.location.href = generateUrl + "?" + params.toString();
}

function copyTemplateOutputToClipboard() {
    const output = resultBox.textContent;
    copyToClipboard(output, "Template Output");
}

function submitSaveForm() {
    const output = resultBox.textContent;

    console.log(document.getElementById('resolverType-input').value);
    console.log(document.getElementById('nginxConfig-input').value);
    console.log(localStorage.getItem('resolverType'));
    console.log(localStorage.getItem('nginxConfig'));

    document.getElementById('content-input').value = output;
    document.getElementById('resolverType-input').value = localStorage.getItem('resolverType') || '';
    document.getElementById('nginxConfig-input').value = localStorage.getItem('nginxConfig') || '';

    document.getElementById('template-save-form').submit();

    localStorage.removeItem('resolverType');
    localStorage.removeItem('nginxConfig');
}

// Event listeners to connect functions to button clicks
resolverSelection.addEventListener("change", function () {
    if (this.value === "nginx") {
        populateNginxOptions();
        nginxContainer.style.display = "block";
    } else {
        nginxContainer.style.display = "none";
        resetNginxOptions();
    }
});

// Attach event listeners to the new button IDs
generateButton.addEventListener("click", submitGenerate);
copyButton.addEventListener("click", copyTemplateOutputToClipboard);
saveButton.addEventListener("click", submitSaveForm);

// Optional: hide nginx dropdown on page load
nginxContainer.style.display = "none";
