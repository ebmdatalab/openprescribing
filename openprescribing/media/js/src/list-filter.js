var $ = require('jquery');

require('bootstrap');
var Fuse = require('../vendor/fuse');
var domready = require('domready');

var listFilter = {

  setUp: function() {
    var fuse;
    var $inputSearch = $(inputSearch);
    var $resultsList = $(resultsList);
    var minSearchLength = $inputSearch.data('min-search-length');
    $inputSearch.val('');

    function search() {
      var searchTerm = $inputSearch.val();
      var r;
      if (minSearchLength && searchTerm.length < minSearchLength) {
        r = [];
      } else if (searchTerm === '') {
        r = allItems;
      } else {
        r = fuse.search(searchTerm);
      }
      $resultsList.empty();
      var allHtml = '';
      $.each(r, function() {
        var html = '<li class="result-item">';
        html += '<a href="' + this.url + '">';
        html += this.name + '</a> (' + this.code + ')</li>';
        allHtml += html;
      });
      $resultsList.html(allHtml);
    }

    function createFuse() {
      var options = {
        caseSensitive: false,
        includeScore: false,
        shouldSort: false,
        threshold: 0.2,
        location: 0,
        distance: 1000,
        maxPatternLength: 32,
        keys: ['name', 'code'],
      };
      fuse = new Fuse(allItems, options);
    }

    var delay = (function() {
      var timer = 0;
      return function(callback, ms) {
        clearTimeout(timer);
        timer = setTimeout(callback, ms);
      };
    })();

    $inputSearch.on('keyup', function() {
      delay(function() {
        search();
      }, 300);
    });
    createFuse();
  },
};

module.exports = listFilter;
domready(function() {
  listFilter.setUp();
});
