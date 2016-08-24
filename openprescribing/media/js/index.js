global.jQuery = require('jquery');
global.$ = global.jQuery;

if (!window.console) {
  var noOp = function(){};
  console = {
    log: noOp,
    warn: noOp,
    error: noOp
  };
}

var queryForm = require('./src/form');
queryForm.setUp();

$(document).ready(function() {
  $('.doorbell-show').click(function() { doorbell.show(); });
});
