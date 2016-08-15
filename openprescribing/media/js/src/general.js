var Cookies = require('js-cookie');

$(document).ready(function() {
  //
  // Feedback form
  //

  // Ensure it's correctly positioned so only the tab shows
  $(window).resize(function() {
    placeFeedbackForm();
  });
  placeFeedbackForm();
  // Form submission handling and behaviour
  $("#send-feedback").click(function() {
    var csrftoken = Cookies.get('csrftoken');
    /**
     * Tests if a given HTTP method is considered CSRF-safe
     * @param {string} method The HTTP method to check
     * @return {boolean} If the method is allowed
     */
    function csrfSafeMethod(method) {
      // these HTTP methods do not require CSRF protection
      return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup({
      beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
          xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
      }
    });
    $.post("/feedback/", $("#feedback form").serialize(), function() {
      // Visual feedback that it's been done
      $('#send-feedback').attr('value', "Thankyou!");
      $('#send-feedback').addClass('btn-success');
      $("#feedback form :input").attr("disabled", "disabled");
      // Hide the form again after a short delay
      $("#feedback").delay(2000).animate(
        {top: $(window).height()},
        {complete: function() {
          $('#send-feedback').attr('value', "Send");
          $("#feedback form :input").removeAttr("disabled");
          $('#send-feedback').removeClass('btn-success');
        }});
      $(this).data('showing', false);
    });
  });
  // The tab that users can click to show/hide the form
  $(".pull_feedback").click(function() {
    var showing = $(this).attr('data-showing');
    showing = showing === 'true' || showing === true;
    if (showing) {
      $("#feedback").animate({top: $(window).height() + 10});
      $(this).attr('data-showing', false);
    } else {
      $("#feedback").animate(
        {top: (parseInt($(window).height(), 10) -
               parseInt($('#feedback').height(), 10))}
      );
      $(this).attr('data-showing', true);
      return false;
    }
  }).delay(2000).queue(function(next) {
    // Gentle wobble to show it's there
    $(this).addClass("shake");
    next();
  });
});

/**
 * Hide feedback form off the bottom of the window
 */
function placeFeedbackForm() {
  var windHeight = $(window).height();
  $('#feedback').css('top', parseInt(windHeight, 10) + 10);
}
