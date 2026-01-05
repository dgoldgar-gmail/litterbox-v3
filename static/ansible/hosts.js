document.addEventListener("DOMContentLoaded", () => {
  console.log(inventory);
  renderInventory(inventory);

  document
    .getElementById("provision-form")
    .addEventListener("submit", submitProvision);
});

function renderInventory(inventory) {
  const container = document.getElementById("host-groups");
  container.innerHTML = "";

  const groups = inventory?.all?.children || {};

  Object.entries(groups).forEach(([groupName, groupData]) => {
    container.appendChild(createGroupCard(groupName, groupData));
  });
}

function createGroupCard(groupName, groupData) {
  const card = document.createElement("div");
  card.className = "card mb-3";

  const cardBody = document.createElement("div");
  cardBody.className = "card-body";

  // Header container for Title + Select All
  const headerDiv = document.createElement("div");
  headerDiv.className = "d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom";

  const title = document.createElement("h5");
  title.className = "card-title text-capitalize mb-0";
  title.textContent = groupName;

  const selectAllDiv = document.createElement("div");
  selectAllDiv.className = "form-check";

  const selectAllCb = document.createElement("input");
  selectAllCb.className = "form-check-input";
  selectAllCb.type = "checkbox";
  selectAllCb.id = `select-all-${groupName}`;

  const selectAllLabel = document.createElement("label");
  selectAllLabel.className = "form-check-label small text-muted";
  selectAllLabel.setAttribute("for", selectAllCb.id);
  selectAllLabel.textContent = "Select All";

  selectAllDiv.append(selectAllCb, selectAllLabel);
  headerDiv.append(title, selectAllDiv);
  cardBody.appendChild(headerDiv);

  const hosts = groupData.hosts || {};
  const hostCheckboxes = [];

  // Create and track host checkboxes
  Object.keys(hosts).forEach(host => {
    const hostDiv = createHostCheckbox(groupName, host);
    const cb = hostDiv.querySelector('input');
    hostCheckboxes.push(cb);
    cardBody.appendChild(hostDiv);
  });

  // Listener: Master checkbox toggles all children
  selectAllCb.addEventListener("change", (e) => {
    hostCheckboxes.forEach(cb => {
      cb.checked = e.target.checked;
    });
  });

  // Listener: Children toggle the Master checkbox state
  hostCheckboxes.forEach(cb => {
    cb.addEventListener("change", () => {
      const allChecked = hostCheckboxes.every(h => h.checked);
      const someChecked = hostCheckboxes.some(h => h.checked);

      selectAllCb.checked = allChecked;
      // Shows a dash if some (but not all) are selected
      selectAllCb.indeterminate = someChecked && !allChecked;
    });
  });

  card.appendChild(cardBody);
  return card;
}

/**
 * Creates the individual host checkbox row
 */
function createHostCheckbox(group, host) {
  const div = document.createElement("div");
  div.className = "form-check";

  const checkbox = document.createElement("input");
  checkbox.className = "form-check-input";
  checkbox.type = "checkbox";
  checkbox.id = `cb-${group}-${host}`; // Added prefix for safety
  checkbox.value = host;
  checkbox.name = "hosts";

  const label = document.createElement("label");
  label.className = "form-check-label";
  label.setAttribute("for", checkbox.id);
  label.textContent = host;

  div.appendChild(checkbox);
  div.appendChild(label);

  return div;
}

function submitProvision(event) {
  event.preventDefault();

  const selectedHosts = Array.from(
    document.querySelectorAll("input[name=hosts]:checked")
  ).map(cb => cb.value);

  if (selectedHosts.length === 0) {
    alert("Select at least one host.");
    return;
  }

  fetch(provisionBaseUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      hosts: selectedHosts
    })
  })
  .then(res => {
    console.log(res)
    if (!res.ok) throw new Error("Provisioning failed");
    return res.json();
  })
  .then(data => {
    console.log("Provisioning started:", data);
  })
  .catch(err => {
    console.error(err);
    alert(err.message);
  });
}
