// Import the Firebase scripts
importScripts("{% static 'js/firebase-app-compat.js' %}");
importScripts("{% static 'js/firebase-messaging-compat.js' %}");

// Initialize the Firebase app in the service worker by passing in the full configuration object
firebase.initializeApp({
	apiKey: "{{ firebase_config.apiKey }}",
	authDomain: "{{ firebase_config.authDomain }}",
	projectId: "{{ firebase_config.projectId }}",
	storageBucket: "{{ firebase_config.storageBucket }}",
	messagingSenderId: "{{ firebase_config.messagingSenderId }}",
	appId: "{{ firebase_config.appId }}",
	measurementId: "{{ firebase_config.measurementId }}",
});

// Retrieve an instance of Firebase Messaging so that it can handle background messages
const messaging = firebase.messaging();

messaging.onBackgroundMessage(function (payload) {
	console.log(
		"[firebase-messaging-sw.js] Received background message ",
		payload
	);
	// Customize notification here
	const notificationTitle = payload.notification.title;
	const notificationOptions = {
		body: payload.notification.body,
		icon: payload.notification.icon,
	};

	self.registration.showNotification(notificationTitle, notificationOptions);
});
