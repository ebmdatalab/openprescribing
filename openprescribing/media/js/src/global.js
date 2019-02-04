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

  // We have to attach the listener to the chart container, rather than to the
  // individual links, because at this point the charts and their links may not
  // exist
  $('#charts').on('click', '.js-shareable-link', function() {
    var $link   = $(this);
    var $input = $link.siblings('input');
    $input.val($link.prop('href'));
    $input.one('blur', function() {
      $input.tooltip('destroy');
      $input.hide();
      $link.show();
    });
    $link.hide();
    $input.show();
    $input.select();
    var copied = false;
    try {
      document.execCommand('copy');
      copied = true;
    } catch(err) {}
    if (copied) {
      $input.tooltip({trigger: 'manual', title: 'Copied to clipboard'});
      $input.tooltip('show');
    }
    return false;
  });
});
