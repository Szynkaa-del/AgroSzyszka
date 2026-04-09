importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// KONFIGURACJA FIREBASE – wszystkie Twoje klucze
firebase.initializeApp({
  apiKey: "AIzaSyD-YourAPIKeyExample",  // Twój API Key z Firebase Web App
  authDomain: "agroszyszka.firebaseapp.com",  // Twój Auth Domain
  projectId: "308210805779",  // Twój Project ID
  messagingSenderId: "308210805779",  // Twój Messaging Sender ID
  appId: "1:308210805779:web:exampleappid123"  // Twój App ID
});

const messaging = firebase.messaging();

// Odbieranie powiadomień, gdy aplikacja jest w tle
messaging.onBackgroundMessage(function(payload) {
  self.registration.showNotification(payload.notification.title, {
    body: payload.notification.body
  });
});