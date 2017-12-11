global.jQuery = require('jquery');
global.$ = global.jQuery;
require('bootstrap');

if (!window.console) {
  var noOp = function(){};
  console = {
    log: noOp,
    warn: noOp,
    error: noOp
  };
}

$(document).ready(function() {
  $('.doorbell-show').click(function(e) {
    if (typeof doorbell !== 'undefined') {
      e.preventDefault();
      doorbell.show();
    }
  });
});
