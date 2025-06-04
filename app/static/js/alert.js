document.querySelectorAll('.btn-close').forEach(button => {
  button.addEventListener('click', () => {
    const alert = button.closest('.alert');
    alert.style.opacity = '0';
    setTimeout(() => alert.remove(), 300);
  });
});
