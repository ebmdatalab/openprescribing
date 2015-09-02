global.jQuery = require('jquery');
global.$ = global.jQuery;
require('Highcharts');
var csv = require('csv');
var _ = require('underscore');

var chartOptions = require('./src/highcharts-options');

var barChart = {

    initialiseData: function(data) {
        _.each(data, function(d) {
            var dates = d.date.split('-');
            var date = Date.UTC(dates[0], dates[1]-1, dates[2]);
            d.x = date;
            d.actual_cost = parseFloat(d.actual_cost);
            d.items = parseFloat(d.items);
        });
        return data;
    },

    getYValueOfData: function(data, graphType) {
        _.each(data, function(d) {
            d.y = d[graphType];
        });
        return data;
    },

    getChartTitle: function(graphType) {
        var title = 'Total ';
        title += (graphType === 'actual_cost') ? 'spending' : 'items';
        if ((pageType !== 'ccg') && (pageType !== 'practice')) {
            title += ' across all practices in England';
        }
        return title;
    },

    getYAxisTitle: function(graphType) {
        var title = (graphType === 'actual_cost') ? 'Spending': 'Items';
        return title;
    },

    initialiseChartOptions: function(chartOptions, graphType) {
        var _this = this;
        var options = chartOptions.baseOptions;
        options.chart.marginTop = 40;
        options.chart.spacingTop = 20;
        options.chart.type = 'column';
        options.legend.enabled = false;
        options.yAxis.title = {
            text: _this.getYAxisTitle(graphType)
        };
        options.yAxis.labels = {
            formatter: function() {
                var str = (_this.graphType == 'actual_cost') ? '£' : '';
                return str + this.axis.defaultLabelFormatter.call(this);
            }
        };
        options.title.text = _this.getChartTitle(graphType);
        options.tooltip = {
            formatter: function() {
                var str = '<b>';
                str += (_this.graphType === 'actual_cost') ? '£' : '';
                str += Highcharts.numberFormat(this.y, 0);
                str += (_this.graphType === 'actual_cost') ? '' : ' items';
                str += '</b>';
                str += ' in ' + Highcharts.dateFormat('%b \'%y',
                                      new Date(this.x));
                return str;
            }
        };
        return options;
    },

    updateChart: function(data, graphType, chart) {
        var _this = this;
        _this.graphType = graphType;
        var newYAxisOptions = {
            title: {
                text: _this.getYAxisTitle(graphType)
            }
        };
        chart.yAxis[0].update(newYAxisOptions, false);
        var newData = _this.getYValueOfData(data, graphType);
        chart.series[0].setData(newData, false);
        chart.setTitle({ text: _this.getChartTitle(graphType)}, false);
        chart.redraw();
    },

    setUp: function() {
        var _this = this;
        _this.graphType = 'items';
        $.ajax({
          type: "GET",
          url: filename,
          error: function() {
            $('.status').html('<p>Sorry, something went wrong.</p>');
          },
          success: function(response) {
            $('.status').hide();
            console.log('response', response);
            var output = (response) ? $.csv.toObjects(response): [];
            chartOptions = _this.initialiseChartOptions(chartOptions, _this.graphType);
            var data = _this.initialiseData(output);
            data = _this.getYValueOfData(data, _this.graphType);
            if (data.length) {
                $('#trends').show();
                chartOptions.series = [{
                    'name': _this.graphType,
                    'data': data
                }];
                var chart = new Highcharts.Chart(chartOptions);
                // Bind events.
                $('#graphtype .btn').on('click', function(e) {
                    e.preventDefault();
                    $('#graphtype .btn').removeClass('btn-info').addClass('btn-default');
                    $(this).addClass('btn-info').removeClass('btn-default');
                    _this.graphType = $(this).data('type');
                    _this.updateChart(data, _this.graphType, chart);
                });
            } else {
                $('#trends, #download-data').hide();
                $('#no-data').show();
            }
          }
        });
    }
};

barChart.setUp();
