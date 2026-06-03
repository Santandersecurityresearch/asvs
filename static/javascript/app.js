(function () {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("asvs.theme", theme);
  }

  const savedTheme = localStorage.getItem("asvs.theme");
  if (savedTheme) {
    applyTheme(savedTheme);
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    applyTheme("dark");
  }

  document.addEventListener("click", function (event) {
    const themeToggle = event.target.closest("[data-theme-toggle]");
    if (themeToggle) {
      const nextTheme = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(nextTheme);
    }

    const modalTrigger = event.target.closest("[data-modal-target]");
    if (modalTrigger) {
      const modal = document.querySelector(modalTrigger.getAttribute("data-modal-target"));
      if (modal) modal.classList.add("is-open");
    }

    const modalClose = event.target.closest("[data-modal-close]");
    if (modalClose || event.target.classList.contains("modal")) {
      const modal = event.target.closest(".modal") || event.target;
      if (modal) modal.classList.remove("is-open");
    }
  });

  function statusClass(status) {
    return `status-pill status-${status}`;
  }

  function updateMetric(selector, value) {
    const element = document.querySelector(selector);
    if (element) element.textContent = value;
  }

  function updateWorkspaceMetrics(metrics) {
    if (!metrics) return;
    updateMetric("[data-metric='complete']", metrics.complete);
    updateMetric("[data-metric='incomplete']", metrics.incomplete);
    updateMetric("[data-metric='review']", metrics.review);
    updateMetric("[data-metric='na']", metrics.na);
    updateMetric("[data-metric='percentage']", `${metrics.percentage}%`);
    const bar = document.querySelector("[data-metric='progress-bar']");
    if (bar) bar.style.width = `${metrics.percentage}%`;
  }

  async function saveRequirement(form) {
    const state = form.querySelector("[data-save-state]");
    if (state) state.textContent = "Saving";
    const response = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      if (state) state.textContent = "Error";
      return;
    }
    updateWorkspaceMetrics(data.metrics);
    const card = form.closest("[data-requirement-card]");
    if (card) {
      const pill = card.querySelector("[data-status-pill]");
      const select = form.querySelector("select[name='status']");
      if (pill && select) {
        pill.className = statusClass(select.value);
        pill.textContent = select.options[select.selectedIndex].text;
      }
    }
    if (state) state.textContent = "Saved";
  }

  let saveTimers = new WeakMap();
  document.addEventListener("input", function (event) {
    const form = event.target.closest("[data-autosave-form]");
    if (!form) return;
    clearTimeout(saveTimers.get(form));
    saveTimers.set(form, setTimeout(function () {
      saveRequirement(form);
    }, 450));
  });

  document.addEventListener("change", function (event) {
    const form = event.target.closest("[data-autosave-form]");
    if (form) saveRequirement(form);
  });
})();
