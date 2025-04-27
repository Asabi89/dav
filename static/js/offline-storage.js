// Initialiser la base de données IndexedDB
const dbPromise = idb.openDB('opay-db', 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains('pending-transactions')) {
        const store = db.createObjectStore('pending-transactions', { keyPath: 'id', autoIncrement: true });
        store.createIndex('status', 'status');
      }
    }
  });
  
  // Fonction pour stocker une transaction en attente
  async function storeTransaction(transaction) {
    const db = await dbPromise;
    transaction.status = 'pending';
    transaction.timestamp = new Date().toISOString();
    return db.add('pending-transactions', transaction);
  }
  
  // Fonction pour récupérer les transactions en attente
  async function getPendingTransactions() {
    const db = await dbPromise;
    return db.getAllFromIndex('pending-transactions', 'status', 'pending');
  }
  
  // Fonction pour marquer une transaction comme synchronisée
  async function markTransactionSynced(id) {
    const db = await dbPromise;
    const tx = db.transaction('pending-transactions', 'readwrite');
    const store = tx.objectStore('pending-transactions');
    const item = await store.get(id);
    item.status = 'synced';
    store.put(item);
    return tx.complete;
  }
  
  // Fonction pour effectuer une transaction avec support hors ligne
  async function performTransaction(transactionData) {
    if (!navigator.onLine) {
      // Si hors ligne, stocker la transaction localement
      await storeTransaction(transactionData);
      // Planifier une synchronisation lorsque l'utilisateur sera de nouveau en ligne
      navigator.serviceWorker.ready.then(registration => {
        registration.sync.register('sync-transactions');
      });
      return { success: true, offline: true };
    } else {
      // Si en ligne, envoyer directement au serveur
      try {
        const response = await fetch('/api/transactions/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(transactionData),
        });
        return await response.json();
      } catch (error) {
        // En cas d'erreur, stocker localement
        await storeTransaction(transactionData);
        return { success: true, offline: true };
      }
    }
  }
  