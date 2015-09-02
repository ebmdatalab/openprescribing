global.jQuery = require('jquery');
global.$ = global.jQuery;
var Fuse = require('./vendor/fuse');

var listFilter = {

   setUp: function() {
        var fuse,
        $inputSearch = $(inputSearch),
        $resultsList = $(resultsList);

        $inputSearch.val('');

        function search() {
            var searchTerm = $inputSearch.val(),
                r = (searchTerm === '') ? allItems : fuse.search(searchTerm);
            $resultsList.empty();
            var allHtml = '';
            $.each(r, function() {
                var html = '<li class="result-item">';
                html += '<a href="' + this.url + '">';
                html +=  this.name + '</a> (' + this.code + ')</li>';
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
              keys: ["name", "code"]
            };
            fuse = new Fuse(allItems, options);
        }

        var delay = (function(){
          var timer = 0;
          return function(callback, ms){
          clearTimeout (timer);
          timer = setTimeout(callback, ms);
         };
        })();

        $inputSearch.on('keyup', function() {
          delay(function(){
            search();
          }, 300);
        });
        createFuse();
    }
};

listFilter.setUp();