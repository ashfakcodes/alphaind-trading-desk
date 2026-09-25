/**
 * Alphaind · Bitget Agentic Account Encrypted Security Vault
 * 
 * Hardware-grade client-side encryption using the Web Cryptography API (window.crypto.subtle).
 * Encrypts API Key, Secret Key, Passphrase, and Agent UID via AES-GCM (256-bit) before writing
 * to browser storage (localStorage). Plaintext credentials never touch browser disk storage.
 */

(function (window) {
  'use strict';

  const STORAGE_KEY = 'alphaind_agentic_vault';
  const DEVICE_KEY_STORAGE = 'alphaind_device_kdf_seed';
  const PBKDF2_ITERATIONS = 100000;
  const KEY_LENGTH_BITS = 256;
  const IV_LENGTH_BYTES = 12; // 96-bit IV recommended for AES-GCM
  const SALT_LENGTH_BYTES = 16;

  // In-memory decrypted credentials cache (ephemeral, wiped on lock/disconnect)
  let _unlockedCredentials = null;

  // -------------------------------------------------------------
  // Binary / Base64 Helpers
  // -------------------------------------------------------------

  function bufferToBase64(buf) {
    const bytes = new Uint8Array(buf);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  function base64ToBuffer(b64) {
    const binary = window.atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  function getRandomBytes(len) {
    const bytes = new Uint8Array(len);
    window.crypto.getRandomValues(bytes);
    return bytes;
  }

  // -------------------------------------------------------------
  // Key Derivation Functions
  // -------------------------------------------------------------

  /**
   * Derive AES-GCM-256 CryptoKey from a user PIN or passphrase via PBKDF2 (SHA-256).
   */
  async function deriveKeyFromPin(pin, saltBytes) {
    const encoder = new TextEncoder();
    const pinData = encoder.encode(pin);

    const baseKey = await window.crypto.subtle.importKey(
      'raw',
      pinData,
      { name: 'PBKDF2' },
      false,
      ['deriveKey']
    );

    return window.crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: saltBytes,
        iterations: PBKDF2_ITERATIONS,
        hash: 'SHA-256'
      },
      baseKey,
      { name: 'AES-GCM', length: KEY_LENGTH_BITS },
      false,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * Retrieve or generate a device-bound entropy seed for seamless zero-PIN mode.
   * Ensures the raw API keys are never stored unencrypted in localStorage.
   */
  function getOrCreateDeviceSeed() {
    let seed = localStorage.getItem(DEVICE_KEY_STORAGE);
    if (!seed) {
      const randomSeed = getRandomBytes(32);
      seed = bufferToBase64(randomSeed.buffer);
      localStorage.setItem(DEVICE_KEY_STORAGE, seed);
    }
    return seed;
  }

  /**
   * Derive AES-GCM-256 CryptoKey using device entropy.
   */
  async function deriveDeviceKey(saltBytes) {
    const seed = getOrCreateDeviceSeed();
    return deriveKeyFromPin(seed, saltBytes);
  }

  // -------------------------------------------------------------
  // Cryptographic Vault Core API
  // -------------------------------------------------------------

  const AlphaindVault = {
    /**
     * Encrypt credentials using AES-GCM-256 and store in browser storage.
     * @param {Object} credentials - { apiKey, secretKey, passphrase, userId, accountType }
     * @param {string} [pin] - Optional user PIN for PBKDF2. If omitted, uses device-bound vault.
     */
    async saveVault(credentials, pin = '') {
      if (!window.crypto || !window.crypto.subtle) {
        throw new Error('Web Cryptography API is not available in this browser environment.');
      }

      const salt = getRandomBytes(SALT_LENGTH_BYTES);
      const iv = getRandomBytes(IV_LENGTH_BYTES);

      const isPinMode = Boolean(pin && pin.trim().length > 0);
      const cryptoKey = isPinMode
        ? await deriveKeyFromPin(pin.trim(), salt)
        : await deriveDeviceKey(salt);

      const encoder = new TextEncoder();
      const plaintextBytes = encoder.encode(JSON.stringify(credentials));

      const ciphertextBuf = await window.crypto.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: iv,
          tagLength: 128
        },
        cryptoKey,
        plaintextBytes
      );

      // Safe non-sensitive metadata for UI display
      const apiKey = credentials.apiKey || '';
      const maskedKey = apiKey.length > 10
        ? `${apiKey.slice(0, 6)}...${apiKey.slice(-4)}`
        : '******';

      const vaultPayload = {
        version: 1,
        algorithm: 'AES-GCM-256',
        mode: isPinMode ? 'pin_protected' : 'device_protected',
        salt: bufferToBase64(salt.buffer),
        iv: bufferToBase64(iv.buffer),
        ciphertext: bufferToBase64(ciphertextBuf),
        tagLength: 128,
        metadata: {
          userId: credentials.userId || 'Bitget Agentic User',
          maskedApiKey: maskedKey,
          accountType: credentials.accountType || 'Bitget Agentic Subaccount',
          obtainedAt: credentials.obtainedAt || Date.now(),
          encryptedAt: Date.now()
        }
      };

      // Persist strictly ciphertext to browser storage
      localStorage.setItem(STORAGE_KEY, JSON.stringify(vaultPayload));

      // Keep active in ephemeral memory for the live session
      _unlockedCredentials = { ...credentials };

      return vaultPayload.metadata;
    },

    /**
     * Unlock and decrypt the vault from browser storage into memory.
     * @param {string} [pin] - User PIN if the vault was saved with pin_protected mode.
     */
    async unlockVault(pin = '') {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        throw new Error('No encrypted vault found in browser storage.');
      }

      const vault = JSON.parse(raw);
      const salt = new Uint8Array(base64ToBuffer(vault.salt));
      const iv = new Uint8Array(base64ToBuffer(vault.iv));
      const ciphertextBuf = base64ToBuffer(vault.ciphertext);

      let cryptoKey;
      if (vault.mode === 'pin_protected') {
        if (!pin) {
          throw new Error('This vault is protected by a trader PIN. Please enter your PIN.');
        }
        cryptoKey = await deriveKeyFromPin(pin.trim(), salt);
      } else {
        cryptoKey = await deriveDeviceKey(salt);
      }

      try {
        const decryptedBuf = await window.crypto.subtle.decrypt(
          {
            name: 'AES-GCM',
            iv: iv,
            tagLength: vault.tagLength || 128
          },
          cryptoKey,
          ciphertextBuf
        );

        const decoder = new TextDecoder();
        const jsonStr = decoder.decode(decryptedBuf);
        const credentials = JSON.parse(jsonStr);

        _unlockedCredentials = credentials;
        return credentials;
      } catch (err) {
        throw new Error('Decryption failed. Incorrect PIN or corrupted ciphertext.');
      }
    },

    /**
     * Returns true if an encrypted vault exists in localStorage.
     */
    hasVault() {
      return Boolean(localStorage.getItem(STORAGE_KEY));
    },

    /**
     * Returns true if valid credentials are currently decrypted and cached in memory.
     */
    isUnlocked() {
      return Boolean(_unlockedCredentials && _unlockedCredentials.apiKey);
    },

    /**
     * Get currently cached in-memory credentials without reading disk.
     */
    getActiveCredentials() {
      return _unlockedCredentials ? { ..._unlockedCredentials } : null;
    },

    /**
     * Read non-sensitive metadata from browser storage without decrypting secret keys.
     */
    getMetadata() {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      try {
        const vault = JSON.parse(raw);
        return {
          ...vault.metadata,
          mode: vault.mode,
          algorithm: vault.algorithm
        };
      } catch (e) {
        return null;
      }
    },

    /**
     * Clear in-memory credentials cache (locks vault).
     */
    lockVault() {
      _unlockedCredentials = null;
    },

    /**
     * Wipe all encrypted credentials from browser storage and memory.
     */
    wipeVault() {
      _unlockedCredentials = null;
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(DEVICE_KEY_STORAGE);
    }
  };

  // Expose to window
  window.AlphaindVault = AlphaindVault;

})(window);
