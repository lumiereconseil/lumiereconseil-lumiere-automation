(() => {
  const box = document.querySelector('[data-progress-checklist]');
  if (!box) return;
  const inputs = [...box.querySelectorAll('input[data-step]')];
  const status = box.querySelector('.progress-status');
  const key = 'rakuten-referral-progress-v1';
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(key) || '{}'); } catch (_) {}
  const render = () => {
    const done = inputs.filter((input) => input.checked).length;
    status.textContent = `完了 ${done} / ${inputs.length}`;
  };
  inputs.forEach((input) => {
    input.checked = Boolean(saved[input.dataset.step]);
    input.addEventListener('change', () => {
      saved[input.dataset.step] = input.checked;
      localStorage.setItem(key, JSON.stringify(saved));
      render();
    });
  });
  render();
})();
