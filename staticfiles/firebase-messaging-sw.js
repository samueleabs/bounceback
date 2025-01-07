importScripts("/static/js/firebase-app-compact.js");
importScripts("/static/js/firebase-messaging-compact.js");

self.addEventListener("install", (event) => {
	event.waitUntil(
		fetch("/firebase-config/")
			.then((response) => response.json())
			.then((config) => {
				firebase.initializeApp(config);

				// Retrieve an instance of Firebase Messaging so that it can handle background messages.
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

					self.registration.showNotification(
						notificationTitle,
						notificationOptions
					);
				});
			})
			.catch((err) => {
				console.error("Failed to fetch Firebase config:", err);
			})
	);
});
