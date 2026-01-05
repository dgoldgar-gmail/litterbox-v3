// Get references to all your elements
const resolverOptionContainer = document.getElementById("resolver-option-select-container");
const resolverOptionSelect = document.getElementById("resolver-option-select");

const resolverSelection = document.getElementById("resolver-select");
const resultBox = document.getElementById("result-box");

// Get button references using their new IDs
const generateButton = document.getElementById("generate-button");
const copyButton = document.getElementById("copy-button");
const saveButton = document.getElementById("save-button");

const fileTreeContainer = document.getElementById("file-tree-container");

function stripTemplateName(filename, prefix) {
    return filename.replace(new RegExp(`^${prefix}_`), '').replace(/\.j2$/, '');
}

const nginxOptions = template_files
    .filter(f => f.startsWith("nginx_") && f.endsWith(".j2"))
    .map(f => stripTemplateName(f, "nginx"));

const homeassistantOptions = template_files
    .filter(f => f.startsWith("homeassistant_") && f.endsWith(".j2"))
    .map(f => stripTemplateName(f, "homeassistant"));

function resetResolverOptions() {
    resolverOptionSelect.innerHTML = '<option disabled selected>Select config</option>';
}

function populateResolverOptions() {
    resetResolverOptions()
    const resolverType = resolverSelection.value;
    let options = []
    if ( resolverType == "nginx") {
        options = nginxOptions
    } else if ( resolverType == "homeassistant") {
        options = homeassistantOptions
    }
    console.log("Populate options: " + options);

    options.forEach(opt => {
        const option = document.createElement("option");
        option.value = opt;
        option.textContent = opt;
        resolverOptionSelect.appendChild(option);
    });
    resolverOptionContainer.style.display = "block";
}

function submitGenerate() {
    resolverType = resolverSelection.value;
    resolverOption = resolverOptionSelect.value;

    console.log(resolverOption)
    if ( ( resolverType === "nginx" ||  resolverType === "homeassistant" ) && resolverOption === "Select resolver option") {
        alert("Please select a resolver option for ", resolverType);
        return;
    }

    console.log("Setting resolverType to " + resolverType);
    console.log("Setting resolverOption to " + resolverOption);

    localStorage.setItem('resolverType', resolverType);
    localStorage.setItem('resolverOption', resolverOption);

    const params = new URLSearchParams();
    params.append("resolverType", resolverType);
    if (resolverType === "nginx" || resolverType === "homeassistant" ) {
        params.append( "resolverOption", resolverOption);
    }
    window.location.href = generateUrl + "?" + params.toString();
}

function copyTemplateOutputToClipboard() {
    const output = resultBox.textContent;
    copyToClipboard(output, "Template Output");
}

function submitSaveForm() {
    const output = resultBox.textContent;
    const resolverType = resolverSelection.value;
    const resolverOption = resolverOptionSelect.value;

    if (!resolverType) {
        alert("Select a resolver type");
        return;
    }

    document.getElementById('content-input').value = output;
    document.getElementById('resolverType-input').value = resolverType;

    if (resolverType === "nginx" || resolverType === "homeassistant") {
        document.getElementById('resolverOption-input').value = resolverOption || '';
    } else {
        document.getElementById('resolverOption-input').value = '';
    }

    document.getElementById('template-save-form').submit();
}

resolverSelection.addEventListener("change", function () {
    console.log("Resolver type changed to " + this.value);
    if (this.value === "nginx"  || this.value === "homeassistant") {
        populateResolverOptions();
        resolverOptionContainer.style.display = "block";
    } else {
        resolverOptionContainer.style.display = "none";
        resetResolverOptions();
    }
});

resolverOptionSelect.addEventListener("change", function () {
    console.log("Resolver option changed to " + this.value);
});

function getResolverSelections() {
    return {
        resolver: resolverSelection.value,
        option: resolverOptionSelect.value
    };
}

window.addEventListener("DOMContentLoaded", () => {
    console.log("Called the DOMContentLoaded event");
    console.log("resolverType: " + window.resolverType);
    console.log("resolverOption: " + window.resolverOption);


    if (resolverType) {
        resolverSelection.value = window.resolverType;

        if ( window.resolverType === "nginx" || window.resolverType === "homeassistant") {
            populateResolverOptions();

            if (window.resolverOption) {
                resolverOptionSelect.value = window.resolverOption;
            }
        }
    }
});

// Attach event listeners to the new button IDs
generateButton.addEventListener("click", submitGenerate);
copyButton.addEventListener("click", copyTemplateOutputToClipboard);
saveButton.addEventListener("click", submitSaveForm);

// Optional: hide nginx dropdown on page load
resolverOptionContainer.style.display = "none";
