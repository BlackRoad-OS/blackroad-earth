/**
 * BlackRoad SHA-Infinity Hashing Module
 *
 * Implements recursive/chained SHA-256 hashing for enhanced security.
 * SHA-Infinity applies SHA-256 multiple times based on a configurable depth,
 * creating a computationally expensive but highly secure hash.
 *
 * Formula: sha-infinity(data, depth) = sha256(sha256(...sha256(data)...)) [depth times]
 *
 * Use cases:
 * - Critical state verification
 * - Deployment integrity checks
 * - Secret verification without storing secrets
 * - Audit trail integrity
 *
 * @module kanban/hashing/sha-infinity
 * @author BlackRoad OS
 * @license Proprietary
 */

const sha256Module = require('./sha256');

/**
 * Default configuration for SHA-Infinity
 */
const DEFAULT_CONFIG = {
    defaultDepth: 7,           // Default number of hash iterations
    maxDepth: 256,             // Maximum allowed depth
    minDepth: 1,               // Minimum allowed depth
    parallelThreshold: 1000,   // Depth at which to use parallel processing
    cacheEnabled: true,        // Enable intermediate hash caching
    salt: 'blackroad-infinity' // Default salt for enhanced security
};

/**
 * Cache for intermediate hashes (memory optimization)
 */
const hashCache = new Map();
const MAX_CACHE_SIZE = 10000;

/**
 * Core SHA-Infinity implementation
 * Applies SHA-256 recursively for the specified depth
 *
 * @param {string} data - The data to hash
 * @param {number} depth - Number of hash iterations (default: 7)
 * @param {object} options - Additional options
 * @param {boolean} options.useSalt - Whether to include salt (default: true)
 * @param {string} options.salt - Custom salt value
 * @param {boolean} options.includeDepthInHash - Include depth in final hash (default: true)
 * @returns {string} The SHA-Infinity hash
 */
function shaInfinity(data, depth = DEFAULT_CONFIG.defaultDepth, options = {}) {
    const {
        useSalt = true,
        salt = DEFAULT_CONFIG.salt,
        includeDepthInHash = true
    } = options;

    // Validate depth
    if (depth < DEFAULT_CONFIG.minDepth) {
        throw new Error(`Depth must be at least ${DEFAULT_CONFIG.minDepth}`);
    }
    if (depth > DEFAULT_CONFIG.maxDepth) {
        throw new Error(`Depth cannot exceed ${DEFAULT_CONFIG.maxDepth}`);
    }

    // Prepare initial data
    let currentHash = useSalt
        ? sha256Module.sha256(salt + ':' + data)
        : sha256Module.sha256(data);

    // Apply recursive hashing
    for (let i = 1; i < depth; i++) {
        currentHash = sha256Module.sha256(currentHash);
    }

    // Optionally include depth in final hash for verification
    if (includeDepthInHash) {
        currentHash = sha256Module.sha256(currentHash + ':depth:' + depth);
    }

    return currentHash;
}

/**
 * Async SHA-Infinity for browser environments
 * @param {string} data - The data to hash
 * @param {number} depth - Number of hash iterations
 * @param {object} options - Additional options
 * @returns {Promise<string>} The SHA-Infinity hash
 */
async function shaInfinityAsync(data, depth = DEFAULT_CONFIG.defaultDepth, options = {}) {
    const {
        useSalt = true,
        salt = DEFAULT_CONFIG.salt,
        includeDepthInHash = true
    } = options;

    // Validate depth
    if (depth < DEFAULT_CONFIG.minDepth || depth > DEFAULT_CONFIG.maxDepth) {
        throw new Error(`Depth must be between ${DEFAULT_CONFIG.minDepth} and ${DEFAULT_CONFIG.maxDepth}`);
    }

    // Prepare initial data
    let currentHash = useSalt
        ? await sha256Module.sha256Async(salt + ':' + data)
        : await sha256Module.sha256Async(data);

    // Apply recursive hashing
    for (let i = 1; i < depth; i++) {
        currentHash = await sha256Module.sha256Async(currentHash);
    }

    // Optionally include depth in final hash
    if (includeDepthInHash) {
        currentHash = await sha256Module.sha256Async(currentHash + ':depth:' + depth);
    }

    return currentHash;
}

/**
 * Hash an object with SHA-Infinity
 * @param {object} obj - The object to hash
 * @param {number} depth - Number of hash iterations
 * @param {object} options - Additional options
 * @returns {string} The SHA-Infinity hash
 */
function hashObjectInfinity(obj, depth = DEFAULT_CONFIG.defaultDepth, options = {}) {
    const jsonData = sha256Module.stableStringify(obj);
    return shaInfinity(jsonData, depth, options);
}

/**
 * Verify a SHA-Infinity hash
 * @param {string} data - The original data
 * @param {string} expectedHash - The expected hash
 * @param {number} depth - The depth used for hashing
 * @param {object} options - Additional options
 * @returns {boolean} True if the hash matches
 */
function verifyInfinityHash(data, expectedHash, depth = DEFAULT_CONFIG.defaultDepth, options = {}) {
    const actualHash = shaInfinity(data, depth, options);
    return actualHash === expectedHash.toLowerCase();
}

/**
 * Async verify for browser environments
 */
