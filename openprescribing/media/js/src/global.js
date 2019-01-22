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

  $('.js-hide-long-list').each(function() {
    var $container = $(this);
    var maxItems = $container.data('max-items') || 10;
    var $elementsToHide = $container.children().slice(maxItems);
    if ( ! $elementsToHide.length) return;
    var $button = $(
      '<button type="button" class="btn btn-default btn-xs">'+
      '  Show all &hellip;'+
      '</button>'
    );
    $button.on('click', function() {
      $button.remove();
      $elementsToHide.css('display', '');
    });
    $elementsToHide.css('display', 'none');
    $button.appendTo($container);
  });
});
