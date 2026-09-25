/**
 * Alphaind · Bitget Agentic Account OAuth Page Controller
 * Handles token-free RSA handshake, WebCrypto AES-GCM vault encryption, and desk synchronization.
 */

let _oauthPollInterval = null;
let _pendingOAuthSessionId = null;
let _pendingVaultPin = '';

document.addEventListener('DOMContentLoaded', async () => {
  initSpotlight();
  await checkAuthStatusAndParams();
});

// Interactive Spotlight for Background Grid
function initSpotlight() {
  let rafId = null;
  window.addEventListener('mousemove', (e) => {
    if (!rafId) {
      rafId = requestAnimationFrame(() => {
        document.documentElement.style.setProperty('--mouse-x', `${e.clientX}px`);
        document.documentElement.style.setProperty('--mouse-y', `${e.clientY}px`);
        rafId = null;
      });
    }
  }, { passive: true });
}

// Check URL Params & Existing Vault
async function checkAuthStatusAndParams() {
  // 1. Mark that user has visited onboarding
  localStorage.setItem('alphaind_has_visited', 'true');

  // 2. Check if returning from Bitget OAuth redirect (?dataKey=...)
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const dataKey = urlParams.get('dataKey');
    const storedSessionId = sessionStorage.getItem('bitget_oauth_active_session');

    if (dataKey && storedSessionId) {
      showAuthToast('Exchanging Bitget OAuth authorization key...', 'info');
      switchAuthView('waiting');
      const res = await apiFetch('/api/oauth/complete', {
        method: 'POST',
        body: JSON.stringify({ session_id: storedSessionId, data_key: dataKey })
      });

      if (res.ok) {
        const body = await res.json();
        if (body.credentials && window.AlphaindVault) {
          await window.AlphaindVault.saveVault(body.credentials, _pendingVaultPin);
          await syncCredentialsToDesk(body.credentials);
          showAuthToast('Bitget Agentic Subaccount authorized & encrypted!', 'success');
          renderConnectedDetails();
          switchAuthView('connected');
        }
      }

      // Sanitize URL
      const cleanUrl = window.location.origin + window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
      sessionStorage.removeItem('bitget_oauth_active_session');
      return;
    }
  } catch (e) {
    console.error('[OAuth] Redirect handling error:', e);
  }

  // 3. Check existing vault in browser storage
  if (window.AlphaindVault && window.AlphaindVault.hasVault()) {
    const meta = window.AlphaindVault.getMetadata();
    if (meta && meta.mode === 'device_protected') {
      try {
        const creds = await window.AlphaindVault.unlockVault();
        if (creds) {
          await syncCredentialsToDesk(creds);
          renderConnectedDetails();
          switchAuthView('connected');
          return;
        }
      } catch (err) {
        console.warn('[OAuth] Device vault unlock failed:', err);
      }
    } else if (meta && meta.mode === 'pin_protected') {
      if (window.AlphaindVault.isUnlocked()) {
        localStorage.setItem('alphaind_has_visited', 'true');
        localStorage.setItem('alphaind_paper_selected', 'true');
        localStorage.setItem('alphaind_active_desk_mode', 'live');
        renderConnectedDetails();
        switchAuthView('connected');
        return;
      } else {
        switchAuthView('locked');
        return;
      }
    }
  }

  // Default: show connect view
  switchAuthView('connect');
}

function switchAuthView(viewName) {
  const views = {
    connect: document.getElementById('oauthViewConnect'),
    waiting: document.getElementById('oauthViewWaiting'),
    connected: document.getElementById('oauthViewConnected'),
    locked: document.getElementById('oauthViewLocked')
  };

  Object.values(views).forEach(v => {
    if (v) v.style.display = 'none';
  });

  if (views[viewName]) {
    views[viewName].style.display = 'block';
  }
}

function renderConnectedDetails() {
  if (!window.AlphaindVault) return;
  const creds = window.AlphaindVault.getActiveCredentials() || {};
  const meta = window.AlphaindVault.getMetadata() || {};

  const uidEl = document.getElementById('connectedUserId');
  const keyEl = document.getElementById('connectedMaskedKey');
  const tsEl = document.getElementById('connectedTimestamp');

  if (uidEl) uidEl.textContent = creds.userId || meta.userId || 'Bitget Agentic User';
  if (keyEl) keyEl.textContent = meta.maskedApiKey || (creds.apiKey ? `${creds.apiKey.slice(0, 6)}...${creds.apiKey.slice(-4)}` : 'bg_live_...');
  if (tsEl) tsEl.textContent = new Date(meta.obtainedAt || creds.obtainedAt || Date.now()).toLocaleString();
}

