global.jQuery = require('jquery');
global.$ = global.jQuery;
require('bootstrap');
require('Highcharts');
require('Highcharts-export');
var _ = require('underscore');

var chartOptions = require('./highcharts-options');

var tariffChart = {

  initialiseData: function(data) {
    // add nulls
    var byVmpp = {};
    var hasConcession = {};
    _.each(data, function(d) {
      var dates = d.date.split('-');
      var date = Date.UTC(dates[0], dates[1]-1, dates[2]);
      if (!(d.vmpp in byVmpp)) {
        byVmpp[d.vmpp] = [];
      }
      byVmpp[d.vmpp].push({
        x: date,
        y: parseFloat(d.price_pence)/100,
        tariff_category: d.tariff_category,
      });
      var concessionKey = d.vmpp + ' (price concession)';
      if (d.concession) {
        hasConcession[concessionKey] = true;
      }
      if (!(concessionKey in byVmpp)) {
        byVmpp[concessionKey] = [];
      }
      byVmpp[concessionKey].push({
        x: date,
        y: d.concession ? parseFloat(d.concession) : d.concession});
    });
    var newData = [];
    var categoriesShown = [];
    for (var vmpp in byVmpp) {
      var isConcessionSeries = vmpp.indexOf('concession') > -1;
      if (byVmpp.hasOwnProperty(vmpp)) {
        var zIndex = 1 - _.max(_.pluck(byVmpp[vmpp], 'y'));
        if (isConcessionSeries && !hasConcession[vmpp]) {
          continue;
        } else {
          zones = [];
          var lastCat = null;
          var cat = null;
          var dashStyle;
          var dataWithDummy = byVmpp[vmpp].concat([{tariff_category: null}]);
          _.each(dataWithDummy, function(d) {
            cat = d.tariff_category;
            if (!lastCat) {
              lastCat = cat;
            }
            // is a zone where it ends rather than starts?
            if (cat !== lastCat) {
              switch (lastCat) {
              case 'Part VIIIA Category A':
                categoriesShown.push('Category A');
                dashStyle = 'line';
                break;
              case 'Part VIIIA Category C':
                categoriesShown.push('Category C');
                dashStyle = 'dot';
                break;
              case 'Part VIIIA Category M':
                categoriesShown.push('Category M');
                dashStyle = 'dash';
                break;
              }
              // starting from 'value', thereafter...
              zones.push(
                {value: d.x, dashStyle: dashStyle}
              );
            }
            lastCat = cat;
          });
          console.log(zones);
          newData.push({
            name: vmpp,
            data: byVmpp[vmpp],
            zones: zones,
            zoneAxis: 'x',
            zIndex: zIndex});
        }
      }
    }

    _.each(_.uniq(categoriesShown), function(category) {
      newData.push({name: category, data: [], color: '#fff'});
    });
    return newData;
  },

    getChartTitle: function(graphType) {
        var title = 'Total ';
        title += (graphType === 'actual_cost') ? 'spending' : 'items';
        if ((pageType !== 'ccg') && (pageType !== 'practice')) {
            title += ' across all practices in England';
        }
        return title;
    },


    initialiseChartOptions: function(chartOptions, data) {
      var _this = this;
      var options = chartOptions.baseOptions;
      options.chart.showCrosshair = false;
      options.chart.marginTop = 40;
      options.plotOptions = {
        series: {
          marker: {
            radius: 0
          },
          fillOpacity: 0.4,
          connectNulls: false,
          pointPadding: 0,
          groupPadding: 0
        }
      };
      options.chart.spacingTop = 20;
      options.chart.type = 'area';
      options.title.text = chartTitle;
      options.legend = {
        useHTML: true,
        floating: false,
        symbolHeight: 0,
        symbolWidth: 0,
        itemMarginTop: 4,
        itemMarginBottom: 4,
        labelFormatter: function() {
          var str = '<div><div style="width:30px;display:inline-block;padding:3px 2px 3px 2px;margin-right: 4px;text-align:center;color:#FFF;background-color:' + this.color + '">';
          if (this.name == 'Category A') {
            str += '<svg width="30" height="5"><path d="M0 0 H30" stroke="black" stroke-width="2" stroke-dasharray="none" /></svg>';
          } else if (this.name == 'Category C') {
            str += '<svg width="30" height="5"><path d="M0 0 H30" stroke="black" stroke-width="2" stroke-dasharray="2,6" /></svg>';
          } else if (this.name == 'Category M') {
            str += '<svg width="30" height="5"><path d="M0 0 H30" stroke="black" stroke-width="2" stroke-dasharray="8,6" /></svg>';
          }
          str += '</div>'
          return str + this.name;
        }
      }
      options.tooltip = {
        pointFormatter: function() {
          var str = '<span style="color:' + this.color + '">\u25CF</span> ';
          str += this.series.name + ': <b>£' + this.y.toFixed(2);
          if (this.tariff_category) {
            str += ' (' + this.tariff_category + ') ';
          }
          str += '</b><br/>';
          return str;
        }
      }

      if (data.length > 1) {
        options.legend.enabled = true;
      } else {
        options.legend.enabled = false;
      }
        options.yAxis.title = {
            text: "Price (£)"
        };
        return options;
    },

  setUp: function() {
    var _this = this;
    $('.tariff-selector').select2(
      {placeholder: 'Start typing a presentation name'}
    );
        $.ajax({
          type: "GET",
          url: filename,
          error: function() {
            $('.status').html('<p>Sorry, something went wrong.</p>');
          },
          success: function(response) {
            $('.status').hide();
            var data = _this.initialiseData(response);
            chartOptions = _this.initialiseChartOptions(chartOptions, data);
            if (data.length) {
                $('#tariff').show();
                chartOptions.series = data;
                var chart = new Highcharts.Chart(chartOptions);
            } else {
                $('#tariff').hide();
                $('#no-data').show();
            }
          }
        });
    }
};

$(document).ready(function() {
  tariffChart.setUp();
});
