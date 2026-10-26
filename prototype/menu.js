// Marque l'onglet de la catégorie visible et le garde visible dans la barre.
(() => {
  const links = [...document.querySelectorAll(".tabs a")];
  const bar = document.querySelector(".tabs ul");
  if (!links.length || !("IntersectionObserver" in window)) return;
  const calm = matchMedia("(prefers-reduced-motion: reduce)");

  const setCurrent = (id) => {
    for (const a of links) {
      const on = a.hash === "#" + id;
      if (on) {
        a.setAttribute("aria-current", "true");
        bar.scrollTo({ left: a.parentElement.offsetLeft - 16, behavior: calm.matches ? "auto" : "smooth" });
      } else {
        a.removeAttribute("aria-current");
      }
    }
  };

  const io = new IntersectionObserver(
    (entries) => entries.forEach((en) => en.isIntersecting && setCurrent(en.target.id)),
    { rootMargin: "-72px 0px -70% 0px" }
  );
  document.querySelectorAll("main section").forEach((s) => io.observe(s));
})();

// Garde la section en cours quand on change de langue.
document.querySelectorAll(".lang-btn").forEach((a) =>
  a.addEventListener("click", () => { if (location.hash) a.href = a.href.split("#")[0] + location.hash; })
);
