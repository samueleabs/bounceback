// Import the OneSignal SDK
importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js");

// Add custom code to handle push notifications
self.addEventListener("push", function (event) {
	const data = event.data.json();
	const options = {
		body: data.body,
		icon: "/static/img/notification-icon.png", // Update with your icon path
		badge: "/static/img/notification-badge.png", // Update with your badge path
		data: {
			url: data.url, // URL to open when notification is clicked
		},
	};
	event.waitUntil(self.registration.showNotification(data.title, options));
});

// Handle notification click event
self.addEventListener("notificationclick", function (event) {
	event.notification.close();
	event.waitUntil(clients.openWindow(event.notification.data.url));
});
