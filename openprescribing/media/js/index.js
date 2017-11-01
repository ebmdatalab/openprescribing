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
var homeForm = require('./src/home');

$(document).ready(function() {
  homeForm.setUp();
  queryForm.setUp();
  $('.doorbell-show').click(function(e) {
    if (typeof doorbell !== 'undefined') {
      e.preventDefault();
      doorbell.show();
    }
  });
});