window.toggleVaultPinInput = function() {
  const pinRadio = document.getElementById('vaultModePin');
  const pinBox = document.getElementById('vaultPinBox');
  if (pinRadio && pinBox) {
    pinBox.style.display = pinRadio.checked ? 'block' : 'none';
  }
};

window.skipToTradingDesk = function() {
  localStorage.setItem('alphaind_has_visited', 'true');
  localStorage.setItem('alphaind_paper_selected', 'true');
  localStorage.setItem('alphaind_active_desk_mode', 'paper');
  window.location.href = '/desk?mode=paper';
};

window.launchLiveTradingDesk = function() {
  try {
    localStorage.setItem('alphaind_has_visited', 'true');
    localStorage.setItem('alphaind_paper_selected', 'true');
    localStorage.setItem('alphaind_active_desk_mode', 'live');
  } catch (e) {
    console.warn('[OAuth] Storage error:', e);
  }
  window.location.href = '/desk?mode=live';
};

window.launchBitgetOAuth = async function() {
  const pinRadio = document.getElementById('vaultModePin');
  const pinInput = document.getElementById('vaultPinInput');
  let pin = '';
  if (pinRadio && pinRadio.checked) {
    pin = pinInput ? pinInput.value.trim() : '';
    if (pin.length < 4) {
      if (window.showAlertDialog) {
        await window.showAlertDialog({
          title: 'Vault PIN Required',
          message: 'Master PIN must be at least 4 characters for PBKDF2 vault encryption.',
          type: 'warning'
        });
      } else {
        alert('Master PIN must be at least 4 characters for PBKDF2 vault encryption.');
      }
      return;
    }
  }
  _pendingVaultPin = pin;

  try {
    const hostIp = window.location.hostname || '127.0.0.1';
    const res = await apiFetch('/api/oauth/start', {
      method: 'POST',
      body: JSON.stringify({ host_ip: hostIp })
    });

    if (!res.ok) {
      throw new Error(`Failed to initialize OAuth session: ${res.statusText}`);
    }

    const data = await res.json();
    _pendingOAuthSessionId = data.session_id;
    sessionStorage.setItem('bitget_oauth_active_session', data.session_id);

    const sidDisplay = document.getElementById('oauthSessionIdDisplay');
    const portDisplay = document.getElementById('oauthPortDisplay');
    const reopenLink = document.getElementById('reopenAuthLink');
    if (sidDisplay) sidDisplay.textContent = data.session_id;
    if (portDisplay) portDisplay.textContent = `${data.host_ip}:${data.port}`;
    if (reopenLink) reopenLink.href = data.authorize_url;

    switchAuthView('waiting');
    window.open(data.authorize_url, '_blank', 'width=980,height=750');
    startOAuthStatusPolling(data.session_id, pin);

  } catch (err) {
    if (window.showAlertDialog) {
      await window.showAlertDialog({
        title: 'Bitget OAuth Error',
        message: `Could not start Bitget OAuth: ${err.message}`,
        type: 'danger'
      });
    } else {
      alert(`Could not start Bitget OAuth: ${err.message}`);
    }
  }
};

function startOAuthStatusPolling(sessionId, pin) {
  if (_oauthPollInterval) clearInterval(_oauthPollInterval);

  let attempts = 0;
  const maxAttempts = 120; // 3 minutes

  _oauthPollInterval = setInterval(async () => {
    attempts++;
    if (attempts > maxAttempts) {
      clearInterval(_oauthPollInterval);
      _oauthPollInterval = null;
      if (window.showAlertDialog) {
        await window.showAlertDialog({
          title: 'Session Timed Out',
          message: 'Bitget OAuth session timed out. Please retry connection.',
          type: 'warning'
        });
      } else {
        alert('Bitget OAuth session timed out. Please retry.');
      }
      switchAuthView('connect');
      return;
    }

    try {
      const res = await apiFetch(`/api/oauth/session-status?session_id=${encodeURIComponent(sessionId)}`);
      if (!res.ok) return;
      const data = await res.json();

      if (data.status === 'completed' && data.credentials) {
        clearInterval(_oauthPollInterval);
        _oauthPollInterval = null;

        if (window.AlphaindVault) {
          await window.AlphaindVault.saveVault(data.credentials, pin);
        }

        await syncCredentialsToDesk(data.credentials);
        showAuthToast('Bitget Agentic Subaccount authorized & encrypted!', 'success');
        renderConnectedDetails();
        switchAuthView('connected');
      } else if (data.status === 'failed') {
        clearInterval(_oauthPollInterval);
        _oauthPollInterval = null;
        if (window.showAlertDialog) {
          await window.showAlertDialog({
            title: 'Authorization Failed',
            message: `OAuth authorization failed: ${data.error || 'Unknown error'}`,
            type: 'danger'
          });
        } else {
          alert(`OAuth authorization failed: ${data.error || 'Unknown error'}`);
        }
        switchAuthView('connect');
      }
    } catch (e) {
      console.warn('[OAuth] Polling error:', e);
    }
  }, 1500);
}

