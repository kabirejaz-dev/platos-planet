document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector("[data-menu-toggle]");
  const menu = document.querySelector("[data-menu]");
  if (toggle && menu) {
    toggle.addEventListener("click", () => menu.classList.toggle("open"));
  }

  document.querySelectorAll(".toast").forEach((toast) => {
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(-8px)";
      setTimeout(() => toast.remove(), 350);
    }, 4200);
  });
});
