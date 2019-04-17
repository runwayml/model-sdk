// Read the Docs doesn't currently support HTTPS redirects for CNAME domains
// This is a hacky work around that keeps us free of having to host our own
// server-side component.
if (location.protocol != 'https:') {
 location.href = 'https:' + window.location.href.substring(window.location.protocol.length);
}

// Hide RTD search.

window.document.onload = function(){ 
  var s = document.getElementsByClassName("injected")
  s[0].children[3].style.display = 'none';
}

