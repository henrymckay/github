// Theme toggle, live search and delete confirmation; every form still works without it.

function currentTheme() {
  const chosen = document.documentElement.dataset.theme;
  if (chosen) return chosen;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function setUpThemeToggle() {
  const button = document.querySelector("[data-theme-toggle]");
  if (!button) return;
  button.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch (ignored) {}
  });
}

function setUpLiveSearch() {
  const form = document.querySelector("[data-live-search]");
  const results = document.getElementById("results");
  if (!form || !results) return;
  let timer;
  let latest = 0;
  const refresh = async () => {
    const query = new URLSearchParams(new FormData(form));
    for (const [key, value] of [...query]) if (!value) query.delete(key);
    const url = query.toString() ? `/?${query}` : "/";
    const request = ++latest;
    try {
      const response = await fetch(url, { headers: { Accept: "text/html" } });
      if (!response.ok || request !== latest) return;
      const page = new DOMParser().parseFromString(await response.text(), "text/html");
      const fresh = page.getElementById("results");
      if (fresh) results.replaceWith(fresh);
      history.replaceState(null, "", url);
    } catch (ignored) {
      form.submit();
    }
  };
  form.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(refresh, 200);
  });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    refresh();
  });
}

function setUpConfirm() {
  for (const form of document.querySelectorAll("form[data-confirm]")) {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  }
}

setUpThemeToggle();
setUpLiveSearch();
setUpConfirm();
