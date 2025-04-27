// Nom du cache
const CACHE_NAME = 'opay-cache-v1';

// Fichiers à mettre en cache
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/images/logo.png',
  '/static/offline.html',
  // Ajoutez d'autres ressources importantes
];

// Installation du service worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache ouvert');
        return cache.addAll(urlsToCache);
      })
  );
});

// Modifier l'écouteur fetch pour gérer le mode hors ligne
self.addEventListener('fetch', event => {
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          if (response) {
            return response;
          }
          
          return fetch(event.request)
            .then(response => {
              if(!response || response.status !== 200 || response.type !== 'basic') {
                return response;
              }
  
              const responseToCache = response.clone();
              caches.open(CACHE_NAME)
                .then(cache => {
                  cache.put(event.request, responseToCache);
                });
  
              return response;
            })
            .catch(error => {
              // Si la requête échoue (hors ligne), renvoyer la page hors ligne
              if (event.request.mode === 'navigate') {
                return caches.match('/static/offline.html');
              }
            });
        })
    );
  });

// Mise à jour du service worker
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});


// Ajouter ceci à votre service-worker.js
self.addEventListener('sync', function(event) {
    if (event.tag === 'sync-transactions') {
      event.waitUntil(syncTransactions());
    }
  });
  
  // Fonction pour synchroniser les transactions
  async function syncTransactions() {
    try {
      // Récupérer les transactions en attente depuis IndexedDB
      const pendingTransactions = await getPendingTransactions();
      
      // Envoyer chaque transaction au serveur
      for (const transaction of pendingTransactions) {
        await fetch('/api/transactions/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(transaction),
        });
        
        // Marquer la transaction comme synchronisée
        await markTransactionSynced(transaction.id);
      }
      
      return true;
    } catch (error) {
      console.error('Erreur lors de la synchronisation:', error);
      return false;
    }
  }
  

  // Ajouter ceci à votre service-worker.js
self.addEventListener('push', function(event) {
    const data = event.data.json();
    
    const options = {
      body: data.body,
      icon: '/static/images/icons/icon-192x192.png',
      badge: '/static/images/icons/badge-72x72.png',
      vibrate: [100, 50, 100],
      data: {
        url: data.url
      }
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  });
  
  // Gérer le clic sur la notification
  self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    event.waitUntil(
      clients.openWindow(event.notification.data.url)
    );
  });
  