global.jQuery = require('jquery');
global.$ = global.jQuery;
var _ = require('underscore');
var humanize = require('humanize');
var config = require('./config');
var utils = {

  getDataUrls: function(options) {
    var panelUrl = config.apiHost + '/api/1.0/measure_by_';
    panelUrl += options.orgType.toLowerCase() + '/?format=json';
    var urls = {
      panelMeasuresUrl: panelUrl,
      globalMeasuresUrl: config.apiHost + '/api/1.0/measure/?format=json'
    };
    if (options.orgId) {
      urls.panelMeasuresUrl += '&org=' + options.orgId;
    }
    if (options.measure) {
      urls.panelMeasuresUrl += '&measure=' + options.measure;
      urls.globalMeasuresUrl += '&measure=' + options.measure;
    }
    return urls;
  },

  getCentilesAndYAxisExtent: function(globalData, options, centiles) {
    /*
    If there is a single global set of centiles, calculate the global
    y-axis min and max. We will use this to set the y-axis extent of
    all the charts consistently. This is because visual comparisons
    are much easier if the y-axes are consistent.
    */
    var _this = this;
    var globalCentiles = {};
    var globalYMax = 0;
    var globalYMin = 0;
    if (options.rollUpBy !== 'measure_id') {
      var series = _.findWhere(globalData, {id: options.measure});
      if (series) {
        _.each(centiles, function(i) {
          globalCentiles[i.toString()] =
          _this._addHighchartsXAndY(series.data,
            true, series.is_percentage, options, i);
        });
        globalYMax = _.max(globalCentiles['90'], _.property('y'));
        globalYMin = _.min(globalCentiles['10'], _.property('y'));
      }
    }
    return {
      globalCentiles: globalCentiles,
      globalYMax: globalYMax,
      globalYMin: globalYMin
    };
  },

  annotateData: function(panelData, options, numMonths) {
    /*
    Create a new array with an item for each chart, each chart being
    either a measure or an organisation, as appropriate.
    Annotate each chart with the mean percentile over the past
    N months, and cost saving if appropriate.
    */
    var _this = this;
    if (panelData.length) {
      if (options.rollUpBy !== 'measure_id') {
        panelData = _this._rollUpByOrg(panelData[0], options.orgType);
      }
      panelData = _this._getSavingAndPercentilePerItem(panelData,
                                                       numMonths);
    }
    return panelData;
  },

  sortData: function(panelData) {
    /*
       Sort data such that the worst scores come first (but nulls
       always come at the bottom).
    */
    var sortedArray = _(panelData).chain().sortBy(function(d) {
      // Sort by `id` first, so that tiles are always returned in a
      // predictable order
      return d.id;
    }).sortBy(function(d) {
      // Now by score, respecting `lowIsGood`
      var score = d.meanPercentile;
      if (score === null) {
        score = 101;
      } else if (d.lowIsGood !== false) {
        score = 100 - score;
      }
      return score;
    }).value();
    return sortedArray;
  },

  _rollUpByOrg: function(data, orgType) {
    var rolled = {};
    _.each(data.data, function(d) {
      var id = (orgType === 'practice') ? d.practice_id : d.pct_id;
      var name = (orgType === 'practice') ? d.practice_name : d.pct_name;
      if (id in rolled) {
        rolled[id].data.push(d);
      } else {
        rolled[id] = {
          id: id,
          name: name,
          numeratorShort: data.numerator_short,
          denominatorShort: data.denominator_short,
          data: [d],
          isCostBased: data.is_cost_based,
          isPercentage: data.is_percentage
        };
      }
    });
    var rolledArr = [];
    for (var orgId in rolled) {
      if (rolled[orgId]) {
        rolledArr.push(rolled[orgId]);
      }
    }
    return rolledArr;
  },

  _getSavingAndPercentilePerItem: function(data, numMonths) {
    /*
    For each measure, or org, in the data, get the mean percentile,
    and the mean cost saving at the 50th percentile,
    over the number of months specified.
    We'll use this to sort the charts by percentile or saving.
    */
    _.each(data, function(d) {
      var latestData = d.data.slice(numMonths * -1);
      var sum = _.reduce(latestData, function(memo, num) {
        return (num.percentile === null) ? memo : memo + num.percentile;
      }, null);
      var validMonths = _.filter(latestData, function(d) {
        return (d.percentile !== null);
      }).length;
      d.meanPercentile = (sum === null) ? null : sum / validMonths;
      d.costSaving50th = _.reduce(latestData, function(memo, num) {
        var saving = (num.cost_savings) ? num.cost_savings['50'] : null;
        return memo + saving;
      }, null);
      d.costSaving10th = _.reduce(latestData, function(memo, num) {
        // We assume that `low_is_good` for all cost-savings
        var saving = (num.cost_savings) ? num.cost_savings['10'] : null;
        return memo + saving;
      }, null);
      // normalise to camelcase convention
      if (!('isPercentage' in d)) {
        d.isPercentage = d.is_percentage;
      }
      if (!('isCostBased' in d)) {
        d.isCostBased = d.is_cost_based;
      }
      if (!('numeratorShort' in d)) {
        d.numeratorShort = d.numerator_short;
        d.denominatorShort = d.denominator_short;
      }
    });
    return data;
  },

  getPerformanceSummary: function(orderedData, options, numMonths) {
    /*
    Get the introductory paragraph for the page, talking about
    (if applicable) the number of practices above the
    median, or (if applicable) the cost savings available.
    */
    var perf = {
      total: 0,
      worseThanMedian: 0,
      potentialSavings50th: 0,
      potentialSavings10th: 0,
      orgId: options.orgId,
      measureId: options.measure
    };
    if (orderedData.length) {
      _.each(orderedData, function(d) {
        if (d.meanPercentile !== null) {
          perf.total += 1;
          if (d.lowIsGood !== false && d.meanPercentile > 50) {
            perf.worseThanMedian += 1;
          } else if (d.lowIsGood === false && d.meanPercentile < 50) {
            perf.worseThanMedian += 1;
          }
          if (d.meanPercentile > 50) {
            perf.potentialSavings50th +=
              (options.isCostBasedMeasure) ? d.costSaving50th : 0;
          }
          if (d.meanPercentile > 10) {
            perf.potentialSavings10th +=
              (options.isCostBasedMeasure) ? d.costSaving50th : 0;
          }
        }
      });
      perf.proportionAboveMedian =
        humanize.numberFormat(perf.proportionAboveMedian * 100, 1);
      if (options.isCostBasedMeasure) {
        if (options.rollUpBy === 'measure_id') {
          perf.costSavings = 'Over the past ' + numMonths + ' months, if this ';
          perf.costSavings += (options.orgType === 'practice') ?
            "practice " : "CCG ";
          perf.costSavings += ' had prescribed at the median ratio or better ' +
            'on all cost-saving measures below, then it would have spent £' +
            humanize.numberFormat(perf.potentialSavings50th, 2) +
            ' less. (We use the national median as a suggested ' +
            'target because by definition, 50% of practices were already ' +
            'prescribing at this level or better, so we think it ought ' +
            'to be achievable.)';
        } else {
          perf.costSavings = 'Over the past ' + numMonths + ' months, if all ';
          perf.costSavings += (options.orgType === 'practice') ?
            "practices " : "CCGs ";
          perf.costSavings += 'had prescribed at the median ratio ' +
            'or better, then ';
          perf.costSavings += (options.orgType === 'practice') ?
            "this CCG " : "NHS England ";
          perf.costSavings += 'would have spent £' +
            humanize.numberFormat(perf.potentialSavings50th, 2) +
            ' less. (We use the national median as a suggested ' +
            'target because by definition, 50% of ';
          perf.costSavings += (options.orgType === 'practice') ?
            "practices " : "CCGs ";
          perf.costSavings += 'were already prescribing ' +
            'at this level or better, so we think it ought to be achievable.)';
        }
      }
    } else {
      perf.performanceDescription = "This organisation hasn't " +
        "prescribed on any of these measures.";
    }
    return perf;
  },

  addChartAttributes: function(data, globalData, globalCentiles,
    centiles, options, numMonths) {
    /*
    Expects an array that represents a series of charts. For
    each chart, add Highcharts attributes to the data,
    merge in centiles and low_is_good from the global data, and
    add chart title, URL, description etc.
    */
    var _this = this;
    var newData = [];
    _.each(data, function(d) {
      d.data = _this._addHighchartsXAndY(d.data, false,
        d.isPercentage, options, null);
      if (options.rollUpBy === 'measure_id') {
        // If each chart is a different measure, get the
        // centiles for that measure, and if lowIsGood
        var series = _.findWhere(globalData, {id: d.id});
        if (typeof series !== 'undefined') {
          d.lowIsGood = series.low_is_good;
        }
        d.globalCentiles = {};
        _.each(centiles, function(i) {
          d.globalCentiles[i] = _this._addHighchartsXAndY(series.data,
            true, series.is_percentage, options, i);
        });
      } else {
        d.globalCentiles = globalCentiles;
        d.lowIsGood = options.lowIsGood;
      }
      d.chartId = d.id;
      _.extend(d, _this._getChartTitleEtc(d, options, numMonths));
      newData.push(d);
    });
    return newData;
  },

  _addHighchartsXAndY: function(data, isGlobal, isPercentage,
      options, centile) {
    // Add X and Y attributes in the format that Highcharts expects.
    var dataCopy = JSON.parse(JSON.stringify(data));
    _.each(dataCopy, function(d, i) {
      var dates = d.date.split('-');
      d.x = Date.UTC(dates[0], dates[1] - 1, dates[2]);
      if (isGlobal) {
        var p = d.percentiles;
        var org = options.orgType.toLowerCase();
        d.y = (p && p[org] && p[org][centile] !== null) ?
          parseFloat(p[org][centile]) : null;
      } else {
        d.y = (d.calc_value === null) ? null : parseFloat(d.calc_value);
      }
      if (isPercentage) {
        d.y = (isPercentage && d.y) ? d.y * 100 : d.y;
      }
    });
    return dataCopy;
  },

  _getChartTitleEtc: function(d, options, numMonths) {
    var chartTitle;
    var chartTitleUrl;
    var chartExplanation = '';
    var measureUrl;
    if (options.rollUpBy === 'measure_id') {
      // We want measure charts to link to the
      // measure-by-all-practices-in-CCG page.
      chartTitle = d.name;
      chartTitleUrl = '/ccg/';
      chartTitleUrl += (options.parentOrg) ? options.parentOrg : options.orgId;
      chartTitleUrl += '/' + d.id;
      measureUrl = '/measure/' + d.id;
    } else {
      // We want organisation charts to link to the appropriate
      // organisation page.
      chartTitle = d.id + ': ' + d.name;
      chartTitleUrl = '/' + options.orgType.toLowerCase() +
        '/' + d.id;
    }
    if (d.meanPercentile === null) {
      chartExplanation = 'No data available.';
    } else {
      if (d.lowIsGood === null) {
        chartExplanation = (
          'This is a measure where there is disagreement about whether ' +
            'higher, or lower, is better. Nonetheless it is interesting to ' +
            'know if a ' + options.orgType + ' is a long way from average ' +
            'prescribing behaviour. ');
      }
      if (d.isCostBased || options.isCostBasedMeasure) {
        if (d.costSaving50th < 0) {
          chartExplanation += 'By prescribing better than the median, ' +
            'this ' + options.orgType + ' has saved the NHS £' +
            humanize.numberFormat((d.costSaving50th * -1), 2) +
            ' over the past ' + numMonths + ' months.';
        } else {
          chartExplanation += 'If it had prescribed in line with the ' +
            'median, this ' + options.orgType + ' would have spent £' +
            humanize.numberFormat(d.costSaving50th, 2) +
            ' less over the past ' + numMonths + ' months.';
        }
        if (d.costSaving10th > 0) {
          chartExplanation += ' If it had prescribed in line with the best ' +
            '10%, it would have spent £' +
            humanize.numberFormat(d.costSaving10th, 2) + ' less. ';
        }
      }
    }
    return {
      measureUrl: measureUrl,
      chartTitle: chartTitle,
      chartTitleUrl: chartTitleUrl,
      chartExplanation: chartExplanation
    };
  },

  getGraphOptions: function(d, options, isPercentageMeasure, chartOptions) {
    // Assemble the series for the chart, and add chart config options.
    if (d.data.length) {
      var hcOptions = this._getChartOptions(d, isPercentageMeasure,
        options, chartOptions);
      hcOptions.series = [{
        name: 'This ' + options.orgType,
        isNationalSeries: false,
        data: d.data,
        color: 'red',
        marker: {
          radius: 2
        }
      }];
      _.each(_.keys(d.globalCentiles), function(k) {
        var e = {
          name: k + 'th percentile nationally',
          isNationalSeries: true,
          data: d.globalCentiles[k],
          dashStyle: 'dot',
          color: 'blue',
          lineWidth: 1,
          marker: {
            enabled: false
          }
        };
        // Distinguish the median visually.
        if (k === '50') {
          e.dashStyle = 'longdash';
        }
        hcOptions.series.push(e);
      });
      return hcOptions;
    }
    return null;
  },

  _getChartOptions: function(d, isPercentageMeasure,
        options, chartOptions) {
    /*
    Get Highcharts config for each chart: set
    Y-axis minimum, maximum, and label, and tooltip.
    */
    var chOptions = $.extend(true, {}, chartOptions.dashOptions);
    var localMax = _.max(d.data, _.property('y'));
    var localMin = _.min(d.data, _.property('y'));
    var ymax;
    var ymin;
    isPercentageMeasure = (d.isPercentage || isPercentageMeasure);
    chOptions.chart.renderTo = d.chartId;
    chOptions.chart.height = 200;
    chOptions.legend.enabled = false;
    if (options.rollUpBy === 'org_id') {
      ymax = _.max([localMax.y, options.globalYMax.y]);
      ymin = _.min([localMin.y, options.globalYMin.y]);
    } else {
      var local90thMax = _.max(d.globalCentiles['90'], _.property('y'));
      ymax = _.max([localMax.y, local90thMax.y]);
      var local90thMin = _.min(d.globalCentiles['10'], _.property('y'));
      ymin = _.min([localMin.y, local90thMin.y]);
    }
    var yAxisLabel = (isPercentageMeasure) ? '%' : 'Measure';
    chOptions.yAxis = {
      title: {
        text: yAxisLabel
      },
      max: ymax,
        // If ymin is zero, Highcharts will sometimes pick a negative value
        // because it prefers that formatting. Force zero as the lowest value.
      min: _.max([0, ymin])
    };
    if (d.lowIsGood === false) {
      chOptions.yAxis.reversed = true;
    }
    chOptions.tooltip = {
      formatter: function() {
        var num = humanize.numberFormat(this.point.numerator, 0);
        var denom = humanize.numberFormat(this.point.denominator, 0);
        var percentile = humanize.numberFormat(this.point.percentile, 0);
        var str = '';
        str += '<b>' + this.series.name;
        str += ' in ' + humanize.date('M Y', new Date(this.x));
        str += '</b><br/>';
        if (!this.series.options.isNationalSeries) {
          str += d.numeratorShort + ': ' + num;
          str += '<br/>';
          str += d.denominatorShort + ': ' + denom;
          str += '<br/>';
        }
        str += 'Measure: ' + humanize.numberFormat(this.point.y, 3);
        str += (isPercentageMeasure) ? '%' : '';
        if (!this.series.options.isNationalSeries) {
          str += ' (' + humanize.ordinal(percentile);
          str += ' percentile)';
        }
        return str;
      }
    };
    return chOptions;
  }

};

module.exports = utils;
