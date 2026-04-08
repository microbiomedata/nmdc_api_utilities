document.addEventListener('DOMContentLoaded', function () {
  try {
    var links = document.querySelectorAll('a[href^="http"]');
    links.forEach(function (a) {
      // skip links that point to the same origin
      try {
        if (a.hostname && a.hostname !== location.hostname) {
          a.setAttribute('target', '_blank');
          a.setAttribute('rel', 'noopener noreferrer');
        }
      } catch (e) {
        // ignore malformed URLs
      }
    });
  } catch (e) {
    // defensive: do nothing if querySelectorAll isn't supported
  }
});
