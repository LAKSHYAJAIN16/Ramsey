// Mobile menu toggle
const menuToggle = document.getElementById('menuToggle');
const mobileMenu = document.getElementById('mobileMenu');

if (menuToggle && mobileMenu) {
  menuToggle.addEventListener('click', () => {
    mobileMenu.classList.toggle('open');
  });
  mobileMenu.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => mobileMenu.classList.remove('open'));
  });
}

// Nav background on scroll
const navBar = document.querySelector('.nav-bar');
if (navBar) {
  const onScroll = () => {
    if (window.scrollY > 20) {
      navBar.style.background = 'rgba(255,255,255,0.7)';
      navBar.style.boxShadow = '0 2px 20px rgba(74,26,0,0.08)';
    } else {
      navBar.style.background = 'rgba(255,255,255,0.04)';
      navBar.style.boxShadow = 'none';
    }
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

// FAQ accordion
document.querySelectorAll('.faq-item').forEach((item) => {
  const question = item.querySelector('.faq-question');
  question.addEventListener('click', () => {
    const isOpen = item.classList.contains('open');
    document.querySelectorAll('.faq-item.open').forEach((openItem) => {
      if (openItem !== item) {
        openItem.classList.remove('open');
        openItem.querySelector('.faq-question').setAttribute('aria-expanded', 'false');
      }
    });
    item.classList.toggle('open', !isOpen);
    question.setAttribute('aria-expanded', String(!isOpen));
  });
});

// Reveal on scroll
const revealEls = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window && revealEls.length) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );
  revealEls.forEach((el) => observer.observe(el));
}

// Dish forms actually launch the real app at /app/?q=<dish>, not a fake waitlist
function handleDishSubmit(form, inputId) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const input = document.getElementById(inputId);
    if (!input || !input.value.trim()) return;
    window.location.href = `/app/?q=${encodeURIComponent(input.value.trim())}`;
  });
}
handleDishSubmit(document.getElementById('heroForm'), 'heroDish');
handleDishSubmit(document.getElementById('ctaForm'), 'ctaDish');

// Account state belongs to the website launcher; the WebXR app consumes the
// same backend profile once the cook enters a mode.
const siteAuth = document.getElementById('site-auth');
const siteRank = document.getElementById('site-rank');
fetch('/api/me').then((response) => response.json()).then((account) => {
  if (account.authenticated) {
    siteRank.textContent = `${account.profile.display_name} · ${account.profile.rank}`;
    siteAuth.textContent = 'Profile saved';
    siteAuth.disabled = true;
  } else if (!account.oauth_ready) {
    siteAuth.textContent = 'Sign-in unavailable';
    siteAuth.disabled = true;
  }
}).catch(() => { siteAuth.disabled = true; siteAuth.textContent = 'Sign-in unavailable'; });
if (siteAuth) siteAuth.addEventListener('click', () => { window.location.href = '/api/auth/google/login'; });

// Share button
const shareBtn = document.getElementById('shareBtn');
if (shareBtn) {
  shareBtn.addEventListener('click', async () => {
    const shareData = { title: 'Ramsey — AI Chef in Your Kitchen', url: window.location.href };
    if (navigator.share) {
      try { await navigator.share(shareData); } catch (err) { /* user cancelled */ }
    } else if (navigator.clipboard) {
      await navigator.clipboard.writeText(window.location.href);
    }
  });
}

// Smooth scroll for in-page anchors
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener('click', (e) => {
    const targetId = anchor.getAttribute('href');
    if (targetId.length > 1) {
      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  });
});
