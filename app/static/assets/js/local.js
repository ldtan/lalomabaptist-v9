var url = new URL(window.location.href);
var tz = Intl.DateTimeFormat().resolvedOptions().timeZone;

url.searchParams.set('tz', tz);
window.location.replace(url);