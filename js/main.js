/**
 * Portfolio interactions — no dependencies.
 *  - header state + mobile navigation (accessible, Esc / focus handling)
 *  - active section in the nav
 *  - reveal-on-scroll
 *  - subtle hero parallax (pointer + scroll) and project image parallax
 *  - process timeline progress
 * Motion is skipped entirely when the user prefers reduced motion.
 */
(() => {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  const desktopNav = window.matchMedia("(min-width: 768px)");

  const header = document.querySelector("[data-header]");
  const toggle = document.querySelector("[data-nav-toggle]");
  const toggleLabel = document.querySelector("[data-nav-label]");
  const nav = document.querySelector("[data-nav]");
  const navLinks = [...document.querySelectorAll("[data-nav-link]")];
  const outside = [document.querySelector("main"), document.querySelector(".site-footer")];

  /* ---------------------------------------------------------- Header -- */

  const updateHeader = () => {
    header.classList.toggle("is-scrolled", window.scrollY > 8);
  };

  /* ------------------------------------------------------ Mobile nav -- */

  const setNav = (open, { restoreFocus = false } = {}) => {
    header.classList.toggle("is-open", open);
    document.body.classList.toggle("nav-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggleLabel.textContent = open ? "Cerrar menú" : "Abrir menú";
    // Keep keyboard and screen-reader focus inside the open menu.
    outside.forEach((el) => el && (el.inert = open));
    if (open) navLinks[0].focus();
    else if (restoreFocus) toggle.focus();
  };

  toggle.addEventListener("click", () => {
    setNav(toggle.getAttribute("aria-expanded") !== "true");
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && header.classList.contains("is-open")) {
      setNav(false, { restoreFocus: true });
    }
  });

  nav.addEventListener("click", (event) => {
    const link = event.target.closest("a[href^='#']");
    if (!link || !header.classList.contains("is-open")) return;
    // The open menu locks scrolling and makes <main> inert, so the browser's
    // default jump would be swallowed: close first, then scroll explicitly.
    event.preventDefault();
    setNav(false);
    const target = document.querySelector(link.getAttribute("href"));
    if (!target) return;
    history.pushState(null, "", link.getAttribute("href"));
    target.scrollIntoView({ behavior: reduceMotion.matches ? "auto" : "smooth" });
    target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: true });
  });

  desktopNav.addEventListener("change", (event) => {
    if (event.matches && header.classList.contains("is-open")) setNav(false);
  });

  /* ------------------------------------------------- Active section -- */

  // Sections without their own nav entry highlight the closest parent link.
  const sectionToLink = { home: "home", about: "about", skills: "about", projects: "projects", process: "projects", contact: "contact" };

  const setActive = (id) => {
    const target = `#${sectionToLink[id] || id}`;
    navLinks.forEach((link) => {
      if (link.getAttribute("href") === target) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    });
  };

  const sectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) setActive(entry.target.id);
      });
    },
    { rootMargin: "-45% 0px -50% 0px" }
  );
  document.querySelectorAll("main section[id]").forEach((section) => sectionObserver.observe(section));

  /* ---------------------------------------------------------- Reveal -- */

  const revealTargets = document.querySelectorAll("[data-reveal]");
  if ("IntersectionObserver" in window) {
    const revealObserver = new IntersectionObserver(
      (entries, observer) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.12 }
    );
    revealTargets.forEach((el) => revealObserver.observe(el));
  } else {
    revealTargets.forEach((el) => el.classList.add("is-visible"));
  }

  /* --------------------------------------------------------- Process -- */

  const processList = document.querySelector("[data-process]");
  const steps = processList ? [...processList.querySelectorAll(".step")] : [];

  const updateProcess = () => {
    if (!processList) return;
    const rect = processList.getBoundingClientRect();
    const vh = window.innerHeight;
    const start = vh * 0.8;
    const progress = Math.min(Math.max((start - rect.top) / (rect.height + vh * 0.2), 0), 1);
    processList.style.setProperty("--progress", progress.toFixed(3));
    steps.forEach((step) => {
      step.classList.toggle("is-active", step.getBoundingClientRect().top < start - vh * 0.05);
    });
  };

  /* ---------------------------------------------------------- Motion -- */

  const heroArt = document.querySelector("[data-hero-art]");
  const projectImages = [...document.querySelectorAll(".project__frame img")];

  const pointer = { x: 0, y: 0 };      // target, -1..1
  const current = { x: 0, y: 0 };      // eased value
  let frame = 0;

  const lerp = (a, b, t) => a + (b - a) * t;

  const render = () => {
    frame = 0;
    const motion = !reduceMotion.matches;

    if (motion && heroArt) {
      current.x = lerp(current.x, pointer.x, 0.08);
      current.y = lerp(current.y, pointer.y, 0.08);
      const scroll = Math.min(window.scrollY, window.innerHeight);
      const x = current.x * 14;
      const y = current.y * 10 + scroll * 0.12;
      heroArt.style.transform = `translate3d(${x.toFixed(2)}px, ${y.toFixed(2)}px, 0)`;
    }

    if (motion) {
      const vh = window.innerHeight;
      projectImages.forEach((img) => {
        const rect = img.parentElement.getBoundingClientRect();
        if (rect.bottom < 0 || rect.top > vh) return;
        // -1 when the frame enters from below, 1 when it leaves at the top.
        const progress = (vh / 2 - (rect.top + rect.height / 2)) / (vh / 2 + rect.height / 2);
        img.style.transform = `translate3d(0, ${(progress * 14).toFixed(2)}px, 0) scale(1.06)`;
      });
    }

    updateProcess();

    // Keep easing towards the pointer until it settles.
    if (motion && (Math.abs(current.x - pointer.x) > 0.001 || Math.abs(current.y - pointer.y) > 0.001)) {
      schedule();
    }
  };

  const schedule = () => {
    if (!frame) frame = requestAnimationFrame(render);
  };

  window.addEventListener("scroll", () => {
    updateHeader();
    schedule();
  }, { passive: true });

  window.addEventListener("resize", schedule, { passive: true });

  window.addEventListener("pointermove", (event) => {
    if (!finePointer.matches || reduceMotion.matches) return;
    pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
    pointer.y = (event.clientY / window.innerHeight) * 2 - 1;
    schedule();
  }, { passive: true });

  reduceMotion.addEventListener("change", () => {
    if (reduceMotion.matches) {
      if (heroArt) heroArt.style.transform = "";
      projectImages.forEach((img) => (img.style.transform = ""));
    }
    schedule();
  });

  /* ------------------------------------------------------------ Init -- */

  const year = document.querySelector("[data-year]");
  if (year) year.textContent = String(new Date().getFullYear());

  updateHeader();
  schedule();
})();
