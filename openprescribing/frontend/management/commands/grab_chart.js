var system = require('system');
var page = new WebPage();
page.onConsoleMessage = function(msg) {
  system.stderr.writeLine('console: ' + msg);
};
page.viewportSize = {
  width: 1024,
  height: 1024
};
var address;

function waitFor($config) {
  $config._start = $config._start || new Date();

  if ($config.timeout && new Date() - $config._start > $config.timeout) {
    if ($config.error) {
      $config.error();
    }
    if ($config.debug) {
      console.log('timedout ' + (new Date() - $config._start) + 'ms');
    }
    return;
  }

  if ($config.check()) {
    if ($config.debug) {
      console.log('success ' + (new Date() - $config._start) + 'ms');
    }
    return $config.success();
  }

  setTimeout(waitFor, $config.interval || 0, $config);
}

var capture = function(targetFile, clipRect) {
  var previousClipRect;
  previousClipRect = page.clipRect;
  page.clipRect = clipRect;
  try {
    page.render(targetFile);
  } catch (e) {
    console.log(
      'Failed to capture screenshot as ' + targetFile + ': ' + e, "error");
  }
  if (previousClipRect) {
    page.clipRect = previousClipRect;
  }
  return this;
};

var captureSelector = function(targetFile, selector) {
  return capture(targetFile, page.evaluate(function(selector) {
    try {
      var clipRect = document.querySelector(selector).getBoundingClientRect();
      return {
        top: clipRect.top,
        left: clipRect.left,
        width: clipRect.width,
        height: clipRect.height
      };
    } catch (e) {
      console.log("Unable to fetch bounds for element " + selector, "warning");
    }
  }, selector));
};

if (system.args.length !== 3) {
  console.log('Usage: phantomjs grab_chart.js <url> <img_id>');
  phantom.exit();
} else {
  address = system.args[1];
  var imgId = system.args[2];
  page.open(address, function(status) {
    if (!status === 'success') {
      console.log('Unable to load the address!');
    } else {
      waitFor({
        debug: true,
        interval: 1000, // XXX the time series chart is actually
                        // visible some time after the element is
                        // visible (there's a jerky refresh thing
                        // going on). We should fix the jerky thing,
                        // then we can on the waitFor with a timeout
                        // of 0.
        timeout: 8000,
        check: function() {
          return page.evaluate(function() {
            return $('.tab-pane').is(':visible');
          });
        },
        success: function() {
          captureSelector(imgId + '.png','.tab-pane');
          phantom.exit();
        },
        error: function() {
          console.log("Error waiting for chart");
          phantom.exit();
        }
      });
    }
  });
}