async function verifyInfinityHashAsync(data, expectedHash, depth = DEFAULT_CONFIG.defaultDepth, options = {}) {
    const actualHash = await shaInfinityAsync(data, depth, options);
    return actualHash === expectedHash.toLowerCase();
}

/**
 * Create an infinity hash chain
 * Each entry in the chain is the SHA-Infinity of the previous entry + new data
 *
 * @param {string} previousHash - The previous hash in the chain
 * @param {string} data - The new data to add
 * @param {number} depth - Hash depth for this chain link
 * @returns {string} The new chain hash
 */
function infinityChain(previousHash, data, depth = DEFAULT_CONFIG.defaultDepth) {
    const combined = previousHash + ':' + data + ':' + Date.now();
    return shaInfinity(combined, depth);
}

/**
 * Create a proof-of-work style hash
 * Useful for rate limiting or proving computational effort
 *
 * @param {string} data - The data to hash
 * @param {number} difficulty - Number of leading zeros required
 * @param {number} depth - Base depth for each attempt
 * @returns {object} { hash, nonce, attempts }
 */
function proofOfWork(data, difficulty = 4, depth = DEFAULT_CONFIG.defaultDepth) {
    const prefix = '0'.repeat(difficulty);
    let nonce = 0;
    let hash;

    do {
        hash = shaInfinity(data + ':' + nonce, depth, { includeDepthInHash: false });
        nonce++;
    } while (!hash.startsWith(prefix) && nonce < 10000000);

    return {
        hash,
        nonce: nonce - 1,
        attempts: nonce,
        verified: hash.startsWith(prefix)
    };
}

/**
 * Create a time-based hash that includes timestamp
 * @param {string} data - The data to hash
 * @param {number} depth - Hash depth
 * @param {number} timestamp - Optional timestamp (default: now)
 * @returns {object} { hash, timestamp }
 */
function timedHash(data, depth = DEFAULT_CONFIG.defaultDepth, timestamp = Date.now()) {
    const hash = shaInfinity(data + ':timestamp:' + timestamp, depth);
    return { hash, timestamp };
}

/**
 * Generate a hash-based unique identifier with infinity hashing
 * @param {...string} components - Components to include
 * @returns {string} A 16-character hash-based ID
 */
function generateInfinityId(...components) {
    const data = components.join(':') + ':' + Date.now() + ':' + Math.random();
    return shaInfinity(data, 3, { includeDepthInHash: false }).substring(0, 16);
}

/**
 * Create a merkle root from multiple hashes using SHA-Infinity
 * @param {string[]} hashes - Array of hashes
 * @param {number} depth - Depth for each combining operation
 * @returns {string} The merkle root
 */
function infinityMerkleRoot(hashes, depth = DEFAULT_CONFIG.defaultDepth) {
    if (hashes.length === 0) {
        return shaInfinity('empty', depth);
    }
    if (hashes.length === 1) {
        return hashes[0];
    }

    const paired = [];
    for (let i = 0; i < hashes.length; i += 2) {
        const left = hashes[i];
        const right = hashes[i + 1] || left; // Duplicate last if odd
        paired.push(shaInfinity(left + right, depth, { includeDepthInHash: false }));
    }

    return infinityMerkleRoot(paired, depth);
}

/**
 * State integrity wrapper
 * Creates a complete integrity record for kanban state
 *
 * @param {object} state - The kanban state object
 * @param {number} depth - Hash depth
 * @returns {object} Integrity record with multiple hash types
 */
function createStateIntegrity(state, depth = DEFAULT_CONFIG.defaultDepth) {
    const timestamp = Date.now();
    const stateJson = sha256Module.stableStringify(state);

    return {
        sha256: sha256Module.sha256(stateJson),
        sha_infinity: shaInfinity(stateJson, depth),
        chain_depth: depth,
        timestamp,
        version: '1.0.0',
        algorithm: 'sha-infinity-v1'
    };
}

/**
 * Verify complete state integrity
 * @param {object} state - The kanban state to verify
 * @param {object} integrity - The integrity record
 * @returns {object} Verification result
 */
function verifyStateIntegrity(state, integrity) {
    const stateJson = sha256Module.stableStringify(state);

    const sha256Valid = sha256Module.sha256(stateJson) === integrity.sha256;
    const infinityValid = shaInfinity(stateJson, integrity.chain_depth) === integrity.sha_infinity;

    return {
        valid: sha256Valid && infinityValid,
        sha256_valid: sha256Valid,
        sha_infinity_valid: infinityValid,
        checked_at: Date.now(),
        original_timestamp: integrity.timestamp
    };
}

// Export configuration
const config = { ...DEFAULT_CONFIG };

// Export all functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        shaInfinity,
        shaInfinityAsync,
        hashObjectInfinity,
        verifyInfinityHash,
        verifyInfinityHashAsync,
        infinityChain,
        proofOfWork,
        timedHash,
        generateInfinityId,
        infinityMerkleRoot,
        createStateIntegrity,
        verifyStateIntegrity,
        config
    };
}

// Browser/ES module export
if (typeof window !== 'undefined') {
    window.BlackRoadSHAInfinity = {
        shaInfinity,
        shaInfinityAsync,
        hashObjectInfinity,
        verifyInfinityHash,
        verifyInfinityHashAsync,
        infinityChain,
        proofOfWork,
        timedHash,
        generateInfinityId,
        infinityMerkleRoot,
        createStateIntegrity,
        verifyStateIntegrity,
        config
    };
}
