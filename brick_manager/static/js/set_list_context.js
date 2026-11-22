(() => {
  const list = document.getElementById('sets-table');
  const filters = document.getElementById('set-filters');
  const filterValues = () => new URLSearchParams(new FormData(filters)).toString();
  const originalFilters = filterValues();
  function showFilterDraft() {
    document.getElementById('filter-draft').hidden = filterValues() === originalFilters;
  }
  filters.addEventListener('input', showFilterDraft);
  filters.addEventListener('change', showFilterDraft);

  const listUrl = list.dataset.listUrl;
  const storageKey = box => 'set-list-position:' + listUrl + ':' + box;
  const overview = document.getElementById('collection-overview');
  const tableScroll = list.querySelector('.table-responsive');
  list.addEventListener('click', event => {
    const link = event.target.closest('a.set-detail-link');
    if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const box = link.dataset.userSetId;
    history.replaceState({ ...history.state, openedSetBox: box }, '');
    try {
      sessionStorage.setItem(storageKey(box), JSON.stringify({
        scrollY: window.scrollY, tableLeft: tableScroll.scrollLeft, overviewOpen: overview.open
      }));
    } catch { /* Focus restoration also works when storage is unavailable. */ }
  });
  window.addEventListener('pageshow', event => {
    const viaHistory = event.persisted || performance.getEntriesByType('navigation')[0]?.type === 'back_forward';
    const openedBox = history.state?.openedSetBox;
    if (viaHistory && openedBox) {
      // Requery even without a client marker (a native form or another tab may have saved).
      const target = new URL(listUrl, location.origin);
      target.searchParams.set('returned_box', openedBox);
      target.hash = 'set-box-' + openedBox;
      history.replaceState({ ...history.state, openedSetBox: null }, '', target);
      location.reload();
      return;
    }
    const box = list.dataset.returnBox;
    if (!box) return;
    const link = document.getElementById('set-box-' + box)?.querySelector('a.set-detail-link');
    const focusTarget = link || document.getElementById('set-results-heading');
    let position;
    try {
      const saved = sessionStorage.getItem(storageKey(box));
      if (saved !== null) position = JSON.parse(saved);
    } catch { /* Fall back to scrolling the focused result into view. */ }
    if (position) {
      overview.open = position.overviewOpen;
      tableScroll.scrollLeft = position.tableLeft;
      if (link) window.scrollTo(0, position.scrollY);
    }
    focusTarget.focus({ preventScroll: true });
    const rect = focusTarget.getBoundingClientRect();
    if (!link || rect.top < 0 || rect.bottom > innerHeight || rect.left < 0 || rect.right > innerWidth) {
      focusTarget.scrollIntoView({ block: 'center', inline: 'nearest' });
    }
  });
})();
