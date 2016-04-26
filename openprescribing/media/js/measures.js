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

var measures = {
    el: {
        mapPanel: 'map-ccg'
    },

    setUp: function() {
        var _this = this;

        // The number of months to look at when calculating ranks.
        _this.NUM_MONTHS = 6;
        _this.centiles = ['10', '20', '30', '40', '50', '60', '70', '80', '90'];

        // This may be the measure name, or undefined.
        _this.measure = measureData.measure;
        _this.measure_is_cost_based = (measureData.measure_is_cost_based) ? (measureData.measure_is_cost_based === 'True') : null;
        _this.orgType = measureData.orgType;
        _this.orgId = measureData.orgId;
        _this.orgName = measureData.orgName;
        _this.rollUpBy = (_this.measure) ? 'org_id': 'measure_id';

        // Show a map, if required.
        if ($('#' + _this.el.mapPanel).length) {
            _this.setUpMap(_this.orgId, _this.orgType);
        }

        // All pages have a summary, and a series of panels.
        var summary_template = Handlebars.compile($('#summary-panel').html()),
            panel_template = Handlebars.compile($("#measure-panel").html());

        // Get the appropriate URLs for the individual panel measures, and the global measures.
        var urls = _this.getDataUrls(_this.orgId, _this.orgType, _this.measure);
        $.when(
            $.ajax(urls.panelMeasuresUrl),
            $.ajax(urls.globalMeasuresUrl)
            ).done(function(panelMeasures, globalMeasures) {
                var panelData = panelMeasures[0].measures,
                    globalData = globalMeasures[0].measures,
                    globalSeries = {};

                // If we're just looking at one measure, calculate the Highcharts x and
                // y values at this point, so we can re-use them.
                if (_this.rollUpBy === 'org_id') {
                    // We're only using one measure. Get the global series.
                    var series = _.findWhere(globalData, { id: _this.measure});
                    _.each(_this.centiles, function(i) {
                        globalSeries[i.toString()] = _this.convertDataForHighcharts(series.data,
                            true, _this.orgType.toLowerCase(), i);
                    });
                    _this.globalYMax = _.max(globalSeries['90'], _.property('y'));
                } else {
                    _this.globalYMax = 0;
                }

                panelData = _this.annotateAndSortPanelData(panelData);

                // Render performance summary measures.
                var perf = _this.getPerformanceSummary(panelData, _this.rollUpBy,
                    _this.measure_is_cost_based, _this.orgId, _this.measure);
                $('#summary').html(summary_template(perf));

                // Draw the panel for each item (whether measure or org).
                var html = '';
                var chartData = _this.addChartAttributes(panelData, _this.rollUpBy, _this.orgType);
                _.each(chartData, function(d) {
                    html += panel_template(d);
                });
                $('#charts').html(html);

                // Render the chart to each panel.
                _.each(chartData, function(d) {
                    d.data = _this.convertDataForHighcharts(d.data, false);
                    if (_this.rollUpBy === 'measure_id') {
                        // For measures, get the global series for each measure.
                        var series = _.findWhere(globalData, { id: d.id});
                        d.globalSeries = {};
                        _.each(_this.centiles, function(i) {
                            d.globalSeries[i] = _this.convertDataForHighcharts(series.data, true,
                                _this.orgType.toLowerCase(), i);
                        });
                    } else {
                        d.globalSeries = globalSeries;
                    }
                    _this.renderGraph(d, _this.orgType);
                });

                // Set up 'sort by' options, for per-measure pages.
                if (_this.rollUpBy === 'measure_id') {
                    var chartsByPercentile = $('#charts .chart');
                    var chartsBySaving = $(chartsByPercentile).filter(function(a) {
                        return $(this).data('costsaving') !== 0;
                    });
                    chartsBySaving.sort(function(a, b) {
                        return +a.costsaving - +b.costsaving;
                        // TODO: Fix for <IE10?
                        //return +a.getAttribute('data-costsaving') - +b.getAttribute('data-costsaving');
                    });
                    $(".btn-group > .btn").click(function(){
                        $(this).addClass("active").siblings().removeClass("active");
                        if ($(this).data('orderby') === 'savings') {
                            $('#charts').fadeOut(function(){
                                $('#charts').html(chartsBySaving).fadeIn();
                            });
                        } else {
                            $('#charts').fadeOut(function(){
                                $('#charts').html(chartsByPercentile).fadeIn();
                            });
                        }
                    });
                }
            })
            .fail(function(){
                console.log('data failed');
            });
    },

    getDataUrls: function(orgId, orgType, measure) {
        var urls = {
            panelMeasuresUrl: '/api/1.0/measure_by_' + orgType.toLowerCase() + '/?format=json',
            globalMeasuresUrl: '/api/1.0/measure/?format=json'
        };
        if (orgId) {
            urls.panelMeasuresUrl += '&org=' + orgId;
        }
        if (measure) {
            urls.panelMeasuresUrl += '&measure=' + measure;
            urls.globalMeasuresUrl += '&measure=' + measure;
        }
        return urls;
    },

    renderGraph: function(d, orgType) {
        // console.log('renderGraph', d.globalSeries);
        var _this = this;
        if (d.data.length) {
            var hcOptions = _this.getChartOptions(d);
            hcOptions.series = [{
                'name': 'This ' + orgType,
                'is_national_series': false,
                'data': d.data,
                'color': 'red',
                'marker': {
                   'radius': 2
                }
            }];
            for (var k in d.globalSeries) {
                var e = {
                    'name': k + 'th percentile nationally',
                    'is_national_series': true,
                    'data': d.globalSeries[k],
                    'dashStyle': 'dot',
                    'color': 'blue',
                    'lineWidth': 1,
                    'marker': {
                       'enabled': false
                    }
                };
                // if (k === '50') {
                //     e.dashStyle = 'longdash';
                // }
                hcOptions.series.push(e);
            }
            var chart = new Highcharts.Chart(hcOptions);
        } else {
            $('#' + chartOptions.chartId).find(_this.el.status).html('No data found for this ' + _this.orgType).show();
        }
    },

    annotateAndSortPanelData: function(panelData) {
        // Create an array with an item for each chart, rolled up either
        // by measure, OR by organisation ID, as appropriate.
        // Annotate each chart with the saving, and percentile.
        // Sort the array by percentile, put all nulls at the bottom.
        var data, _this = this;
        if (_this.rollUpBy !== 'measure_id') {
            panelData = _this.rollUpByOrg(panelData[0], _this.orgType);
        }
        panelData = _this.getSavingAndPercentilePerItem(panelData, _this.NUM_MONTHS);
        data = _.sortBy(panelData, function(d) {
            if (d.mean_percentile === null) return -1;
            return d.mean_percentile;
        }).reverse();
        return data;
    },

    _parseDate: function(d) {
        var dates = d.split('-');
        return Date.UTC(dates[0], dates[1]-1, dates[2]);
    },

    convertDataForHighcharts: function(data, is_global, org, num) {
        // Take a data series and an attribute, and convert it to
        // a series of x/y dictionaries, ready for Highcharts.
        var _this = this,
            dataCopy = JSON.parse(JSON.stringify(data));
        _.each(dataCopy, function(d, i) {
            d.x = _this._parseDate(d.date);
            p = d.percentiles;
            if (is_global) {
                d.y = (p && p[org] && p[org][num] !== null) ? parseFloat(p[org][num]) : null;
            } else {
                d.y = (d.calc_value !== null) ? parseFloat(d.calc_value) : null;
            }
            // TODO: Only multiply values for percentage-based measures.
            d.y = (d.y) ? d.y * 100 : d.y;
        });
        return dataCopy;
    },

    rollUpByOrg: function(data, orgType) {
        var rolled = {};
        _.each(data.data, function(d) {
            var id = (orgType === 'practice') ? d.practice_id : d.pct_id,
                name = (orgType === 'practice') ? d.practice_name : d.pct_name;
            if (id in rolled) {
                rolled[id].data.push(d);
            } else {
                rolled[id] = {
                    'id': id,
                    'name': name,
                    'numerator_short': data.numerator_short,
                    'denominator_short': data.denominator_short,
                    'data': [d],
                    'description': ''
                };
            }
        });
        var rolledArr = [];
        for (var org_id in rolled) {
            rolledArr.push(rolled[org_id]);
        }
        return rolledArr;
    },

    getSavingAndPercentilePerItem: function(data, num_months) {
        // For each measure, or org, in the data, get the mean percentile,
        // and the mean cost saving at the 50th percentile,
        // over the number of months specified.
        // We'll use this to sort the panels.
        // console.log('getSavingAndPercentilePerItem', data);
        _.each(data, function(d) {
            var latestData = d.data.slice(num_months * -1);
            var sum = _.reduce(latestData, function(memo, num){
                return (num.percentile === null) ? memo : memo + num.percentile;
            }, null);
            d.mean_percentile = (sum !== null) ? sum / latestData.length: null;
            d.cost_saving_50th = _.reduce(latestData, function(memo, num) {
                var saving = (num.cost_savings) ? num.cost_savings['50'] : null;
                return memo + saving;
            }, null);
        });
        return data;
    },

    addChartAttributes: function(data, rollUpBy, orgType) {
        // Add the chart title, URL, description, etc.
        _.each(data, function(d) {
            // console.log('addChartAttributes', d);
            d.chart_id = d.id;
            if (rollUpBy === 'measure_id') {
                d.chart_title = d.name;
                d.chart_title_url = '/measure/' + d.id;
            } else {
                d.chart_title = d.id + ': ' + d.name;
                d.chart_title_url = '/' + orgType + '/' + d.id;
            }
            d.description_short = d.description.substring(0, 80) + ' ...';
            if (d.is_cost_based) {
                d.cost_description = '<strong>Cost savings</strong>: ';
                if (d.cost_saving_50th < 0) {
                    d.cost_description += 'By prescribing better than the median, ';
                    d.cost_description += 'this ' + orgType + ' has saved the NHS £';
                    d.cost_description += Highcharts.numberFormat((d.cost_saving_50th * -1), 2);
                    d.cost_description += ' over the past six months.';
                } else if (d.cost_saving_50th === 0) {
                } else {
                    d.cost_description += 'If it had prescribed in line with the median, ';
                    d.cost_description += 'this ' + orgType + ' would have spent £';
                    d.cost_description += Highcharts.numberFormat(d.cost_saving_50th, 2);
                    d.cost_description += ' less over the past six months.';
                }
            }
        });
        return data;
    },

    getChartOptions: function(d) {
        // Highcharts options for these panel charts.
        var _this = this,
            options = $.extend(true, {}, chartOptions.dashOptions);
        options.chart.renderTo = d.chart_id;
        options.chart.height = 200;
        options.legend.enabled = false;
        var localMax = _.max(d.data, _.property('y'));
        var ymax;
        if (_this.rollUpBy === 'org_id') {
            ymax = _.max([localMax.y, _this.globalYMax.y]);
        } else {
            var local90thMax = _.max(d.globalSeries['90'], _.property('y'));
            ymax = _.max([localMax.y, local90thMax.y]);
        }
        options.yAxis = {
            title: {
                text: '%' // d.numerator_short + ' / ' + d.denominator_short
            },
            max: ymax,
            min: 0 // use min, or hard-code zero if the local min is zero
        };
        options.tooltip = {
            formatter: function() {
                // console.log('tooltip', this.point);
                var num = Highcharts.numberFormat(this.point.numerator, 0),
                    denom = Highcharts.numberFormat(this.point.denominator, 0),
                    percentile = Highcharts.numberFormat(this.point.percentile, 0),
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
                    //str += ' (' + num + '/' + denom + ')';
                    str += ' (' + percentile + _this.getOrdinalSuffix(percentile) + ' percentile)';
                }
                return str;
            }
        };
        return options;
    },

    getOrdinalSuffix: function(percentile) {
        var lastChar = percentile.toString().slice(-1), suffix;
        switch (lastChar) {
            case '1':
                suffix = 'st';
                break;
            case '2':
                suffix = 'nd';
                break;
            case '3':
                suffix = 'rd';
                break;
            default:
                suffix = 'th';
        }
        return suffix;
    },

    getPerformanceSummary: function(orderedData, rollUpBy, isCostBased, orgId, measure) {
        // console.log('getPerformanceSummary', orderedData, rollUpBy);
        // Calculate % of measures above the median, and the total
        // possible savings at the median.
        var perf = {
            total: 0,
            above_median: 0,
            potential_savings_50th: 0,
            potential_savings_10th: 0,
            org_id: orgId,
            measure_id: measure
        };
        _.each(orderedData, function(d) {
            if (d.mean_percentile !== null) {
                perf.total += 1;
                if (d.mean_percentile > 50) {
                    perf.above_median += 1;
                    perf.potential_savings_50th += (isCostBased) ? d.cost_saving_50th : 0;
                }
                if (d.mean_percentile > 10) {
                    perf.potential_savings_10th += (isCostBased) ? d.cost_saving_10th : 0;
                }
            }
        });
        perf.proportion_above_median = perf.above_median / perf.total;
        if (perf.proportion_above_median > 0.75) {
            perf.performance_description = 'poor';
        } else if (perf.proportion_above_median > 0.5) {
            perf.performance_description = 'acceptable';
        } else if (perf.proportion_above_median > 0.25) {
            perf.performance_description = 'good';
        } else if (perf.proportion_above_median > 0) {
            perf.performance_description = 'very good';
        }
        if (perf.performance_description) {
            perf.performance_description = 'We think this is ' + perf.performance_description;
            perf.performance_description += ' performance overall.';
        }
        perf.proportion_above_median = Highcharts.numberFormat(perf.proportion_above_median * 100, 1);

        if (isCostBased) {
            if (rollUpBy === 'measure_id') {
                perf.cost_savings = 'Over the same period, if this practice had prescribed ';
                perf.cost_savings += 'at the median ratio or better on all cost-saving measures below, then it would ';
                perf.cost_savings += 'have spent £' + Highcharts.numberFormat(perf.potential_savings_50th, 2);
                perf.cost_savings += ' less. (We use the national median as a suggested ';
                perf.cost_savings += 'target because by definition, 50% of practices were already prescribing ';
                perf.cost_savings += 'at this level or better, so we think it ought to be achievable.)';
            } else {
                perf.cost_savings = 'Over the same period, if all practices had prescribed ';
                perf.cost_savings += 'at the median ratio or better, then this CCG would ';
                perf.cost_savings += 'have spent £' + Highcharts.numberFormat(perf.potential_savings_50th, 2);
                perf.cost_savings += ' less. (We use the national median as a suggested ';
                perf.cost_savings += 'target because by definition, 50% of practices were already prescribing ';
                perf.cost_savings += 'at this level or better, so we think it ought to be achievable.)';
            }
        }
        //console.log('perf', perf);
        return perf;
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
