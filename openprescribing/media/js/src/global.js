var $ = require('jquery');
var domready = require('domready');
var bootstrap = require('bootstrap');

if (!window.console) {
  var noOp = function(){};
  console = {
    log: noOp,
    warn: noOp,
    error: noOp
  };
}
domready(function() {
  $('.doorbell-show').click(function(e) {
    if (typeof doorbell !== 'undefined') {
      e.preventDefault();
      doorbell.show();
    }
  });
});
