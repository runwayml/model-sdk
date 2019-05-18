// Read the Docs doesn't currently support HTTPS redirects for CNAME domains
// This is a hacky work around that keeps us free of having to host our own
// server-side component.
if (location.protocol == 'http:') {
 location.href = 'https:' + window.location.href.substring(window.location.protocol.length);
}

// Hide RTD search.
window.addEventListener('load', function() {
  var s = document.getElementsByClassName('injected')
  s[0].children[4].style.display = 'none';
})