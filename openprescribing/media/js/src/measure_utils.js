var $ = require('jquery');
var _ = require('underscore');
var humanize = require('humanize');
var config = require('./config');
var downloadjs = require('downloadjs');
var csvUtils = require('./csv-utils');

var utils = {

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
      globalYMin: globalYMin,
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
    _.each(panelData, function(d) {
      if (options.specificMeasures) {
        // These are any measures that have been defined to appear at
        // specific locations in the DOM - from embedded javascript in
        // templates
        d.chartContainerId = _.findWhere(
          options.specificMeasures, {measure: d.id}).chartContainerId;
      } else {
        d.chartContainerId = '#charts';
      }
    });
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
      // For aggregates (i.e. the "All England" charts) we sort by cost saving
      // as sorting by mean percentile doesn't make any sense
      var score = d.isAggregateEntity ? d.costSaving50th : d.meanPercentile;
      // For the All England view, always sort the Low Priority Omnibus measure to the top
      if (d.isAggregateEntity && d.id === 'lpzomnibus') {
        score = 999999999999;
      }
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
      var id;
      var name;

      if (orgType === 'ccg') {
        id = d['pct_id'];
        name = d['pct_name'];
      } else {
        id = d[orgType + '_id'];
        name = d[orgType + '_name'];
      }

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
          isPercentage: data.is_percentage,
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
    var perf = {};
    var potentialSavings50th = 0;

    if (orderedData.length) {
      _.each(orderedData, function(d) {
        if (d.meanPercentile !== null) {
          if (d.meanPercentile > 50) {
            potentialSavings50th +=
              (options.isCostBasedMeasure || d.isCostBased) ? d.costSaving50th : 0;
          }
        }
      });
      if (options.rollUpBy === 'measure_id' && ! options.aggregate) {
        if (potentialSavings50th > 0) {
          perf.costSavings = 'Over the past ' + numMonths + ' months, if this ';
          perf.costSavings += options.orgTypeHuman;
          perf.costSavings += ' had prescribed at the median ratio or better ' +
            'on all cost-saving measures below, then it would have spent £' +
            humanize.numberFormat(potentialSavings50th, 0) +
            ' less. (We use the national median as a suggested ' +
            'target because by definition, 50% of practices were already ' +
            'prescribing at this level or better, so we think it ought ' +
            'to be achievable.)';
        }
      } else if (options.isCostBasedMeasure) {
        perf.costSavings = 'Over the past ' + numMonths + ' months, if all ';
        perf.costSavings += options.orgTypeHuman;
        perf.costSavings += 's had prescribed at the median ratio ' +
          'or better, then ';
        if (options.parentOrgTypeHuman) {
          perf.costSavings += 'this ' + options.parentOrgTypeHuman;
        } else {
          perf.costSavings += 'NHS England';
        }
        perf.costSavings += ' would have spent £' +
          humanize.numberFormat(potentialSavings50th, 0) +
          ' less. (We use the national median as a suggested ' +
          'target because by definition, 50% of ';
        perf.costSavings += options.orgTypeHuman;
        perf.costSavings += 's were already prescribing ' +
          'at this level or better, so we think it ought to be achievable.)';
      }
    } else {
      perf.performanceDescription = 'This organisation hasn\'t ' +
        'prescribed on any of these measures.';
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
    var series;
    _.each(data, function(d) {
      d.data = _this._addHighchartsXAndY(
        d.data, false, d.isPercentage, options, null);
      if (options.rollUpBy === 'measure_id') {
        // If each chart is a different measure, get the
        // centiles for that measure, and if lowIsGood
        series = _.findWhere(globalData, {id: d.id});
        if (typeof series !== 'undefined') {
          d.lowIsGood = series.low_is_good;
          d.tagsFocus = series.tags_focus;
          d.numeratorCanBeQueried = series.numerator_is_list_of_bnf_codes;
        }
        d.globalCentiles = {};
        _.each(centiles, function(i) {
          d.globalCentiles[i] = _this._addHighchartsXAndY(series.data,
            true, series.is_percentage, options, i);
        });
      } else {
        // sometimes, the measure metadata is defined in javascript
        // expressions within the django template.
        d.globalCentiles = globalCentiles;
        d.lowIsGood = options.lowIsGood;
        d.tagsFocus = options.tagsFocus;
        series = _.findWhere(globalData, {id: options.measure});
        if (typeof series !== 'undefined') {
          d.numeratorCanBeQueried = series.numerator_is_list_of_bnf_codes;
        }
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
        var orgType = options.orgType;
        d.y = (p && p[orgType] && p[orgType][centile] !== null) ?
          parseFloat(p[orgType][centile]) : null;
      } else {
        d.y = (d.calc_value === null) ? null : parseFloat(d.calc_value);
      }
      if (isPercentage) {
        d.y = (isPercentage && d.y) ? d.y * 100 : d.y;
      }
    });
    return dataCopy;
  },

  _buildUrl: function(urlTemplate, context) {
    if (typeof urlTemplate == 'undefined') {
      return null;
    }

    return urlTemplate.replace(/\{(\w+)\}/g, function(_, key) {
      var value = context[key];
      if (value === null || typeof value === 'undefined') {
        throw 'Invalid value for ' + key +' in ' + urlTemplate + ': ' + value;
      }
      return value;
    });
  },

  _getChartTitleEtc: function(d, options, numMonths) {
    var chartTitle;
    var chartTitleUrl;
    var chartExplanation = '';
    var measureUrl;
    var oneEntityUrl;
    var tagsFocusUrl;
    var measureForAllPracticesUrl;
    var measureForAllCCGsUrl;
    var context = {};
    var _this = this;

    if (options.rollUpBy == 'measure_id') {
      chartTitle = d.name;
      context['measure'] = d.id;
      context['entity_code'] = options.orgId;
      context[options.orgType + '_code'] = options.orgId;
      if (options.orgType == 'practice') {
        context['ccg_code'] = options.parentOrgId;
      }
    } else {
      chartTitle = d.id + ': ' + d.name;
      context['measure'] = options.measure;
      context['entity_code'] = d.id;
      context[options.orgType + '_code'] = d.id;
    }

    chartTitleUrl = _this._buildUrl(
      options.chartTitleUrlTemplate,
      context
    );
    measureUrl = _this._buildUrl(
      options.measureUrlTemplate,
      context
    );
    measureForAllPracticesUrl = _this._buildUrl(
      options.measureForAllPracticesUrlTemplate,
      context
    );
    measureForAllCCGsUrl = _this._buildUrl(
      options.measureForAllCCGsUrlTemplate,
      context
    );
    tagsFocusUrl = _this._buildUrl(
      options.tagsFocusUrlTemplate,
      context
    );
    if (tagsFocusUrl) {
      tagsFocusUrl = tagsFocusUrl + '?tags=' + d.tagsFocus;
    }
    oneEntityUrl = _this._buildUrl(
      options.oneEntityUrlTemplate,
      context
    );

    var isAggregateEntity = options.aggregate;
    var costDataAvailable = d.isCostBased && d.costSaving10th;
    if (d.meanPercentile !== null || costDataAvailable) {
      if (d.lowIsGood === null) {
        chartExplanation = (
          'This is a measure where there is disagreement about whether ' +
            'higher, or lower, is better. Nonetheless it is interesting to ' +
            'know if a ' + options.orgTypeHuman + ' is a long way from average ' +
            'prescribing behaviour. ');
      }
      if (d.isCostBased || options.isCostBasedMeasure) {
        var noun1 = 'it';
        var noun2 = 'this ' + options.orgTypeHuman;
        var noun3 = 'it';
        if (isAggregateEntity) {
          noun1 = 'all ' + options.orgTypeHuman + 's in England';
          noun2 = 'the NHS';
          noun3 = 'they';
        }
        if (d.costSaving50th < 0) {
          chartExplanation += 'By prescribing better than the median, ' +
            'this ' + options.orgTypeHuman + ' has saved the NHS £' +
            humanize.numberFormat((d.costSaving50th * -1), 0) +
            ' over the past ' + numMonths + ' months.';
        } else {
          chartExplanation += 'If ' + noun1 + ' had prescribed in line with the ' +
            'median, ' + noun2 + ' would have spent £' +
            humanize.numberFormat(d.costSaving50th, 0) +
            ' less over the past ' + numMonths + ' months.';
        }
        if (d.costSaving10th > 0) {
          chartExplanation += ' If ' + noun3 + ' had prescribed in line with the best ' +
            '10%, it would have spent £' +
            humanize.numberFormat(d.costSaving10th, 0) + ' less. ';
        }
      }
    }
    return {
      orgType: options.orgType,
      orgTypeHuman: options.orgTypeHuman,
      comparisonOrgTypeHuman: options.orgType == 'practice' ? 'CCG' : options.orgTypeHuman,
      measureUrl: measureUrl,
      isAggregateEntity: isAggregateEntity,
      chartTitle: chartTitle,
      oneEntityUrl: oneEntityUrl,
      chartTitleUrl: chartTitleUrl,
      tagsFocus: d.tagsFocus,
      tagsFocusUrl: tagsFocusUrl,
      measureForAllPracticesUrl: measureForAllPracticesUrl,
      measureForAllCCGsUrl: measureForAllCCGsUrl,
      chartExplanation: chartExplanation,
      tags: d.tags,
      tagsForDisplay: (d.tags || []).filter(function(t) { return t.id !== 'core'; })
    };
  },

  getGraphOptions: function(d, options, isPercentageMeasure, chartOptions) {
    // Assemble the series for the chart, and add chart config options.
    if ( ! d.data.length) {
      return null;
    }
    var hcOptions = this._getChartOptions(d, isPercentageMeasure,
      options, chartOptions);
    hcOptions.series = [];
    hcOptions.series.push({
      name: ( ! options.aggregate) ? ('This ' + options.orgTypeHuman) : options.orgName,
      isNationalSeries: false,
      showTooltip: true,
      data: d.data,
      events: {
        legendItemClick: function() { return false; }
      },
      color: 'red',
      showInLegend: true,
      marker: {
        radius: 2,
      },
    });
    _.each(_.keys(d.globalCentiles), function(k) {
      var e = {
        name: k + 'th percentile nationally',
        isNationalSeries: true,
        showTooltip: false,
        data: d.globalCentiles[k],
        dashStyle: 'dot',
        events: {
          legendItemClick: function() { return false; }
        },
        color: 'blue',
        lineWidth: 1,
        showInLegend: false,
        marker: {
          enabled: false,
        },
      };
      // Distinguish the median visually.
      if (k === '50') {
        e.dashStyle = 'longdash';
      }
      // Show median and an arbitrary decile in the legend
      if (k === '10' || k === '50') {
        e.showInLegend = true;
      }
      hcOptions.series.push(e);
    });
    return hcOptions;
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
    chOptions.chart.height = 250;
    chOptions.legend = {
      enabled: true,
      x: 0,
      y: 0,
      labelFormatter: function() {
        // Rename selected series for the legend
        if (this.name === '10th percentile nationally') {
          return "National decile";
        } else if (this.name === '50th percentile nationally') {
          return "National median";
        } else {
          return this.name;
        }
      }
    };
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
        text: yAxisLabel,
      },
      max: ymax,
        // If ymin is zero, Highcharts will sometimes pick a negative value
        // because it prefers that formatting. Force zero as the lowest value.
      min: _.max([0, ymin]),
    };
    if (d.lowIsGood === false) {
      chOptions.yAxis.reversed = true;
    }
    chOptions.tooltip = {
      formatter: function() {
        if ( ! this.series.options.showTooltip) {
          return false;
        }
        var num = humanize.numberFormat(this.point.numerator, 0);
        var denom;
        var percentile = humanize.numberFormat(this.point.percentile, 0);
        var str = '';
        str += '<b>' + this.series.name;
        str += ' in ' + humanize.date('M Y', new Date(this.x));
        str += '</b><br/>';
        if ( ! this.series.options.isNationalSeries) {
          str += d.numeratorShort + ': ' + num;
          str += '<br/>';
          if (d.denominatorShort == '1000 patients') {
            // Treat measures which are per 1000 patients a bit differently.
            // See https://github.com/ebmdatalab/openprescribing/issues/436.
            denom = humanize.numberFormat(1000 * this.point.denominator, 0);
            str += 'Registered Patients: ' + denom;
          } else {
            denom = humanize.numberFormat(this.point.denominator, 0);
            str += d.denominatorShort + ': ' + denom;
          }
          str += '<br/>';
          str += 'Measure: ' + humanize.numberFormat(this.point.y, 3);
          str += (isPercentageMeasure) ? '%' : '';
          if (this.point.percentile !== null) {
            str += ' (' + humanize.ordinal(percentile);
            str += ' percentile)';
          }
        } else {
          str += 'Measure: ' + humanize.numberFormat(this.point.y, 3);
          str += (isPercentageMeasure) ? '%' : '';
        }
        return str;
      },
    };
    return chOptions;
  },

  startDataDownload: function(allChartData, chartId) {
    var chartData = this.getChartDataById(allChartData, chartId);
    var dataTable = this.getChartDataAsTable(chartData);
    var csvData = csvUtils.formatTableAsCSV(dataTable);
    var filename = csvUtils.getFilename(chartData.chartTitle);
    downloadjs(csvData, filename, 'text/csv');
  },

  getChartDataById: function(allChartData, chartId) {
    for (var i = 0; i<allChartData.length; i++) {
      if (allChartData[i].chartId === chartId) {
        return allChartData[i];
      }
    }
    throw 'No matching chartId: ' + chartId;
  },

  getChartDataAsTable: function(chartData) {
    var headers = [
      'date', 'org_id', 'org_name', 'numerator', 'denominator',
      'ratio', 'percentile'];
    var keyPercentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90];
    headers = headers.concat(keyPercentiles.map(function(n) { return n + 'th percentile'; }));
    var percentilesByDate = this.groupPercentilesByDate(chartData.globalCentiles, keyPercentiles);
    var orgIDColumn;
    var orgNameColumn;

    if (chartData.orgType == 'ccg') {
      orgIDColumn = 'pct_id';
      orgNameColumn = 'pct_name';
    } else {
      orgIDColumn = chartData.orgType + '_id';
      orgNameColumn = chartData.orgType + '_name';
    }

    var table = chartData.data.map(function(d) {
      return [
          d.date, d[orgIDColumn], d[orgNameColumn], d.numerator, d.denominator,
          d.calc_value, d.percentile
        ]
        .concat(percentilesByDate[d.date]);
    });
    table.unshift(headers);
    return table;
  },

  groupPercentilesByDate: function(globalCentiles, keyPercentiles) {
    var percentilesByDate = {};
    _.each(keyPercentiles, function(percentile) {
      _.each(globalCentiles[percentile], function(percentileData) {
        var date = percentileData.date;
        if ( ! percentilesByDate[date]) {
          percentilesByDate[date] = [];
        }
        percentilesByDate[date].push(percentileData.y);
      });
    });
    return percentilesByDate;
  }

};

module.exports = utils;
