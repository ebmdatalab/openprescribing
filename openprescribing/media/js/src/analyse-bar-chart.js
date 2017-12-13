var _ = require('underscore');
var $ = require('jquery');

var utils = require('./chart_utils');
var formatters = require('./chart_formatters');

var barChart = {

  setUp: function(barOptions, globalOptions) {
        // console.log('setUpBarChart');
    barOptions.yAxis.title = {
      text: globalOptions.friendly.yAxisTitle,
    };
    if (barOptions.yAxis.title.text.indexOf('<br/>') > -1) {
      barOptions.yAxis.title.margin = 35;
    }
    barOptions.yAxis.labels = {
      formatter: globalOptions.friendly.yAxisFormatter,
    };
    var xAxisTitle = (globalOptions.org == 'practice') ? 'Practice' : 'CCG';
    barOptions.xAxis.title = {text: xAxisTitle};
    var chartValues = globalOptions.chartValues;
    barOptions.tooltip = {
      formatter: function() {
        var chartValues = globalOptions.chartValues;
        var name = this.point.name + ' (' + this.point.id + ')';
        var month = this.point.date;
        var original_x = this.point.options[chartValues.x_val];
        var original_y = this.point.options[chartValues.y];
        var y = this.y;
        return formatters.constructTooltip(globalOptions, name,
                    month, original_y, original_x, y);
      },
    };
    var activeOrgs = _.pluck(globalOptions.orgIds, 'id');
    var convertedData = this._indexDataByMonthAndRatio(
      globalOptions.data.combinedData, activeOrgs);
    this.barData = convertedData.barData;
    globalOptions.maxRatioActualCost = convertedData.maxRatioActualCost;
    globalOptions.maxRatioItems = convertedData.maxRatioItems;
    // Ensure we always show ticks for any active (selected) orgs:
    barOptions.xAxis.tickPositioner = function() {
      var calculated = this.tickPositions;
      var activeOrgsIndex = [];
      _.each(this.series[0].options.data, function(d, i) {
        if (d.active) {
          activeOrgsIndex.push(i);
        }
      });
      _.each(activeOrgsIndex, function(d) {
        var j = _.sortedIndex(calculated, d);
        calculated.splice(j, 0, d);
      });
      return calculated;
    };
    var activeMonth = globalOptions.activeMonth;
    var ratio = globalOptions.chartValues.ratio;
    var dataForMonth = this.barData[activeMonth][ratio];
    // Fix the y Axis
    if (ratio === 'ratio_actual_cost') {
      barOptions.yAxis.max = globalOptions.maxRatioActualCost;
    } else {
      barOptions.yAxis.max = globalOptions.maxRatioItems;
    }
    barOptions.series = utils.createChartSeries(dataForMonth);
    return new Highcharts.Chart(barOptions);
  },

  update: function(chart, month, ratio, title, formatter, playing, yAxisMax) {
    var newYAxisOptions = {
      title: {
        text: title,
      },
      labels: {
        formatter: formatter,
      },
    };
    if (playing) {
      chart.animation = false;
    }
    chart.yAxis[0].update(newYAxisOptions, false);
    if (month in this.barData) {
      chart.series[0].setData(this.barData[month][ratio], false);
    } else {
      chart.series[0].setData([], false);
    }
    chart.yAxis[0].setExtremes(null, yAxisMax);
    try {
      chart.redraw();
    } catch (err) {
      chart.series[0].setData(this.barData[month][ratio], true);
    }
  },

  _indexDataByMonthAndRatio: function(combinedData, activeOrgs) {
    var newData = {};
    _.each(combinedData, function(d) {
      d.name = d.row_name;
      if (_.contains(activeOrgs, d.id)) {
        d.color = 'rgba(255, 64, 129, .8)';
        d.active = true;
      } else {
        d.color = 'rgba(119, 152, 191, .5)';
        d.active = false;
      }
      var copy1 = $.extend(true, {}, d);
      var copy2 = $.extend(true, {}, d);
      if (d.date in newData) {
        newData[d.date].ratio_items.push(copy1);
        newData[d.date].ratio_actual_cost.push(copy2);
      } else {
        newData[d.date] = {
          ratio_items: [copy1],
          ratio_actual_cost: [copy2],
        };
      }
    });
    var maxRatioItems = 0;
    var maxRatioActualCost = 0;
    for (var month in newData) {
      _.each(newData[month].ratio_items, function(d) {
        d.y = d.ratio_items;
        if (d.y > maxRatioItems) {
          maxRatioItems = d.y;
        }
      });
      _.each(newData[month].ratio_actual_cost, function(d) {
        d.y = d.ratio_actual_cost;
        if (d.y > maxRatioActualCost) {
          maxRatioActualCost = d.y;
        }
      });
      newData[month].ratio_items = _.sortBy(newData[month].ratio_items, 'y');
      newData[month].ratio_actual_cost = _.sortBy(newData[month].ratio_actual_cost, 'y');
    }
    return {
      barData: newData,
      maxRatioItems: maxRatioItems,
      maxRatioActualCost: maxRatioActualCost};
  },
};

module.exports = barChart;
