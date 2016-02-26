(function() {

global.jQuery = require('jquery');
global.$ = global.jQuery;
require('bootstrap');
require('Highcharts');
require('mapbox.js');
var _ = require('underscore');
var Handlebars = require('handlebars');

var utils = require('./src/chart_utils');
var formatters = require('./src/chart_formatters');
var chartOptions = require('./src/highcharts-options');

Highcharts.setOptions({
    global: { useUTC: false }
});

// TODO: Write tests for data functions.
var measures = {

    setUp: function() {
        var _this = this;
        _this.measure = measureData.measure;
        _this.orgId = measureData.orgId;
        _this.orgName = measureData.orgName;
        _this.orgType = measureData.orgType;
        _this.numerator = measureData.numerator;
        _this.denominator = measureData.denominator;

        var panel_template = Handlebars.compile($("#measure-panel").html());
        var practiceMeasuresUrl = '/api/1.0/measure_by_practice/?org=';
        practiceMeasuresUrl += _this.orgId + '&measure=';
        practiceMeasuresUrl += _this.measure + '&format=json';
        var globalMeasuresUrl = '/api/1.0/measure/?measure=' + _this.measure;
        globalMeasuresUrl += '&format=json';

        $.when(
            $.ajax(practiceMeasuresUrl),
            $.ajax(globalMeasuresUrl)
            ).done(function(practiceMeasures, globalMeasures) {

                var globalMedian = _this.convertData(globalMeasures[0].data,
                                                    'practice_50th'),
                    global10th = _this.convertData(globalMeasures[0].data,
                                                   'practice_10th'),
                    global90th = _this.convertData(globalMeasures[0].data,
                                                  'practice_90th');

                _this.globalMax = _.max(global90th, function(d) { return d.y; });
                var sortedData = _this.reshapeData(practiceMeasures[0].data);

                // Generate the panel for each practice, then draw the graph.
                var html = '';
                _.each(sortedData, function(d) {
                    html += panel_template(d);
                });
                $('#charts').html(html);
                _.each(sortedData, function(d) {
                    d.data = _this.convertData(d.data, 'calc_value');
                    _this.renderGraph(d, globalMedian, global10th, global90th);
                });
            })
            .fail(function(){
                console.log('failed');
            });
    },

    renderGraph: function(d, globalMedian, global10th, global90th) {
        // Create the series for an individual panel, and render chart.
        var _this = this;
        if (d.data.length) {
            var hcOptions = _this.getChartOptions(d);
            hcOptions.series = [{
                'name': 'This practice',
                'data': d.data,
                'color': 'red',
                marker: {
                   radius: 2
                }
            },
            {
                'name': '50th percentile nationally',
                'data': globalMedian,
                'dashStyle': 'longdash',
                'color': 'blue',
                'lineWidth': 2,
                marker: {
                   enabled: false
                }
            },
            {
                'name': '10th percentile nationally',
                'data': global10th,
                'dashStyle': 'dot',
                'color': 'blue',
                'lineWidth': 2,
                marker: {
                   enabled: false
                }
            },
            {
                'name': '90th percentile nationally',
                'data': global90th,
                'dashStyle': 'dot',
                'color': 'blue',
                'lineWidth': 2,
                marker: {
                   enabled: false
                }
            }];
            var chart = new Highcharts.Chart(hcOptions);
        } else {
            $('#' + chartOptions.chartId).find(_this.el.status).html('No data found for this ' + _this.orgType).show();
        }
    },

    parseDate: function(d) {
        var dates = d.split('-');
        return Date.UTC(dates[0], dates[1]-1, dates[2]);
    },

    convertData: function(data, attr) {
        var _this = this;
        var dataCopy = JSON.parse(JSON.stringify(data));
        _.each(dataCopy, function(d) {
            d.x = _this.parseDate(d.date);
            d.y = (d[attr] !== null) ? parseFloat(d[attr]) : null;
        });
        return dataCopy;
    },

    reshapeData: function(data) {
        // Get the average weighting across the latest three months.
        var lastThreeMonths = _.uniq(_.pluck(data, 'date'), true).slice(-3);
        var dataByPractice = {};
        _.each(data, function(d) {
            if (d.practice_id in dataByPractice) {
                dataByPractice[d.practice_id].data.push(d);
            } else {
                dataByPractice[d.practice_id] = {
                    data: [d],
                    name: d.name,
                    rank: 0
                };
            }
            if (_.contains(lastThreeMonths, d.date)) {
                dataByPractice[d.practice_id].rank += (d.numerator * d.percentile);
            }
        });
        // Return an array sorted by average weighting.
        var temp = [];
        for (var k in dataByPractice) {
            temp.push({
                'practice_id': k,
                'practice_name': dataByPractice[k].name,
                'rank': dataByPractice[k].rank,
                'data': dataByPractice[k].data
            });
        }
        return _.sortBy(temp, 'rank').reverse();
    },

    getChartOptions: function(d) {
        var _this = this;
        var options = $.extend(true, {}, chartOptions.dashOptions);
        options.chart.renderTo = d.practice_id;
        options.chart.height = 200;
        options.legend.enabled = false;
        var localMax = _.max(d.data, function(d) { return d.y; });
        var max = _.max([localMax.y, _this.globalMax.y]);
        options.yAxis = {
            title: {
                text: '%'
            },
            max: max,
            min: 0
        };
        options.tooltip = {
            formatter: function() {
                // console.log('this', this);
                var str = '<b>' + this.series.name;
                str += ' in ' + Highcharts.dateFormat('%b \'%y',
                                      new Date(this.x));
                str += '</b><br/>';
                str += _this.numerator + ': ';
                str += Highcharts.numberFormat(this.point.numerator, 0);
                str += '<br/>';
                str += _this.denominator + ': ';
                str += Highcharts.numberFormat(this.point.denominator, 0);
                str += '<br/>';
                str += 'Measure: ';
                str += Highcharts.numberFormat(this.point.y, 3) + '%';
                return str;
            }
        };
        return options;
    }
};

measures.setUp();
})();
