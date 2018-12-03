var expect = require('chai').expect;
var csvUtils = require('../src/csv-utils');

describe('csvUtils', function() {

  describe('#formatTableAsCSV', function() {
    it('returns valid CSV', function() {
      var result = csvUtils.formatTableAsCSV([
        ['one', 'two', 'three'],
        [1, null, 'with, comma'],
        [2, 'a', 'with " double quote'],
      ]);
      expect(result).to.equal('one,two,three\n1,,"with, comma"\n2,a,"with "" double quote"');
    });
  });

  describe('#getFilename', function() {
    it('removes special characters from string and collaposes multiple spaces', function() {
      var result = csvUtils.getFilename('Hello $" 123-456.test_str : ');
      expect(result).to.equal('Hello 123-456.test_str.csv');
    });
  });

});
