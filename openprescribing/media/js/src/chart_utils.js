var moment = require('moment');
var _ = require('underscore');
var config = require('./config');

var utils = {

  getIEVersion: function() {
    var ie = (function() {
      var undef,
        v = 3,
        div = document.createElement('div'),
        all = div.getElementsByTagName('i');
      while (
                div.innerHTML = '<!--[if gt IE ' + (++v) + ']><i></i><![endif]-->',
                all[0]
            );
      return v > 4 ? v : undef;
    }());
    if ((typeof ie !== 'undefined') && (ie < 9)) {
      return true;
    } else {
      return false;
    }
  },

  constructQueryURLs: function(options) {
    var numeratorUrl = config.apiHost + '/api/1.0';
    if (options.org === 'CCG') {
      numeratorUrl += '/spending_by_ccg/?format=json';
    } else if (options.org === 'practice') {
      numeratorUrl += '/spending_by_practice/?format=json';
    } else {
      numeratorUrl += '/spending/?format=json';
    }
    var num_ids = options.numIds;
    if (num_ids.length > 0) {
      numeratorUrl += '&code=' + this.idsToString(num_ids);
    }
    var org_ids = options.orgIds;
    if ((org_ids.length > 0) && (options.org === 'practice')) {
      numeratorUrl += '&org=';
      _.each(org_ids, function(d, i) {
        if (('ccg' in d) && (d.ccg)) {
          numeratorUrl += d.ccg;
        } else {
          numeratorUrl += d.id;
        }
        numeratorUrl += (i !== (org_ids.length - 1)) ? ',' : '';
      });
    }
    var denominatorUrl = config.apiHost + '/api/1.0';
    if (options.denom === 'chemical') {
      if (options.org === 'CCG') {
        denominatorUrl += '/spending_by_ccg/?format=json';
      } else if (options.org === 'practice') {
        denominatorUrl += '/spending_by_practice/?format=json';
      } else {
        denominatorUrl += '/spending/?format=json';
      }
      var denom_ids = options.denomIds;
      if (denom_ids.length > 0) {
        denominatorUrl += '&code=' + this.idsToString(denom_ids);
      }
    } else {
      denominatorUrl += '/org_details/?format=json';
      denominatorUrl += '&org_type=' + options.org.toLowerCase();
      denominatorUrl += '&keys=' + options.denom;
    }
    if ((org_ids.length > 0) && (options.org === 'practice')) {
      denominatorUrl += '&org=';
      _.each(org_ids, function(d, i) {
        if (('ccg' in d) && (d.ccg)) {
          denominatorUrl += d.ccg;
        } else {
          denominatorUrl += d.id;
        }
        denominatorUrl += (i !== (org_ids.length - 1)) ? ',' : '';
      });
    }
    return {
      'denominatorUrl': denominatorUrl.replace("?&", "?"),
      'numeratorUrl': numeratorUrl.replace("?&", "?")
    };
  },

  idsToString: function(ids) {
    var str = '';
    _.each(ids, function(d, i) {
      str += d.id;
      str += (i !== (ids.length - 1)) ? ',' : '';
    });
    return str;
  },

  combineXAndYDatasets: function(xData, yData, values) {
        // console.log('combineXAndYDatasets');
        // Glue the x and y series data points together,
        // and returns a dataset with a row for each organisation and each month.
        // Also calculates ratios for cost and items.
    var isSpecialDenominator = ((values.x_val !== 'x_actual_cost') &&
                                    (values.x_val !== 'x_items') &&
                                    (typeof values.x_val !== 'undefined'));
    var combinedData = this.combineDatasets(xData, yData, values.x, values.x_val);
    combinedData = this.calculateRatiosForData(combinedData,
                                             isSpecialDenominator,
                                             values.x_val);
    this.sortByDateAndRatio(combinedData, 'ratio_items');
    return combinedData;
  },

  combineDatasets: function(xData, yData, x_val, x_val_key) {
    var xDataDict = _.reduce(xData, function(p, c) {
      var key = c.row_id + "-" + c.date;
      p[key] = {
        row_id: c.row_id,
        row_name: c.row_name,
        date: c.date,
        setting: c.setting,
        x_actual_cost: +c.actual_cost || 0,
        x_items: +c.items || 0,
        y_actual_cost: 0,
        y_items: 0
      };
      if (x_val.slice(0, 8) == 'star_pu.') {
        p[key][x_val_key] = +c['star_pu'][x_val.slice(8, x_val.length)];
      } else {
        p[key][x_val_key] = +c[x_val];
      }
      return p;
    }, {});
    xAndYDataDict = _.reduce(yData, function(p, c) {
      var key = c.row_id + "-" + c.date;
      if (p[key]) {
        p[key].setting = c.setting;
        p[key].y_actual_cost = +c.actual_cost || 0;
        p[key].y_items = +c.items || 0;
      } else {
        p[key] = {
          row_id: c.row_id,
          row_name: c.row_name,
          date: c.date,
          setting: c.setting,
          x_actual_cost: 0,
          x_items: 0,
          y_actual_cost: +c.actual_cost || 0,
          y_items: +c.items || 0
        };
        p[key][x_val_key] = 0;
      }
      return p;
    }, xDataDict);

    var combined = _.values(xAndYDataDict);
    return _.filter(combined, function(p) {
            // Filter out non-prescribing practices. Ignore this for CCGs.
      return (typeof (p.setting) === 'undefined') || (p.setting === 4);
    });
  },

  calculateRatiosForData: function(data, isSpecialDenominator, x_val_key) {
    var ratio_actual_cost_x = (isSpecialDenominator) ? x_val_key : 'x_actual_cost',
      ratio_item_x = (isSpecialDenominator) ? x_val_key : 'x_items';
    _.each(data, function(d, i) {
      d.name = ('row_name' in d) ? d.row_name + " (" + d.row_id + ")" : null;
      d.id = ('row_id' in d) ? d.row_id : null;
      if ((d[ratio_item_x] !== null) && (d[ratio_item_x] > 0)) {
        d.ratio_items = d.y_items / d[ratio_item_x];
        d.ratio_items = d.ratio_items * 1000;
      } else if (d[ratio_item_x] === 0) {
        d.ratio_items = null;
      }
      if ((d[ratio_actual_cost_x] !== null) && (d[ratio_actual_cost_x] > 0)) {
        d.ratio_actual_cost = d.y_actual_cost / d[ratio_actual_cost_x];
        d.ratio_actual_cost = d.ratio_actual_cost * 1000;
      } else if (d[ratio_actual_cost_x] === 0) {
        d.ratio_actual_cost = null;
      }
    });
    return data;
  },

  sortByDateAndRatio: function(data, ratio) {
        // The category data in the bar chart needs to be in order.
    data.sort(function(a, b) {
      var aDate = new Date(a.date);
      var bDate = new Date(b.date);
      var x = aDate - bDate;
      return (x === 0) ? a[ratio] - b[ratio] : x;
    });
  },

  createChartSeries: function(data) {
        // Create a deep copy of the data.
    var dataCopy = JSON.parse(JSON.stringify(data));
    var chartSeries = [{
      turboThreshold: 25000,
      data: dataCopy,
      color: 'rgba(119, 152, 191, .5)'
    }];
    return chartSeries;
  },

  indexDataByRowNameAndMonth: function(combinedData) {
        // Used in the maps.
    var newData = {};
    _.each(combinedData, function(d) {
      if (d.row_name in newData) {
        newData[d.row_name][d.date] = d;
      } else {
        newData[d.row_name] = {};
        newData[d.row_name][d.date] = d;
      }
    });
    return newData;
  },

  getAllMonthsInData: function(options) {
    var combinedData = options.data.combinedData;
        // Used for date slider.
    var monthRange = [];
    if (combinedData.length > 0) {
      var firstMonth = combinedData[0].date;
      if (options.org === 'CCG') {
        // CCGs were formed in Aug 2013. This special-casing can be
        // removed after Aug 2018, as we only deal with 5 years of
        // data.
        var firstCCGDate = '2013-08-01';
        firstMonth = firstMonth > firstCCGDate ? firstMonth : firstCCGDate;
      }
      var lastMonth = combinedData[combinedData.length - 1].date;
      var startDate = moment(firstMonth);
      var endDate = moment(lastMonth);
      if (endDate.isBefore(startDate)) {
        throw "End date must be greater than start date.";
      }
      while (startDate.isBefore(endDate) || startDate.isSame(endDate)) {
        monthRange.push(startDate.format("YYYY-MM-01"));
        startDate.add(1, 'month');
      }
    }
    return monthRange;
  },

  calculateMinMaxByDate: function(combinedData) {
    // Used in maps.
    var minMaxByDate = {};
    var temp = {};
    _.each(combinedData, function(d) {
      if (d.date in temp) {
        temp[d.date].push(d);
      } else {
        temp[d.date] = [d];
      }
    });
    for (var date in temp) {
      minMaxByDate[date] = {};
      minMaxByDate[date].ratio_actual_cost = this.calculateMinMax(temp[date], 'ratio_actual_cost');
      minMaxByDate[date].ratio_items = this.calculateMinMax(temp[date], 'ratio_items');
    }

    return minMaxByDate;
  },

  calculateMinMax: function(arr, key) {
    return [_.min(_.pluck(arr, key)), _.max(_.pluck(arr, key))];
  },

  setChartValues: function(options) {
    var y = options.activeOption,
      x = (options.denom === 'chemical') ? y : options.denom,
      x_val = (options.denom === 'chemical') ? 'x_' + y : options.denom;
    return {
      y: 'y_' + y,
      x: x,
      x_val: x_val,
      ratio: 'ratio_' + y
    };
  }
};

module.exports = utils;
