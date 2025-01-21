importScripts(
	"https://www.gstatic.com/firebasejs/11.2.0/firebase-app-compat.js"
);
importScripts(
	"https://www.gstatic.com/firebasejs/11.2.0/firebase-messaging-compat.js"
);

// Initialize Firebase
const firebaseConfig = {
	apiKey: "{{ firebase_config.apiKey }}",
	authDomain: "{{ firebase_config.authDomain }}",
	projectId: "{{ firebase_config.projectId }}",
	storageBucket: "{{ firebase_config.storageBucket }}",
	messagingSenderId: "{{ firebase_config.messagingSenderId }}",
	appId: "{{ firebase_config.appId }}",
	measurementId: "{{ firebase_config.measurementId }}",
};
firebase.initializeApp(firebaseConfig);

// Initialize Firebase Cloud Messaging
const messaging = firebase.messaging();

messaging.onBackgroundMessage(function (payload) {
	console.log("Received background message ", payload);
	// Customize notification here
	const notificationTitle = payload.notification.title;
	const notificationOptions = {
		body: payload.notification.body,
		icon: "/static/img/notification-icon.png",
	};

	self.registration.showNotification(notificationTitle, notificationOptions);
});
