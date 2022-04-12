import "bootstrap";
import domready from "domready";
import Fuse from "fuse.js";

const listFilter = {
  setUp() {
    let fuse;
    const $inputSearch = $(inputSearch);
    const $resultsList = $(resultsList);
    const minSearchLength = $inputSearch.data("min-search-length");
    $inputSearch.val("");

    function search() {
      const searchTerm = $inputSearch.val();
      let r;
      if (minSearchLength && searchTerm.length < minSearchLength) {
        r = [];
      } else if (searchTerm === "") {
        r = allItems;
      } else {
        r = fuse.search(searchTerm);
      }
      $resultsList.empty();
      let allHtml = "";
      $.each(r, function () {
        let html = '<li class="result-item">';
        html += `<a href="${this.url}">`;
        html += `${this.name}</a> (${this.code})</li>`;
        allHtml += html;
      });
      $resultsList.html(allHtml);
    }

    function createFuse() {
      const options = {
        caseSensitive: false,
        includeScore: false,
        shouldSort: false,
        threshold: 0.2,
        location: 0,
        distance: 1000,
        maxPatternLength: 32,
        keys: ["name", "code"],
      };
      fuse = new Fuse(allItems, options);
    }

    const delay = (() => {
      let timer = 0;
      return (callback, ms) => {
        clearTimeout(timer);
        timer = setTimeout(callback, ms);
      };
    })();

    $inputSearch.on("keyup", () => {
      delay(() => {
        search();
      }, 300);
    });
    createFuse();
  },
};

export default listFilter;
domready(() => {
  listFilter.setUp();
});
