// Kays Lumière Main Script
// Handles UI interactions. Cart and Product logic is now server-side.

// Navigation Toggle
const navToggle = document.querySelector("[data-nav-toggle]");
const navDrawer = document.querySelector("[data-nav-drawer]");
const navOverlay = document.querySelector("[data-nav-overlay]");
const navClose = document.querySelector("[data-nav-close]");

function toggleNav() {
  const isOpen = navDrawer.getAttribute("aria-hidden") === "false";
  navDrawer.setAttribute("aria-hidden", isOpen);
  navOverlay.setAttribute("aria-hidden", isOpen);
  
  if (!isOpen) {
    document.body.classList.add("nav-open");
    document.body.style.overflow = "hidden";
  } else {
    document.body.classList.remove("nav-open");
    document.body.style.overflow = "";
  }
}

if (navToggle) {
    navToggle.addEventListener("click", toggleNav);
    navOverlay.addEventListener("click", toggleNav);
    navClose.addEventListener("click", toggleNav);
}

// Lightbox (Simple implementation)
const lightboxTriggers = document.querySelectorAll("[data-lightbox-trigger]");
if (lightboxTriggers.length > 0) {
    // Basic lightbox functionality can be added here if needed
    // For now, we rely on default behavior or future implementation
    lightboxTriggers.forEach(trigger => {
        trigger.style.cursor = "pointer";
        trigger.addEventListener("click", () => {
            // Placeholder for lightbox
            console.log("Lightbox trigger clicked");
        });
    });
}

// Animations on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px"
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.querySelectorAll('.fade-in, .editorial-animate').forEach(el => {
    observer.observe(el);
});

// Product Thumbs (Product Detail Page)
const thumbs = document.querySelectorAll("[data-thumb]");
const mainImage = document.querySelector("[data-main-image]");

if (thumbs.length > 0 && mainImage) {
    thumbs.forEach(thumb => {
        thumb.addEventListener("click", () => {
            // Update main image source
            mainImage.src = thumb.src;
            
            // Update active state
            thumbs.forEach(t => t.classList.remove("active"));
            thumb.classList.add("active");
        });
    });
}
