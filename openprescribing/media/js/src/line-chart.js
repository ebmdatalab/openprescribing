var utils = require('./chart_utils');
var formatters = require('./chart_formatters');
var _ = require('underscore');

var lineChart = {
    setUp: function(lineOptions, globalOptions) {
        lineOptions.title.text = globalOptions.friendly.chartTitle;
        lineOptions.yAxis.title = {
            text: globalOptions.friendly.yAxisTitle
        };
        if (lineOptions.yAxis.title.text.indexOf("<br/>") > -1) {
            lineOptions.yAxis.title.margin = 35;
        }
        lineOptions.tooltip = {
            formatter: function() {
                var series_name = this.series.name;
                var month = this.x;
                var original_x = this.point.original_x;
                var original_y = this.point.original_y;
                var y = this.y;
                // Set force_items=true here, because this chart
                // only ever shows items, not spending.
                // Dynamic updates to the chart are too slow.
                return formatters.constructTooltip(globalOptions, series_name,
                    month, original_y, original_x, y, true);
            }
        };
        lineOptions.series = this.getDataForLineChart(globalOptions.data.combinedData,
                                            globalOptions.chartValues,
                                            _.pluck(globalOptions.orgIds, 'id'));
        return new Highcharts.Chart(lineOptions);
    },

    getDataForLineChart: function(combinedData, chartValues, activeOrgs) {
        // We want each org to be a series, with an id, name and data[] property.
        // We want each point in the data array to have an x (date) and y (number) property.
        // The y property should be the ratio that we care about.
        // console.log('getDataForLineChart', combinedData, chartValues, activeOrgs);
        var dataForOrganisation = {}, allIds = [], series = [], hasActiveOrg;
        combinedData.forEach(function(d) {
            if (!(d.id in dataForOrganisation)) {
                dataForOrganisation[d.id] = {
                    id: d.id,
                    name: d.name,
                    data: []
                };
            }
            var dataPoint = {};
            var dates = d.date.split('-');
            var date = Date.UTC(dates[0], dates[1]-1, dates[2]);
            dataPoint.original_y = d[chartValues.y];
            dataPoint.original_x = d[chartValues.x_val];
            dataPoint.x = date;
            dataPoint.y = d[chartValues.ratio];
            dataForOrganisation[d.id].data.push(dataPoint);
            allIds.push(d.id);
        });
        hasActiveOrg = (_.intersection(allIds, activeOrgs).length !== 0);
        for (var k in dataForOrganisation) {
            var s = dataForOrganisation[k];
            if (hasActiveOrg) {
                if (_.contains(activeOrgs, s.id)) {
                    s.color = 'rgba(255, 64, 129, 0.6)';
                    s.zIndex = 1000;
                } else {
                    s.color = 'rgba(204, 204, 204, 0.6)';
                    s.zIndex = 1;
                }
            }
            series.push(s);
        }
        return series;
    }
};

module.exports = lineChart;
