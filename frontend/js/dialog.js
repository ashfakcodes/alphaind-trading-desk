/**
 * Alphaind UI System: Built-in Dialog Modals (Alert / Confirm) & Minimal Cookie Banner
 */

(function () {
  'use strict';

  // --- SVG Icons ---
  const ICONS = {
    danger: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#f43f5e" stroke-width="2.2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    warning: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
    success: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
    info: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1993f8" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`
  };

  let _dialogResolve = null;

  function ensureDialogDOM() {
    if (document.getElementById('alphaindDialogBackdrop')) return;

    const dialogEl = document.createElement('div');
    dialogEl.id = 'alphaindDialogBackdrop';
    dialogEl.className = 'alphaind-dialog-backdrop';
    dialogEl.innerHTML = `
      <div class="alphaind-dialog-card" id="alphaindDialogCard" role="dialog" aria-modal="true">
        <div class="alphaind-dialog-header">
          <div class="alphaind-dialog-icon" id="alphaindDialogIcon"></div>
          <div class="alphaind-dialog-titles">
            <span class="alphaind-dialog-badge" id="alphaindDialogBadge">NOTIFICATION</span>
            <h3 class="alphaind-dialog-title" id="alphaindDialogTitle">Desk Notice</h3>
          </div>
        </div>
        <div class="alphaind-dialog-body" id="alphaindDialogMessage"></div>
        <div class="alphaind-dialog-actions" id="alphaindDialogActions">
          <button type="button" class="alphaind-dialog-btn-cancel" id="alphaindDialogCancelBtn">Cancel</button>
          <button type="button" class="alphaind-dialog-btn-confirm" id="alphaindDialogConfirmBtn">Confirm</button>
        </div>
      </div>
    `;
    document.body.appendChild(dialogEl);

    // Event handlers
    const backdrop = document.getElementById('alphaindDialogBackdrop');
    const cancelBtn = document.getElementById('alphaindDialogCancelBtn');
    const confirmBtn = document.getElementById('alphaindDialogConfirmBtn');

    cancelBtn.addEventListener('click', () => closeDialog(false));
    confirmBtn.addEventListener('click', () => closeDialog(true));
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        closeDialog(false);
      }
    });

    document.addEventListener('keydown', (e) => {
      if (!backdrop.classList.contains('active')) return;
      if (e.key === 'Escape') {
        e.preventDefault();
        closeDialog(false);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        closeDialog(true);
      }
    });
  }

  function closeDialog(result) {
    const backdrop = document.getElementById('alphaindDialogBackdrop');
    if (backdrop) {
      backdrop.classList.remove('active');
    }
    if (_dialogResolve) {
      const resolve = _dialogResolve;
      _dialogResolve = null;
      resolve(result);
    }
  }

  /**
   * Built-in Custom Confirm Dialog (Promise-based)
   */
  window.showConfirmDialog = function (options) {
    ensureDialogDOM();
    const opts = typeof options === 'string' ? { message: options } : (options || {});
    const title = opts.title || 'Security Confirmation';
    const message = opts.message || '';
    const confirmText = opts.confirmText || 'Confirm';
    const cancelText = opts.cancelText || 'Cancel';
    const type = opts.type || (opts.isDanger ? 'danger' : 'warning');
    const badge = opts.badge || (type === 'danger' ? 'SECURITY GUARD' : 'CONFIRMATION');

    const backdrop = document.getElementById('alphaindDialogBackdrop');
    const iconEl = document.getElementById('alphaindDialogIcon');
    const titleEl = document.getElementById('alphaindDialogTitle');
    const badgeEl = document.getElementById('alphaindDialogBadge');
    const msgEl = document.getElementById('alphaindDialogMessage');
    const cancelBtn = document.getElementById('alphaindDialogCancelBtn');
    const confirmBtn = document.getElementById('alphaindDialogConfirmBtn');

    iconEl.className = `alphaind-dialog-icon ${type}`;
    iconEl.innerHTML = ICONS[type] || ICONS.warning;
    badgeEl.textContent = badge;
    titleEl.textContent = title;
    msgEl.textContent = message;

    cancelBtn.style.display = 'inline-flex';
    cancelBtn.textContent = cancelText;

    confirmBtn.textContent = confirmText;
    confirmBtn.className = `alphaind-dialog-btn-confirm ${type}`;

    backdrop.classList.add('active');

    return new Promise((resolve) => {
      _dialogResolve = resolve;
      confirmBtn.focus();
    });
  };

  /**
   * Built-in Custom Alert Dialog (Promise-based)
   */
  window.showAlertDialog = function (options) {
    ensureDialogDOM();
    const opts = typeof options === 'string' ? { message: options } : (options || {});
    const title = opts.title || 'Desk Alert';
    const message = opts.message || '';
    const okText = opts.okText || 'Acknowledge';
    const type = opts.type || 'info';
    const badge = opts.badge || (type === 'success' ? 'BITGET ENGINE' : (type === 'error' ? 'SYSTEM ERROR' : 'DESK NOTICE'));

    const backdrop = document.getElementById('alphaindDialogBackdrop');
    const iconEl = document.getElementById('alphaindDialogIcon');
    const titleEl = document.getElementById('alphaindDialogTitle');
    const badgeEl = document.getElementById('alphaindDialogBadge');
    const msgEl = document.getElementById('alphaindDialogMessage');
    const cancelBtn = document.getElementById('alphaindDialogCancelBtn');
    const confirmBtn = document.getElementById('alphaindDialogConfirmBtn');

    iconEl.className = `alphaind-dialog-icon ${type}`;
    iconEl.innerHTML = ICONS[type] || ICONS.info;
    badgeEl.textContent = badge;
    titleEl.textContent = title;
    msgEl.textContent = message;

    cancelBtn.style.display = 'none';

    confirmBtn.textContent = okText;
    confirmBtn.className = `alphaind-dialog-btn-confirm ${type}`;

    backdrop.classList.add('active');

    return new Promise((resolve) => {
      _dialogResolve = () => resolve();
      confirmBtn.focus();
    });
  };

  // Override standard window.alert with built-in modal
  const _nativeAlert = window.alert;
  window.alert = function (message) {
    let type = 'info';
    let title = 'Desk Notice';

    const str = String(message);
    if (str.includes('✓') || str.toLowerCase().includes('executed') || str.toLowerCase().includes('success')) {
      type = 'success';
      title = 'Execution Confirmed';
    } else if (str.toLowerCase().includes('error') || str.toLowerCase().includes('failed') || str.toLowerCase().includes('timeout')) {
      type = 'danger';
      title = 'Desk Alert';
    } else if (str.toLowerCase().includes('preserved') || str.toLowerCase().includes('dismissed') || str.toLowerCase().includes('warning')) {
      type = 'warning';
      title = 'Trade Dismissed';
    }

    window.showAlertDialog({
      title,
      message: str,
      type,
      okText: 'Acknowledge'
    });
  };

  // --- Minimal Solid #1993f8 Cookie Banner ---
  function initCookieBanner() {
    const consent = localStorage.getItem('alphaind_cookie_consent');
    if (consent) return; // Already answered

    if (document.getElementById('alphaindCookieBanner')) return;

    const banner = document.createElement('div');
    banner.id = 'alphaindCookieBanner';
    banner.className = 'cookie-banner-solid';
    banner.innerHTML = `
      <div class="cbs-content">
        <div class="cbs-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#000000" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 0-1.5 19.9"/><circle cx="8.5" cy="8.5" r="1" fill="#000"/><circle cx="15.5" cy="8.5" r="1" fill="#000"/><circle cx="10" cy="14" r="1" fill="#000"/><circle cx="14.5" cy="14.5" r="1" fill="#000"/></svg>
        </div>
        <div class="cbs-text">
          <strong>Storage &amp; Session Privacy:</strong> We use encrypted browser local storage to preserve your client-side Bitget vault and telemetry. No third-party trackers.
        </div>
      </div>
      <div class="cbs-actions">
        <button type="button" class="cbs-btn-secondary" id="cbsBtnEssential">Essential Only</button>
        <button type="button" class="cbs-btn-primary" id="cbsBtnAccept">Accept All</button>
      </div>
    `;

    document.body.appendChild(banner);

    const acceptBtn = document.getElementById('cbsBtnAccept');
    const essentialBtn = document.getElementById('cbsBtnEssential');

    function dismissBanner(choice) {
      localStorage.setItem('alphaind_cookie_consent', choice);
      banner.classList.add('hidden');
      setTimeout(() => {
        if (banner.parentNode) banner.parentNode.removeChild(banner);
      }, 400);
    }

    if (acceptBtn) acceptBtn.addEventListener('click', () => dismissBanner('all'));
    if (essentialBtn) essentialBtn.addEventListener('click', () => dismissBanner('essential'));
  }

  // Initialize on load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      ensureDialogDOM();
      initCookieBanner();
    });
  } else {
    ensureDialogDOM();
    initCookieBanner();
  }
})();
