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

L.mapbox.accessToken = 'pk.eyJ1IjoiYW5uYXBvd2VsbHNtaXRoIiwiYSI6ImNzY1VpYkkifQ.LC_IcHpHfOvWOQCuo5t7Hw';

// TODO: Write tests for data functions.
var measures = {
    el: {
        mapPanel: 'map-ccg'
    },

    setUp: function() {
        var _this = this;
        _this.measure = measureData.measure;
        _this.rollUpBy = (_this.measure) ? 'practice_id': 'measure_id';
        _this.orgId = measureData.orgId;
        _this.orgName = measureData.orgName;
        _this.orgType = measureData.orgType;

        if (_this.orgType === 'practice') {
            _this.setUpMap(_this.orgId, _this.orgType);
        }

        var panel_template = Handlebars.compile($("#measure-panel").html());
        var urls = _this.getDataUrls(_this.orgId, _this.measure);

        $.when(
            $.ajax(urls.practiceMeasuresUrl),
            $.ajax(urls.globalMeasuresUrl)
            ).done(function(practiceMeasures, globalMeasures) {
                var pageData = practiceMeasures[0].measures,
                    globalData = globalMeasures[0].measures,
                    globalMedian = [], global10th = [], global90th = [];

                // Get global percentiles and y-max, if this is an org-based page
                // so there's only one measure to worry about, and all the charts
                // should have the same max and global series.
                if (_this.rollUpBy === 'practice_id') {
                    // We're only using one measure. Get the
                    var globalSeries = _.findWhere(globalData, { id: _this.measure});
                    globalMedian = _this.convertData(globalSeries.data,
                                                    'practice_50th');
                    global10th = _this.convertData(globalSeries.data,
                                                   'practice_10th');
                    global90th = _this.convertData(globalSeries.data,
                                                  'practice_90th');
                    _this.globalYMax = _.max(global90th, _.property('y'));
                } else {
                    _this.globalYMax = 0;
                }

                // TODO: get global x-min and x-max to ensure consistent.
                _this.globalXMin = 0;
                _this.globalXMax = 0;

                // Create an array with an item for each chart, ordered by the
                // metric that we care about.
                if (_this.rollUpBy !== 'measure_id') {
                    pageData = _this.rollUpByOrg(pageData[0]);
                }
                pageData = _this.getSavingAndPercentilePerItem(pageData, _this.rollUpBy);
                var orderedData = _.sortBy(pageData, 'mean_percentile').reverse();
                // console.log('orderedData', orderedData);

                // Draw the chart for each item (measure or practice).
                var html = '';
                orderedData = _this.addChartAttributes(orderedData, _this.rollUpBy);
                _.each(orderedData, function(d) {
                    html += panel_template(d);
                });
                $('#charts').html(html);
                _.each(orderedData, function(d) {
                    d.data = _this.convertData(d.data, 'calc_value');
                    if (_this.rollUpBy === 'measure_id') {
                        var globalSeries = _.findWhere(globalData, { id: d.id});
                        d.median = _this.convertData(globalSeries.data, 'practice_50th');
                        d.percentile10th =_this.convertData(globalSeries.data, 'practice_10th');
                        d.percentile90th =_this.convertData(globalSeries.data, 'practice_90th');
                    } else {
                        d.median = globalMedian;
                        d.percentile10th = global10th;
                        d.percentile90th = global90th;
                    }
                    _this.renderGraph(d);
                });

                // Set up 'sort by' options.
                var chartByPercentile = $('#charts .chart');
                var chartsBySaving = $(chartByPercentile).filter(function(a) {
                    return $(this).data('costsaving') !== 0;
                });
                chartsBySaving.sort(function(a, b) {
                    return +a.costsaving - +b.costsaving;
                    // TODO: Fix for <IE10.
                    //return +a.getAttribute('data-costsaving') - +b.getAttribute('data-costsaving');
                });
                $(".btn-group > .btn").click(function(){
                    $(this).addClass("active").siblings().removeClass("active");
                    var orderType =  $(this).data('orderby');
                    if (orderType === 'savings') {
                        $('#charts').fadeOut().html(chartsBySaving).fadeIn();
                    } else {
                        $('#charts').fadeOut().html(chartByPercentile).fadeIn();
                    }
                });

            })
            .fail(function(){
                console.log('failed');
            });
    },

    getDataUrls: function(orgId, measure) {
        var urls = {
            practiceMeasuresUrl: '/api/1.0/measure_by_practice/?org=',
            globalMeasuresUrl: '/api/1.0/measure/?format=json'
        };
        urls.practiceMeasuresUrl += orgId + '&format=json';
        if (measure) {
            urls.practiceMeasuresUrl += '&measure=' + measure;
        }
        if (measure) {
            urls.globalMeasuresUrl += '&measure=' + measure;
        }
        return urls;
    },

    renderGraph: function(d) {
        var _this = this;
        if (d.data.length) {
            var hcOptions = _this.getChartOptions(d);
            hcOptions.series = [{
                'name': 'This practice',
                'is_national_series': false,
                'data': d.data,
                'color': 'red',
                'marker': {
                   'radius': 2
                }
            },
            {
                'name': '50th percentile nationally',
                'is_national_series': true,
                'data': d.median,
                'dashStyle': 'longdash',
                'color': 'blue',
                'lineWidth': 2,
                'marker': {
                   'enabled': false
                }
            },
            {
                'name': '10th percentile nationally',
                'is_national_series': true,
                'data': d.percentile10th,
                'dashStyle': 'dot',
                'color': 'blue',
                'lineWidth': 2,
                'marker': {
                   'enabled': false
                }
            },
            {
                'name': '90th percentile nationally',
                'is_national_series': true,
                'data': d.percentile90th,
                'dashStyle': 'dot',
                'color': 'blue',
                'lineWidth': 2,
                'marker': {
                   'enabled': false
                }
            }
            ];
            var chart = new Highcharts.Chart(hcOptions);
        } else {
            $('#' + chartOptions.chartId).find(_this.el.status).html('No data found for this ' + _this.orgType).show();
        }
    },

    _parseDate: function(d) {
        var dates = d.split('-');
        return Date.UTC(dates[0], dates[1]-1, dates[2]);
    },

    convertData: function(data, attr) {
        var _this = this,
            dataCopy = JSON.parse(JSON.stringify(data));
        _.each(dataCopy, function(d, i) {
            d.x = _this._parseDate(d.date);
            d.y = (d[attr] !== null) ? parseFloat(d[attr]) : null;
        });
        return dataCopy;
    },

    rollUpByOrg: function(data) {
        var rolled = {};
        _.each(data.data, function(d) {
            var id = d.practice_id;
            if (id in rolled) {
                rolled[id].data.push(d);
            } else {
                rolled[id] = {
                    'id': id,
                    'name': d.practice_name,
                    'numerator_short': data.numerator_short,
                    'denominator_short': data.denominator_short,
                    'data': [d],
                    'description': ''
                };
            }
        });
        var rolledArr = [];
        for (var practice_id in rolled) {
            rolledArr.push(rolled[practice_id]);
        }
        return rolledArr;
    },

    getSavingAndPercentilePerItem: function(data, rollUpBy) {
        // For each measure, or org, in the data, get the mean percentile,
        // and the mean cost saving. We'll use these to offer sorting
        // options in the front-end.
        _.each(data, function(d) {
            var latestData = d.data.slice(-6);
            var sum = _.reduce(latestData, function(memo, num){
                return memo + num.percentile;
            }, 0);
            d.mean_percentile = sum / latestData.length;
            d.cost_saving = _.reduce(latestData, function(memo, num){
                return memo + num.cost_saving_50th;
            }, 0);
            // Hack, just for demo purposes.
            if (d.id === 'rosuvastatin') {
                d.cost_saving = 50;
            } else if (d.id === 'cerazette') {
                d.cost_saving = 100;
            } else {
                d.cost_saving = 0;
            }
        });
        return data;

        // TODO: Use same months across all items?
        // var lastThreeMonths = _.uniq(_.pluck(data, 'date'), true).slice(-3);
        // if (_.contains(lastThreeMonths, d.date)) {
        //     if (rollUpBy === 'measure_id') {
        //         rolledData[d[rollUpBy]].rank += d.percentile;
        //     } else {
        //         rolledData[d[rollUpBy]].rank += (d.numerator * d.percentile);
        //     }
        // }
    },

    addChartAttributes: function(data, rollUpBy) {
        _.each(data, function(d) {
            d.chart_id = d.id;
            if (rollUpBy === 'measure_id') {
                d.chart_title = d.name;
                d.chart_title_url = '/measure/' + d.id;
            } else {
                d.chart_title = d.id + ': ' + d.name;
                d.chart_title_url = '/practice/' + d.id;
            }
            d.description_short = d.description.substring(0, 80) + ' ...';
        });
        return data;
    },

    getChartOptions: function(d) {
        var _this = this,
            options = $.extend(true, {}, chartOptions.dashOptions);
        options.chart.renderTo = d.chart_id;
        options.chart.height = 200;
        options.legend.enabled = false;
        var localMax = _.max(d.data, _.property('y'));
        var ymax;
        if (_this.rollUpBy === 'practice_id') {
            ymax = _.max([localMax.y, _this.globalYMax.y]);
        } else {
            var local90thMax = _.max(d.percentile90th, _.property('y'));
            ymax = _.max([localMax.y, local90thMax.y]);
        }
        options.yAxis = {
            title: {
                text: '%'
            },
            max: ymax,
            min: 0
        };
        options.tooltip = {
            formatter: function() {
                var num = Highcharts.numberFormat(this.point.numerator, 0),
                    denom = Highcharts.numberFormat(this.point.denominator, 0),
                    str = '';
                str += '<b>' + this.series.name;
                str += ' in ' + Highcharts.dateFormat('%b \'%y',
                                      new Date(this.x));
                str += '</b><br/>';
                if (!this.series.options.is_national_series) {
                    str += d.numerator_short + ': ' + num;
                    str += '<br/>';
                    str += d.denominator_short + ': ' + denom;
                    str += '<br/>';
                }
                str += 'Measure: ' +  Highcharts.numberFormat(this.point.y, 3) + '%';
                if (!this.series.options.is_national_series) {
                    str += ' (' + num + '/' + denom + ')';
                }
                return str;
            }
        };
        return options;
    },

    setUpMap: function(orgId, orgType) {
        var _this = this;
        var map = L.mapbox.map(_this.el.mapPanel, 'mapbox.streets').setView([52.905, -1.79], 6);
        map.scrollWheelZoom.disable();
        var url = '/api/1.0/org_location/?org_type=' + orgType.toLowerCase();
        url += '&q=' + orgId;
        var layer = L.mapbox.featureLayer()
            .loadURL(url)
            .on('ready', function() {
                if (layer.getBounds().isValid()) {
                    map.fitBounds(layer.getBounds(), {maxZoom: 12});
                    layer.setStyle({fillColor: '#ff00ff',
                                    fillOpacity: 0.2,
                                    weight: 0.5,
                                    color: "#333",
                                    radius: 10});
                } else {
                    $('#map-container').html('');
                }
            })
            .addTo(map);
    }
};

measures.setUp();
})();
