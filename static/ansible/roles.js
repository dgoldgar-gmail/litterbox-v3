document.addEventListener("DOMContentLoaded", () => {
    renderTagSelector(sites)

    document
        .getElementById("provision-form")
        .addEventListener("submit", submitProvision);
});

function renderTagSelector(playbook) {
  const listContainer = document.getElementById("tag-list");

  // 1. Extract and Sort Tags
  const tags = new Set();
  playbook.forEach(play => {
    play.roles?.forEach(roleObj => {
      if (roleObj.tags) {
        roleObj.tags.forEach(t => tags.add(t));
      }
    });
  });

  const sortedTags = Array.from(tags).sort();
  listContainer.innerHTML = "";

  // 2. Create vertical list items
  const tagCheckboxes = [];

  sortedTags.forEach(tag => {
    const row = document.createElement("div");
    row.className = "tag-item d-flex align-items-center p-2";

    const checkbox = document.createElement("input");
    checkbox.className = "form-check-input me-3";
    checkbox.type = "checkbox";
    checkbox.id = `tag-${tag}`;
    checkbox.value = tag;
    checkbox.name = "ansible_tags";

    const label = document.createElement("label");
    label.className = "form-check-label flex-grow-1 cursor-pointer text-white";
    label.setAttribute("for", `tag-${tag}`);
    label.textContent = tag;

    row.append(checkbox, label);
    listContainer.appendChild(row);
    tagCheckboxes.push(checkbox);

  });
}

function getSelectedTags() {
  return Array.from(document.querySelectorAll("input[name=ansible_tags]:checked"))
    .map(cb => cb.value);
}

function submitProvision(event) {
  event.preventDefault();

  const selectecTags = Array.from(
    document.querySelectorAll("input[name=ansible_tags]:checked")
  ).map(cb => cb.value);


  if (selectecTags.length === 0) {
    alert("Select at least one host.");
    return;
  }

  fetch(provisionBaseUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      tags: selectecTags
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

