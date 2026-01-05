
async function initEditor() {
    const [{ schema_type, schema_data },  { config_type, mapping_data }] = await Promise.all([
        fetch(`/json_editor/api/schema?type=${encodeURIComponent(window.config_type)}`).then(r => r.json()),
        fetch(`/json_editor/api/config?type=${encodeURIComponent(window.config_type)}`).then(r => r.json())
    ]);

    type = schema_type
    const container = document.getElementById("editor");

    const editor = new JSONEditor(container, {
        schema: schema_data,
        theme: "foundation",
        mode: "tree",

        onCreateMenu: function (items, node) {
            // Guard conditions
            if (
              window.config_type === 'applications' &&
              node &&
              Array.isArray(node.path) &&
              node.path.length === 1
            ) {
              const appName = node.path[0]; // top-level key name
              items.push({ type: 'separator' });

              items.push(
                {
                  text: 'Manage',
                  title: `View logs for ${appName}`,
                  click: () => {
                      console.log(appName)
                      console.log(mapping_data)
                      console.log(mapping_data[appName]['name'])
                      const url = manageApplicationUrlBase.replace('__NAME__', mapping_data[appName]['name']);
                      window.location.href = url;
                  }
                }
              );
            }
            return items;
          }
    });

    window.editor = editor;
    await editor.ready;
    editor.set(mapping_data);
}

initEditor();

async function save() {
    const statusEl = document.getElementById("status");
    statusEl.textContent = "Saving...";

    try {
        const payload = {
            config_type: window.config_type,
            mapping_data: editor.get()
        };

        const response = await fetch("/json_editor/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Save failed: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        console.log("Save result:", result);

        statusEl.textContent = "Saved ✔";
    } catch (err) {
        console.error(err);
        statusEl.textContent = err.message;
    }
}
