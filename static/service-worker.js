const CACHE_NAME = "bounceback-cache-v1";
const urlsToCache = [
	"/",
	"/static/css/styles.css", // Add your CSS files
	"/static/js/scripts.js", // Add your JS files
	"/static/icons/icon-192x192.png",
	"/static/icons/icon-512x512.png",
];

// Install the service worker and cache resources
self.addEventListener("install", (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) => {
			return cache.addAll(urlsToCache);
		})
	);
});

// Serve cached resources when offline
self.addEventListener("fetch", (event) => {
	event.respondWith(
		caches.match(event.request).then((response) => {
			return response || fetch(event.request);
		})
	);
});

// Update the service worker and remove old caches
self.addEventListener("activate", (event) => {
	event.waitUntil(
		caches.keys().then((cacheNames) => {
			return Promise.all(
				cacheNames.map((cacheName) => {
					if (cacheName !== CACHE_NAME) {
						return caches.delete(cacheName);
					}
				})
			);
		})
	);
});
