/**
 * Service Worker for Mac Status PWA
 * Enhanced with offline functionality and better caching strategies
 */

const CACHE_NAME = 'mac-status-pwa-v2';
const RUNTIME_CACHE = 'mac-status-runtime-v2';
const OFFLINE_CACHE = 'mac-status-offline-v2';

// Static resources to cache immediately
const STATIC_CACHE_URLS = [
  '/',
  '/static/styles.css',
  '/static/app.js',
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// Runtime cache patterns
const RUNTIME_CACHE_PATTERNS = [
  /^https:\/\/fonts\.googleapis\.com/,
  /^https:\/\/fonts\.gstatic\.com/,
  /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
  /\.(?:js|css)$/
];

// Offline fallback content
const OFFLINE_FALLBACK_PAGE = `
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mac Status PWA - オフライン</title>
    <style>
        :root {
            --apple-blue: #007AFF;
            --apple-gray: #8E8E93;
            --apple-light-gray: #F2F2F7;
            --apple-background: #FFFFFF;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: var(--apple-background);
            color: #1C1C1E;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        
        .offline-container {
            text-align: center;
            padding: 2rem;
            max-width: 400px;
        }
        
        .offline-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        
        .offline-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--apple-gray);
        }
        
        .offline-message {
            font-size: 1rem;
            line-height: 1.5;
            color: var(--apple-gray);
            margin-bottom: 2rem;
        }
        
        .retry-button {
            background: var(--apple-blue);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        
        .retry-button:hover {
            opacity: 0.8;
        }
        
        .offline-features {
            margin-top: 2rem;
            padding: 1rem;
            background: var(--apple-light-gray);
            border-radius: 12px;
            text-align: left;
        }
        
        .offline-features h3 {
            margin: 0 0 1rem 0;
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .offline-features ul {
            margin: 0;
            padding-left: 1.2rem;
        }
        
        .offline-features li {
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            color: var(--apple-gray);
        }
    </style>
</head>
<body>
    <div class="offline-container">
        <div class="offline-icon">📱</div>
        <h1 class="offline-title">オフラインモード</h1>
        <p class="offline-message">
            現在インターネットに接続されていません。<br>
            接続が復旧すると、自動的に同期されます。
        </p>
        <button class="retry-button" onclick="window.location.reload()">
            再接続を試す
        </button>
        
        <div class="offline-features">
            <h3>オフライン機能</h3>
            <ul>
                <li>キャッシュされたページの表示</li>
                <li>過去のチャット履歴の閲覧</li>
                <li>基本的なUI操作</li>
                <li>自動再接続機能</li>
            </ul>
        </div>
    </div>
    
    <script>
        // Auto-retry connection every 30 seconds
        setInterval(() => {
            if (navigator.onLine) {
                window.location.reload();
            }
        }, 30000);
        
        // Listen for online event
        window.addEventListener('online', () => {
            window.location.reload();
        });
    </script>
</body>
</html>
`;

// Install event - cache static resources
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache static resources
      caches.open(CACHE_NAME).then((cache) => {
        console.log('Caching static resources');
        return cache.addAll(STATIC_CACHE_URLS);
      }),
      
      // Cache offline fallback
      caches.open(OFFLINE_CACHE).then((cache) => {
        console.log('Caching offline fallback');
        return cache.put('/offline', new Response(OFFLINE_FALLBACK_PAGE, {
          headers: { 'Content-Type': 'text/html' }
        }));
      })
    ]).then(() => {
      console.log('Service Worker installed successfully');
      // Force activation of new service worker
      return self.skipWaiting();
    })
  );
});

// Activate event - clean up old caches and claim clients
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && 
                cacheName !== RUNTIME_CACHE && 
                cacheName !== OFFLINE_CACHE) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // Claim all clients
      self.clients.claim()
    ]).then(() => {
      console.log('Service Worker activated successfully');
    })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip WebSocket requests
  if (url.protocol === 'ws:' || url.protocol === 'wss:') {
    return;
  }
  
  // Handle different types of requests
  if (url.pathname === '/') {
    // Main page - Network first, fallback to cache
    event.respondWith(networkFirstStrategy(request));
  } else if (url.pathname.startsWith('/static/')) {
    // Static assets - Cache first
    event.respondWith(cacheFirstStrategy(request));
  } else if (url.pathname.startsWith('/ws')) {
    // WebSocket - Don't cache
    return;
  } else if (shouldCacheRuntime(request)) {
    // Runtime cacheable resources - Stale while revalidate
    event.respondWith(staleWhileRevalidateStrategy(request));
  } else {
    // Other requests - Network first with offline fallback
    event.respondWith(networkFirstWithOfflineFallback(request));
  }
});

// Network first strategy (for main page)
async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Update cache with fresh content
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Network failed, trying cache:', error);
    
    // Try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page
    return caches.match('/offline');
  }
}

// Cache first strategy (for static assets)
async function cacheFirstStrategy(request) {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Failed to fetch static asset:', error);
    throw error;
  }
}

// Stale while revalidate strategy (for runtime resources)
async function staleWhileRevalidateStrategy(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  const cachedResponse = await cache.match(request);
  
  // Fetch fresh version in background
  const fetchPromise = fetch(request).then((networkResponse) => {
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  }).catch((error) => {
    console.log('Background fetch failed:', error);
  });
  
  // Return cached version immediately if available
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // Otherwise wait for network
  return fetchPromise;
}

// Network first with offline fallback
async function networkFirstWithOfflineFallback(request) {
  try {
    return await fetch(request);
  } catch (error) {
    console.log('Network request failed, checking cache:', error);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline');
    }
    
    throw error;
  }
}

// Check if request should be cached at runtime
function shouldCacheRuntime(request) {
  return RUNTIME_CACHE_PATTERNS.some(pattern => {
    if (pattern instanceof RegExp) {
      return pattern.test(request.url);
    }
    return request.url.includes(pattern);
  });
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('Background sync triggered:', event.tag);
  
  if (event.tag === 'background-sync-messages') {
    event.waitUntil(syncOfflineMessages());
  }
});

// Sync offline messages when connection is restored
async function syncOfflineMessages() {
  try {
    // Get offline messages from IndexedDB or localStorage
    // This would integrate with the main app's offline message queue
    console.log('Syncing offline messages...');
    
    // Notify all clients that sync is complete
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'SYNC_COMPLETE',
        data: { success: true }
      });
    });
  } catch (error) {
    console.error('Failed to sync offline messages:', error);
  }
}

// Push notification handling (for future use)
self.addEventListener('push', (event) => {
  console.log('Push notification received:', event);
  
  const options = {
    body: event.data ? event.data.text() : 'Mac Status PWA notification',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: '開く',
        icon: '/static/icons/icon-192x192.png'
      },
      {
        action: 'close',
        title: '閉じる',
        icon: '/static/icons/icon-192x192.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('Mac Status PWA', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Message handling from main thread
self.addEventListener('message', (event) => {
  console.log('Service Worker received message:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});