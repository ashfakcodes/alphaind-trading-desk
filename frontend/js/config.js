/**
 * Alphaind - AI Trading Desk
 * Frontend Cloud Configuration & Dynamic API Resolver
 * 
 * Seamlessly connects Vercel frontend to Render backend or local dev server.
 */

(function (window) {
  'use strict';

  // Determine base API URL with fallback precedence
  function resolveApiBaseUrl() {
    // 1. Runtime environment injected via window.API_BASE_URL or window.__ENV__
    if (window.API_BASE_URL && window.API_BASE_URL.trim().length > 0) {
      return window.API_BASE_URL.trim().replace(/\/+$/, '');
    }
    if (window.__ENV__ && window.__ENV__.API_BASE_URL) {
      return window.__ENV__.API_BASE_URL.trim().replace(/\/+$/, '');
    }

    // 2. URL Query Parameter override (?api=https://...)
    try {
      const params = new URLSearchParams(window.location.search);
      const apiParam = params.get('api') || params.get('backend');
      if (apiParam) {
        return apiParam.trim().replace(/\/+$/, '');
      }
    } catch (e) {
      // ignore
    }

    // 3. Local dev server auto-detection (e.g. running on port 3000 or 5173 locally)
    const hostname = window.location.hostname;
    const port = window.location.port;
    const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
    
    if (isLocalhost && port && port !== '8000') {
      return `http://${hostname}:8000`;
    }
    if (isLocalhost && (!port || port === '8000')) {
      return '';
    }

    // 4. Cloud Production Backend (Render)
    return 'https://alphaind-trading-desk.onrender.com';
  }

  // Global Config Object
  const AppConfig = {
    getBaseUrl: function () {
      return resolveApiBaseUrl();
    },

    // Endpoint URL builder
    apiUrl: function (path) {
      const base = this.getBaseUrl();
      const cleanPath = path.startsWith('/') ? path : '/' + path;
      if (!base) return cleanPath;
      return `${base}${cleanPath}`;
    },

    // Robust fetch wrapper that applies dynamic API base URL
    fetch: async function (path, options = {}) {
      const url = this.apiUrl(path);
      const defaultHeaders = {
        'Accept': 'application/json'
      };

      if (options.body && typeof options.body === 'string' && !options.headers?.['Content-Type']) {
        defaultHeaders['Content-Type'] = 'application/json';
      }

      const mergedOptions = {
        ...options,
        headers: {
          ...defaultHeaders,
          ...(options.headers || {})
        }
      };

      return fetch(url, mergedOptions);
    }
  };

  // Expose to window
  window.AppConfig = AppConfig;
  window.getApiUrl = function (path) {
    return AppConfig.apiUrl(path);
  };
  window.apiFetch = function (path, options) {
    return AppConfig.fetch(path, options);
  };

})(window);
