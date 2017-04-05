var _ = require('underscore');

var hashHelper = {
  getHashParams: function() {
    var hashParams = {};
    var e,
      a = /\+/g,
      r = /([^&;=]+)=?([^&;]*)/g,
      d = function(s) {
        if (typeof s === 'string') {
          if (s === 'true') {
            return true;
          } else if (s === 'false') {
            return false;
          } else {
            return decodeURIComponent(s.replace(a, " "));
          }
        } else {
          return s.map(function(e) {
            return decodeURIComponent(e.replace(a, " "));
          });
        }
      },
      hash = window.location.hash.substring(1);
    while (e = r.exec(hash)) {
      var key = e[1];
      if (key === 'numerator') {
        key = 'num';
      }
      if (key === 'denominator') {
        key = 'denom';
      }
      if (key === 'numeratorIds') {
        key = 'numIds';
      }
      if (key === 'denominatorIds') {
        key = 'denomIds';
      }
      var val = e[2];
      val = val.replace(/,\s*$/, "");
      if ((key === 'orgIds') || (key === 'numIds') || (key === 'denomIds')) {
        hashParams[d(key)] = $.map(val.split(','), function(v) {
          if (d(v) !== '') {
            return {
              id: d(v)
            };
          }
        });
      } else {
        hashParams[d(key)] = d(val);
      }
    }
        // console.log('getHashParams', hashParams);
    return hashParams;
  },

  setHashParams: function(params) {
        // console.log('setHashParams', params);
    var hash = '';
    for (var k in params) {
      if ((k === 'orgIds') || (k === 'numIds') || (k === 'denomIds')) {
        if (params[k].length > 0) {
          hash += k + '=';
          _.each(params[k], function(d, i) {
            hash += d.id;
            if (i !== (params[k].length - 1)) {
              hash += ',';
            }
          });
          hash += '&';
        }
      } else if ((k === 'hideSmallListSize') || (k === 'num') ||
                 (k === 'denom') || (k === 'org') || (k === 'selectedTab')) {
        if (params[k] !== 'chemical') {
          hash += k + '=' + params[k] + '&';
        }
      }
    }
    hash = hash.replace(/&$/, "");
    window.location.hash = hash;
    return hash;
  }
};

module.exports = hashHelper;
