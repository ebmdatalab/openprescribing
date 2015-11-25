(function() {

global.jQuery = require('jquery');
global.$ = global.jQuery;
require('bootstrap');
require('Highcharts');
require('mapbox.js');
var _ = require('underscore');

var utils = require('./src/chart_utils');
var formatters = require('./src/chart_formatters');
var chartOptions = require('./src/highcharts-options');

Highcharts.setOptions({
    global: { useUTC: false }
});

var barChart = {
    el: {
        noData: '',
        status: '.status',
        trendsPanel: '#trends'
    },
    errorMessage: '<p>Sorry, something went wrong.</p>',

    setUp: function() {

        this.setUpShowPractices();
        this.setUpMap();

        var _this = this;
        this.orgId = orgId;
        this.orgName = orgName;
        this.orgType = orgType;
        this.baseUrl = '/api/1.0/';
        this.spendUrl = this.baseUrl;
        this.spendUrl += (this.orgType === 'CCG') ? 'spending_by_ccg' : 'spending_by_practice';
        var graphList = [
            {
                chartId: 'rosuvastatin',
                numIds: [{ id: '0212000AA', 'name': 'Rosuvastatin'}],
                denomIds: [{ id: '0212000B0', 'name': 'Atorvastatin'}]
            },
            {
                chartId: 'antibiotics',
                numIds: [{ id: '0501', 'name': 'Antibacterial Drugs'}],
                denom: 'star_pu_oral_antibac_items',
                denomIds: []
            },
            {
                chartId: 'cephalosporins',
                numIds: [{ id: '050102', 'name': 'Cephalosporins and other Beta-Lactams'}],
                denom: 'star_pu_oral_antibac_items',
                denomIds: []
            },
            {
                chartId: 'cerazette',
                numIds: [{ id: '0703021Q0BB', 'name': 'Cerazette'}],
                denomIds: [{ id: '0703021Q0', 'name': 'Desogestrel'}]
            },
            {
                chartId: 'pioglitazone',
                numIds: [{ id: '0601023B0', 'name': 'Pioglitazone Hydrochloride'}],
                denomIds: [{ id: '060102', 'name': 'All diabetes'}]
            },
            {
                chartId: 'celecoxib',
                numIds: [{ id: '0801050AY', 'name': 'Celecoxib'}, {id: '1001010AH', 'name': 'Celecoxib'}],
                denomIds: [{ id: '100101', 'name': 'Non-Steroidal Anti-Inflammatory Drugs'}]
            }
        ];
        _.each(graphList, function(d) {
            var chartOptions = {
                'activeOption': 'items',
                'org': _this.orgType,
                'orgIds': [{ 'id': _this.orgId, 'name': _this.orgName}],
                'num': 'chemical',
            };
            chartOptions.chartId = d.chartId;
            chartOptions.numIds = d.numIds;
            chartOptions.denom = d.denom || 'chemical';
            chartOptions.denomIds = d.denomIds;
            if (chartOptions.denom !== 'chemical') {
                chartOptions.chartValues = {
                    x_val: chartOptions.denom,
                    x: chartOptions.denom
                };
            } else {
                chartOptions.chartValues = {
                    x_val: 'x_items',
                    x: 'items'
                };
            }
            chartOptions.chartValues.y = 'y_items';
            chartOptions.chartValues.ratio = 'ratio_items';

            var numStr = utils.idsToString(chartOptions.numIds);
            chartOptions.numOrgUrl = _this.spendUrl + '/?format=json&org=' + _this.orgId;
            chartOptions.numOrgUrl += '&code=' + numStr;
            chartOptions.numAllNHS = _this.baseUrl + 'spending/?format=json&code=' + numStr;

            var denomStr = utils.idsToString(chartOptions.denomIds);
            if (chartOptions.denom === 'chemical') {
                chartOptions.denomOrgUrl = _this.spendUrl + '/?format=json&code=' + denomStr;
                chartOptions.denomAllNHS = _this.baseUrl + 'spending/?format=json&code=' + denomStr;
            } else {
                chartOptions.denomOrgUrl = _this.baseUrl + 'org_details/?format=json';
                chartOptions.denomOrgUrl += '&org_type=' + _this.orgType.toLowerCase();
                chartOptions.denomAllNHS = _this.baseUrl + 'org_details/?format=json';
            }
            chartOptions.denomOrgUrl += '&org=' + _this.orgId;
            chartOptions.friendly = formatters.getFriendlyNamesForChart(chartOptions);
            _this.setUpChart(chartOptions);
        });
    },

    setUpMap: function() {
      if ($('#map-ccg').length) {
          var map = L.map('map-ccg').setView([52.905, -1.79], 6);
          map.scrollWheelZoom.disable();
          L.tileLayer('https://{s}.tiles.mapbox.com/v3/annapowellsmith.ljij4na8/{z}/{x}/{y}.png', {
              attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
              maxZoom: 18
          }).addTo(map);
          var styleOptions = {"style": {"fillColor": "#ff00ff", "weight": "2", "color": "#333"}};
          var layer = L.geoJson(boundary, styleOptions).addTo(map);
          map.fitBounds(layer.getBounds());
      }
    },

    setUpShowPractices: function() {
        $('#showall').on('click', function(e) {
            e.preventDefault();
            $('#practices li.hidden').each(function () {
                this.style.setProperty( 'display', 'list-item', 'important' );
            });
            $(this).hide();
        });
    },

    setUpChart: function(chartOptions) {
        var _this = this;
        $.when(
            $.ajax(chartOptions.numOrgUrl),
            $.ajax(chartOptions.denomOrgUrl),
            $.ajax(chartOptions.numAllNHS),
            $.ajax(chartOptions.denomAllNHS)
            ).done(function(numOrgResponse, denomOrgResponse, numAllResponse, denomAllResponse) {
                var numOrgData = numOrgResponse[0];
                var denomOrgData = denomOrgResponse[0];
                var combinedOrgData = utils.combineXAndYDatasets(denomOrgData, numOrgData, chartOptions.chartValues);
                var numAllData = numAllResponse[0];
                var denomAllData = denomAllResponse[0];
                var combinedAllData = utils.combineXAndYDatasets(denomAllData, numAllData, chartOptions.chartValues);
                var chartOrgData = _this.convertData(combinedOrgData);
                var chartAllData = _this.convertData(combinedAllData);
                $('#' + this.chartId).find(_this.el.status).hide();
                _this.renderGraph(chartOptions, chartOrgData, chartAllData);
            })
            .fail(function(){
                $('#' + this.chartId).find(_this.el.status).html(_this.errorMessage).show();
            });

    },

    renderGraph: function(chartOptions, combined1, combined2) {
        //console.log('renderGraph', chartOptions, combined1, combined2);
        var _this = this;
        if (combined1.length) {
            var hcOptions = _this.getHighchartsOptions(chartOptions);
            hcOptions.series = [{
                'name': 'Ratio across ' + _this.orgName.replace(/&amp;/g, "&"),
                'data': combined1,
                'color': 'red'
            },
            {
                'name': 'Ratio across all GPs in NHS England',
                'data': combined2
            }];
            var chart = new Highcharts.Chart(hcOptions);
        } else {
            $('#' + chartOptions.chartId).find(_this.el.status).html('No data found for this ' + _this.orgType).show();
        }
    },

    convertData: function(data) {
        _.each(data, function(d) {
            var dates = d.date.split('-');
            var date =  Date.UTC(dates[0], dates[1]-1, dates[2]);
            d.x = date;
            d.y = (d.ratio_items !== null) ? parseFloat(d.ratio_items) : null;
        });
        return data;
    },

    getHighchartsOptions: function(graphOptions) {
        var _this = this,
            values = graphOptions.chartValues;
        var options = $.extend(true, {}, chartOptions.dashOptions);
        options.chart.renderTo = graphOptions.chartId;
        options.yAxis.title.text = graphOptions.friendly.yAxisTitle;
        options.tooltip = {
            formatter: function() {
                var str = '<b>' + this.series.name;
                str += ' in ' + Highcharts.dateFormat('%b \'%y',
                                      new Date(this.x));
                str += '</b><br/>';
                str += Highcharts.numberFormat(this.point[values.y], 0);
                str += (graphOptions.denom === 'chemical') ? ' items for ' : ' ';
                str += graphOptions.friendly.friendlyNumerator + '<br/>';

                str += Highcharts.numberFormat(this.point[values.x_val], 0);
                str += (graphOptions.denom === 'chemical') ? ' items for ' : ' ';
                str += graphOptions.friendly.friendlyDenominator + '<br/>';

                str += 'Ratio: ' + Highcharts.numberFormat(this.point[values.ratio], 2);
                str += ' ' + graphOptions.friendly.friendlyNumerator;
                str += ' items<br/>per ' + graphOptions.friendly.fullDenominator;
                return str;
            }
        };
        return options;
    }
};

barChart.setUp();


})();

