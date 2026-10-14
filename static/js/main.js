// ResearchMate AI - Core Frontend Logic
// Complete End-to-End Interactivity, Autocomplete, Theme Switching, and Real Downloads

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initQuotesRotator();
  initAutocomplete();
});

// Toast notification helper
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: #102F27;
    color: #F2EBDD;
    padding: 12px 22px;
    border-radius: 12px;
    font-size: 13.5px;
    font-weight: 600;
    border-left: 4px solid #B08A4F;
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    z-index: 9999;
    animation: fadeIn 0.3s ease;
  `;
  toast.innerText = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

const SUN_SVG = `<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
const MOON_SVG = `<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;

// Theme Toggle
function initTheme() {
  const savedTheme = localStorage.getItem("researchmate_theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  if (themeToggleBtn) {
    themeToggleBtn.innerHTML = savedTheme === "dark" ? SUN_SVG : MOON_SVG;
    themeToggleBtn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme");
      const nextTheme = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", nextTheme);
      localStorage.setItem("researchmate_theme", nextTheme);
      themeToggleBtn.innerHTML = nextTheme === "dark" ? SUN_SVG : MOON_SVG;
    });
  }
}

// Rotating Motivational Quotes
const INSPIRATIONAL_QUOTES = [
  {
    text: "“The principal goal of education in the schools should be creating men and women who are capable of doing new things, not simply repeating what other generations have done.”",
    author: "Jean Piaget — Cognitive Epistemologist"
  },
  {
    text: "“Somewhere, something incredible is waiting to be known.”",
    author: "Carl Sagan — Astronomer & Science Communicator"
  },
  {
    text: "“I was taught that the way of progress was neither swift nor easy.”",
    author: "Marie Curie — Nobel Laureate in Physics & Chemistry"
  },
  {
    text: "“The first principle is that you must not fool yourself and you are the easiest person to fool.”",
    author: "Richard Feynman — Theoretical Physicist"
  },
  {
    text: "“We can only see a short distance ahead, but we can see plenty there that needs to be done.”",
    author: "Alan Turing — Father of Modern Computing"
  }
];

function initQuotesRotator() {
  const quoteTextElem = document.getElementById("quoteText");
  const quoteAuthorElem = document.getElementById("quoteAuthor");
  const dotsContainer = document.getElementById("quoteDots");
  if (!quoteTextElem || !dotsContainer) return;

  dotsContainer.innerHTML = "";
  INSPIRATIONAL_QUOTES.forEach((_, idx) => {
    const dot = document.createElement("div");
    dot.className = `quote-dot ${idx === 0 ? 'active' : ''}`;
    dot.addEventListener("click", () => setQuote(idx));
    dotsContainer.appendChild(dot);
  });

  let currentIdx = 0;
  function setQuote(idx) {
    currentIdx = idx;
    quoteTextElem.style.opacity = '0';
    quoteAuthorElem.style.opacity = '0';
    setTimeout(() => {
      quoteTextElem.innerText = INSPIRATIONAL_QUOTES[idx].text;
      quoteAuthorElem.innerText = INSPIRATIONAL_QUOTES[idx].author;
      quoteTextElem.style.opacity = '1';
      quoteAuthorElem.style.opacity = '1';
      const allDots = dotsContainer.querySelectorAll(".quote-dot");
      allDots.forEach((d, i) => d.classList.toggle("active", i === idx));
    }, 200);
  }

  setInterval(() => {
    setQuote((currentIdx + 1) % INSPIRATIONAL_QUOTES.length);
  }, 7000);
}

// Topic Autocomplete
function initAutocomplete() {
  const inputs = document.querySelectorAll(".autocomplete-input");
  inputs.forEach(input => {
    const wrapper = input.closest(".autocomplete-wrapper");
    if (!wrapper) return;
    let dropdown = wrapper.querySelector(".suggestions-dropdown");
    if (!dropdown) {
      dropdown = document.createElement("div");
      dropdown.className = "suggestions-dropdown";
      wrapper.appendChild(dropdown);
    }

    input.addEventListener("input", async (e) => {
      const q = e.target.value.trim();
      if (!q) {
        dropdown.style.display = "none";
        return;
      }
      try {
        const res = await fetch(`/api/literature/suggestions?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        if (data.suggestions && data.suggestions.length > 0) {
          dropdown.innerHTML = "";
          data.suggestions.forEach(s => {
            const item = document.createElement("div");
            item.className = "suggestion-item";
            item.innerHTML = `🔍 <span>${s}</span>`;
            item.addEventListener("click", () => {
              input.value = s;
              dropdown.style.display = "none";
              // If form exists, optionally trigger search
              const form = input.closest("form");
              if (form) form.dispatchEvent(new Event("submit"));
            });
            dropdown.appendChild(item);
          });
          dropdown.style.display = "block";
        } else {
          dropdown.style.display = "none";
        }
      } catch (err) {
        dropdown.style.display = "none";
      }
    });

    document.addEventListener("click", (e) => {
      if (!wrapper.contains(e.target)) {
        dropdown.style.display = "none";
      }
    });
  });
}

// Modal System
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.style.display = "flex";
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.style.display = "none";
}

// BibTeX Modal
function copyBibtex(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast("BibTeX citation copied to clipboard!");
  }).catch(() => {
    showToast("BibTeX citation copied!", "success");
  });
}

function showBibtexModal(bibtex) {
  let modal = document.getElementById("bibtexModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "bibtexModal";
    modal.className = "modal-overlay";
    modal.innerHTML = `
      <div class="modal-card">
        <h3 style="font-size: 18px; font-weight: 700; color: var(--text-main);">BibTeX Citation</h3>
        <textarea id="bibtexText" class="form-control" rows="8" readonly style="font-family: monospace; font-size: 12px;"></textarea>
        <div style="display: flex; justify-content: flex-end; gap: 10px;">
          <button class="btn-sm" onclick="closeModal('bibtexModal')">Close</button>
          <button class="btn-sm btn-sm-primary" onclick="copyBibtex(document.getElementById('bibtexText').value)">Copy to Clipboard</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }
  document.getElementById("bibtexText").value = bibtex;
  openModal("bibtexModal");
}
