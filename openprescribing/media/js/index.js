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
