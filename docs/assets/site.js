"use strict";

// Progressive enhancement only: downloads, status and evidence work without JS.
for (const button of document.querySelectorAll("button[data-copy-target]")) {
  button.addEventListener("click", async () => {
    const target = document.getElementById(button.dataset.copyTarget);
    const label = button.textContent;
    try {
      if (!target || !navigator.clipboard) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(target.textContent);
      button.textContent = "Copied";
    } catch {
      button.textContent = "Select text to copy";
    }
    window.setTimeout(() => { button.textContent = label; }, 2500);
  });
}

for (const input of document.querySelectorAll("input[data-filter-table]")) {
  const table = document.getElementById(input.dataset.filterTable);
  if (!table) continue;
  input.addEventListener("input", () => {
    const query = input.value.trim().toLocaleLowerCase();
    for (const row of table.querySelectorAll("tbody tr")) {
      row.hidden = !row.textContent.toLocaleLowerCase().includes(query);
    }
  });
}