window.cancelOAuthSession = function() {
  if (_oauthPollInterval) {
    clearInterval(_oauthPollInterval);
    _oauthPollInterval = null;
  }
  _pendingOAuthSessionId = null;
  sessionStorage.removeItem('bitget_oauth_active_session');
  switchAuthView('connect');
};

window.unlockSavedVault = async function() {
  const pinIn = document.getElementById('unlockPinInput');
  const pin = pinIn ? pinIn.value.trim() : '';

  try {
    if (!window.AlphaindVault) throw new Error('Cryptographic vault engine not loaded');
    const creds = await window.AlphaindVault.unlockVault(pin);
    if (creds) {
      await syncCredentialsToDesk(creds);
      showAuthToast('Vault unlocked. Bitget Agentic Subaccount active.', 'success');
      renderConnectedDetails();
      switchAuthView('connected');
    }
  } catch (err) {
    if (window.showAlertDialog) {
      await window.showAlertDialog({
        title: 'Unlock Failed',
        message: `Unlock failed: ${err.message}`,
        type: 'danger'
      });
    } else {
      alert(`Unlock failed: ${err.message}`);
    }
  }
};

window.lockVault = function() {
  if (window.AlphaindVault) {
    window.AlphaindVault.lockVault();
  }
  switchAuthView('locked');
  showAuthToast('Agentic credential vault locked.', 'info');
};

window.disconnectAndWipe = async function() {
  let confirmed = false;
  if (window.showConfirmDialog) {
    confirmed = await window.showConfirmDialog({
      title: 'Disconnect & Wipe Storage?',
      badge: 'SECURITY GUARD',
      message: 'Are you sure you want to disconnect and wipe all encrypted Bitget credentials from this browser?',
      confirmText: 'Disconnect & Wipe',
      cancelText: 'Cancel',
      type: 'danger'
    });
  } else {
    confirmed = confirm('Are you sure you want to disconnect and wipe all encrypted Bitget credentials from this browser?');
  }

  if (confirmed) {
    if (window.AlphaindVault) {
      window.AlphaindVault.wipeVault();
    }
    await apiFetch('/api/oauth/disconnect', { method: 'POST' });
    switchAuthView('connect');
    showAuthToast('Bitget credentials wiped from browser storage. Reverted to paper desk.', 'info');
  }
};

window.syncVaultToDesk = async function() {
  if (window.AlphaindVault && window.AlphaindVault.isUnlocked()) {
    const creds = window.AlphaindVault.getActiveCredentials();
    const syncRes = await syncCredentialsToDesk(creds);
    if (syncRes) {
      showAuthToast('Desk credentials re-synchronized with Bitget.', 'success');
    } else {
      showAuthToast('Failed to synchronize credentials with Bitget desk.', 'error');
    }
  }
};

async function syncCredentialsToDesk(credentials) {
  if (!credentials) return null;
  try {
    localStorage.setItem('alphaind_has_visited', 'true');
    localStorage.setItem('alphaind_paper_selected', 'true');
    localStorage.setItem('alphaind_active_desk_mode', 'live');
  } catch (e) {}

  const payload = {
    api_key: credentials.apiKey || credentials.api_key || '',
    apiKey: credentials.apiKey || credentials.api_key || '',
    secret_key: credentials.secretKey || credentials.secret_key || '',
    secretKey: credentials.secretKey || credentials.secret_key || '',
    passphrase: credentials.passphrase || '',
    user_id: credentials.userId || credentials.user_id || '',
    userId: credentials.userId || credentials.user_id || '',
    account_type: credentials.accountType || credentials.account_type || 'Bitget Agentic Subaccount',
    accountType: credentials.accountType || credentials.account_type || 'Bitget Agentic Subaccount',
    is_simulation: false,
    isSimulation: false
  };

  try {
    const res = await apiFetch('/api/oauth/sync', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      console.error('[OAuth] Failed to sync credentials to desk:', errData);
      return null;
    }
    const data = await res.json();
    localStorage.setItem('alphaind_has_visited', 'true');
    localStorage.setItem('alphaind_paper_selected', 'true');
    localStorage.setItem('alphaind_active_desk_mode', 'live');
    return data;
  } catch (err) {
    console.error('[OAuth] Network error syncing credentials:', err);
    return null;
  }
}

function showAuthToast(msg, type = 'info') {
  let toast = document.getElementById('oauthToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'oauthToast';
    toast.className = 'oauth-hud-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.className = `oauth-hud-toast active ${type}`;
  setTimeout(() => {
    toast.classList.remove('active');
  }, 4000);
}
