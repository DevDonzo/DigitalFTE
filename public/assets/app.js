(() => {
  const button = document.querySelector("#copy-button");
  const command = document.querySelector("#install-command");

  if (!button || !command) return;

  const label = button.querySelector("span");
  const defaultLabel = label.textContent;
  let resetTimer;

  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(button.dataset.command);
      button.dataset.state = "copied";
      label.textContent = "Copied";

      window.clearTimeout(resetTimer);
      resetTimer = window.setTimeout(() => {
        delete button.dataset.state;
        label.textContent = defaultLabel;
      }, 2500);
    } catch {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(command);
      selection.removeAllRanges();
      selection.addRange(range);
      label.textContent = "Press ⌘C / Ctrl+C";
    }
  });
})();
