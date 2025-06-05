document.addEventListener('DOMContentLoaded', () => {
  const hamburger = document.querySelector('.hamburger');
  const navLinks = document.querySelector('.nav-links');
  const dropdown = document.querySelector('.dropdown');
  const dropdownToggle = dropdown.querySelector('.dropdown-toggle');

  hamburger.addEventListener('click', () => {
    navLinks.classList.toggle('open');
  });

  dropdownToggle.addEventListener('click', () => {
    dropdown.classList.toggle('open');
  });

  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target) && !dropdownToggle.contains(e.target)) {
      dropdown.classList.remove('open');
    }
  });
});