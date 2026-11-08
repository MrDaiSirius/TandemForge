self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));
self.addEventListener("fetch", (event) => {
  if (event.request.mode !== "navigate") return;
  event.respondWith(fetch(event.request).catch(() => new Response(
    "TandemForge · Start your Windows PC and reconnect. / เปิดคอม Windows และเชื่อมต่ออีกครั้ง",
    { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } },
  )));
});
