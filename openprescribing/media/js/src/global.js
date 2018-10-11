var Sentry = require('@sentry/browser');
if (window.SENTRY_PUBLIC_DSN && SENTRY_PUBLIC_DSN !== '') {
  Sentry.init({dsn: SENTRY_PUBLIC_DSN});
}

var $ = require('jquery');
var domready = require('domready');
var bootstrap = require('bootstrap');
var bigtext = require('bigtext');

if (!window.console) {
  var noOp = function() {};
  console = {
    log: noOp,
    warn: noOp,
    error: noOp,
  };
}
domready(function() {
  $('.feedback-show').click(function(e) {
    e.preventDefault();
    window.location.href='/feedback/?from_url=' + encodeURIComponent(window.location.href);
  });
  $('.js-submit-on-change').on('change', function() {
    this.form.submit();
  });
  $('.bigtext').bigtext({resize: true});
});
