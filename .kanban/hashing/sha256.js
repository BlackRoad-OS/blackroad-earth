/**
 * BlackRoad SHA-256 Hashing Module
 *
 * Provides SHA-256 hashing for state integrity verification.
 * Used across all kanban state operations to ensure data consistency.
 *
 * @module kanban/hashing/sha256
 * @author BlackRoad OS
 * @license Proprietary
 */

// For Node.js environments
const crypto = typeof require !== 'undefined' ? require('crypto') : null;

/**
 * Calculate SHA-256 hash of a string
 * @param {string} data - The data to hash
 * @returns {string} The hex-encoded SHA-256 hash
 */
function sha256(data) {
    if (crypto) {
        // Node.js environment
        return crypto.createHash('sha256').update(data, 'utf8').digest('hex');
    } else if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
        // Browser environment - returns a Promise
        throw new Error('Use sha256Async for browser environments');
    }
    throw new Error('No crypto implementation available');
}

/**
 * Async SHA-256 for browser environments
 * @param {string} data - The data to hash
 * @returns {Promise<string>} The hex-encoded SHA-256 hash
 */
async function sha256Async(data) {
    if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
        const encoder = new TextEncoder();
        const dataBuffer = encoder.encode(data);
        const hashBuffer = await window.crypto.subtle.digest('SHA-256', dataBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    // Fallback to sync version for Node.js
    return sha256(data);
}

/**
 * Hash an object by JSON stringifying it first
 * @param {object} obj - The object to hash
 * @param {boolean} sortKeys - Whether to sort object keys for consistent hashing
 * @returns {string} The hex-encoded SHA-256 hash
 */
function hashObject(obj, sortKeys = true) {
    const data = sortKeys ? stableStringify(obj) : JSON.stringify(obj);
    return sha256(data);
}

/**
 * Async version of hashObject for browser environments
 * @param {object} obj - The object to hash
 * @param {boolean} sortKeys - Whether to sort object keys for consistent hashing
 * @returns {Promise<string>} The hex-encoded SHA-256 hash
 */
async function hashObjectAsync(obj, sortKeys = true) {
    const data = sortKeys ? stableStringify(obj) : JSON.stringify(obj);
    return sha256Async(data);
}

/**
 * Stable JSON stringify that sorts object keys
 * Ensures consistent hashing regardless of key order
 * @param {*} obj - The value to stringify
 * @returns {string} JSON string with sorted keys
 */
function stableStringify(obj) {
    if (obj === null || typeof obj !== 'object') {
        return JSON.stringify(obj);
    }

    if (Array.isArray(obj)) {
        return '[' + obj.map(stableStringify).join(',') + ']';
    }

    const keys = Object.keys(obj).sort();
    const pairs = keys.map(key => {
        const value = stableStringify(obj[key]);
        return JSON.stringify(key) + ':' + value;
    });

    return '{' + pairs.join(',') + '}';
}

/**
 * Verify a hash matches the expected value
 * @param {string} data - The data to verify
 * @param {string} expectedHash - The expected hash value
 * @returns {boolean} True if the hash matches
 */
function verifyHash(data, expectedHash) {
    const actualHash = sha256(data);
    return actualHash === expectedHash.toLowerCase();
}

/**
 * Async verify for browser environments
 * @param {string} data - The data to verify
 * @param {string} expectedHash - The expected hash value
 * @returns {Promise<boolean>} True if the hash matches
 */
async function verifyHashAsync(data, expectedHash) {
    const actualHash = await sha256Async(data);
    return actualHash === expectedHash.toLowerCase();
}

/**
 * Create a hash chain (useful for audit trails)
 * @param {string} previousHash - The previous hash in the chain
 * @param {string} data - The new data to add to the chain
 * @returns {string} The new chain hash
 */
function chainHash(previousHash, data) {
    return sha256(previousHash + data);
}

/**
 * Hash a file's contents (Node.js only)
 * @param {string} filePath - Path to the file
 * @returns {Promise<string>} The file's SHA-256 hash
 */
async function hashFile(filePath) {
    if (!crypto) {
        throw new Error('hashFile requires Node.js environment');
    }

    const fs = require('fs').promises;
    const content = await fs.readFile(filePath, 'utf8');
    return sha256(content);
}

/**
 * Generate a hash-based ID
 * @param {...string} components - Components to include in the ID
 * @returns {string} A shortened hash-based ID (12 characters)
 */
function generateHashId(...components) {
    const data = components.join(':') + ':' + Date.now();
    return sha256(data).substring(0, 12);
}

/**
 * Create a content-addressable key
 * @param {*} content - The content to create a key for
 * @returns {string} A content-addressable hash key
 */
function contentKey(content) {
    return 'sha256:' + hashObject(content);
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        sha256,
        sha256Async,
        hashObject,
        hashObjectAsync,
        stableStringify,
        verifyHash,
        verifyHashAsync,
        chainHash,
        hashFile,
        generateHashId,
        contentKey
    };
}

// Browser/ES module export
if (typeof window !== 'undefined') {
    window.BlackRoadSHA256 = {
        sha256,
        sha256Async,
        hashObject,
        hashObjectAsync,
        stableStringify,
        verifyHash,
        verifyHashAsync,
        chainHash,
        generateHashId,
        contentKey
    };
}
