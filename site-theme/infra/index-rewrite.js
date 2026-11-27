// CloudFront viewer-request function (cloudfront-js-2.0).
//
// An S3 REST origin (the only kind that works with an origin access control) has no directory
// index: it looks for an object literally named `places/<slug>/`, which does not exist. So the
// extensionless, trailing-slash URLs the site generates are rewritten to the file on disk.
//
//   /                      -> /index.html
//   /places/<slug>/      -> /places/<slug>/index.html
//   /places/<slug>       -> /places/<slug>/index.html
//   /img/hero.jpg          -> untouched (it has an extension)
function handler(event) {
  var request = event.request;
  var uri = request.uri;
  var last = uri.split('/').pop();

  if (uri.endsWith('/')) {
    request.uri = uri + 'index.html';
  } else if (last.indexOf('.') === -1) {
    request.uri = uri + '/index.html';
  }
  return request;
}
