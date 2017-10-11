global.jQuery = require('jquery');
global.$ = global.jQuery;
require('select2');
var _ = require('underscore');
var Cookies = require('cookies-js');

var config = require('./config');

var homeForm = {
  el: {
    orgIds: '#homeOrg',
  },

  setUp: function() {
   function repoFormatSelection(repo) {
      return repo.full_name;
   }
    var select2Options = {
      dropdownCssClass: 'bigdrop',
      placeholder: "add names or codes",
      // allowClear: true,
      escapeMarkup: function(markup) {
        return markup;
      },
      minimumInputLength: 1,
      templateResult: function (d) {
        if (d.loading) return d.text;
        return d.text;
      },
      ajax: {
        url: config.apiHost + '/api/1.0/org_code?org_type=CCG,practice&format=json',
        dataType: 'json',
        delay: 50,
        quietMillis: 250,
        data: function(params) {
          return {
            q: params.term,
            page: params.page,
          };
        },
        processResults: function (data, page) { // parse the results into the format expected by Select2.
          // since we are using custom formatting functions we do not need to alter the remote JSON data
          results = [];
          practices = [];
          ccgs = [];

          _.each(data, function(d) {
            if (d.type == 'CCG') {
              ccgs.push({id: d.id, text: d.name, type: 'CCG'});
            } else {
              practices.push({id: d.id, text: d.name + ' (in <em>' + d.postcode + '</em>)', type: 'practice'});
            }
          });
          if (practices.length > 0) {
            results.push(
              {
                text: 'Practices',
                children: practices,
              });
          }
          if (ccgs.length > 0) {
            results.push(
              {
                text: 'CCGs',
                children: ccgs,
              });
          }
          return {results: results};
        },
        cache: false,
      },
    };
    $(this.el.orgIds).select2(select2Options).on('select2:select', function(e) {
      data = $(this).select2('data')[0];
      Cookies.set('home', JSON.stringify(data));
      if (data.type == 'CCG') {
        window.location = '/ccg/' + data.id;
      } else {
        window.location = '/practices/' + data.id;
      }
    });
    var saved = Cookies.get('home');
    if (typeof(saved) !== 'undefined') {
      var data = $.parseJSON(saved);
      $(this.el.orgIds).val(data.id);
      var newOption = new Option(data.text, data.id, true, true);
      $(this.el.orgIds).append(newOption).trigger('change');
    }
  },
};

module.exports = homeForm;
