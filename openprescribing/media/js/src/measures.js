var $ = require('jquery');
var _ = require('underscore');
var mu = require('./measure_utils');
var domready = require('domready');
var Highcharts = require('Highcharts');
var chartOptions = require('./highcharts-options');
var L = require('mapbox.js');
var Handlebars = require('handlebars');
var config = require('./config');
var downloadjs = require('downloadjs');
Highcharts.setOptions({
  global: {useUTC: false},
});
L.mapbox.accessToken = 'pk.eyJ1IjoiYW5uYXBvd2VsbHNta' +
  'XRoIiwiYSI6ImNzY1VpYkkifQ.LC_IcHpHfOvWOQCuo5t7Hw';

var measures = {
  el: {
    chart: '#charts .chart',
    charts: '#charts',
    mapPanel: 'map-measure',
    perfSummary: '#perfsummary',
    showAll: '#showall',
    sortButtons: '.btn-group > .btn',
    summaryTemplate: '#summary-panel',
    panelTemplate: '#measure-panel',
    noCostSavingWarning: '#no-cost-saving-warning'
  },

  setUp: function() {
    var _this = this;
    var summaryTemplate =
        Handlebars.compile($(_this.el.summaryTemplate).html());
    var panelTemplate =
        Handlebars.compile($(_this.el.panelTemplate).html());
    var NUM_MONTHS_FOR_RANKING = 6;
    var centiles = ['10', '20', '30', '40', '50', '60', '70', '80', '90'];
    var selectedMeasure = window.location.hash;
    _this.allGraphsRendered = false;
    _this.graphsToRenderInitially = 24;
    var options = measureData; // defined in handlebars templates
    if (!options.rollUpBy) {
      options.rollUpBy = (options.measure) ? 'org_id' : 'measure_id';
    }
    _this.setUpShowPractices();
    _this.setUpMap(options);

    var urls = mu.getDataUrls(options);
    $.when(
      $.ajax(urls.panelMeasuresUrl),
      $.ajax(urls.globalMeasuresUrl)
    ).done(function(panelMeasures, globalMeasures) {
      var chartData = panelMeasures[0].measures;
      var globalData = globalMeasures[0].measures;

      _.extend(options,
               mu.getCentilesAndYAxisExtent(globalData, options, centiles));
      chartData = mu.annotateData(chartData, options,
                                  NUM_MONTHS_FOR_RANKING);
      chartData = mu.addChartAttributes(chartData, globalData,
                                        options.globalCentiles, centiles, options,
                                        NUM_MONTHS_FOR_RANKING);
      chartData = mu.sortData(chartData);
      var perf = mu.getPerformanceSummary(chartData, options,
                                          NUM_MONTHS_FOR_RANKING);
      $(_this.el.perfSummary).html(summaryTemplate(perf));
      var html = '';
      _.each(chartData, function(d) {
        html += panelTemplate(d);
      });
      $(_this.el.charts)
        .html(html)
        .find('a[data-download-chart-id]')
        .on('click', function() {
          var chartId = $(this).data('download-chart-id');
          _this.startDataDownload(chartData, chartId);
          return false;
        });
      _.each(chartData, function(d, i) {
        if (i < _this.graphsToRenderInitially) {
          var chOptions = mu.getGraphOptions(d,
                                             options, d.is_percentage, chartOptions);
          if (chOptions) {
            new Highcharts.Chart(chOptions);
          }
        }
      });

      // On long pages, render remaining graphs only after scroll,
      // to stop the page choking on first load.
      $(window).scroll(function() {
        if (_this.allGraphsRendered === false) {
          _.each(chartData, function(d, i) {
            if (i >= _this.graphsToRenderInitially) {
              var chOptions = mu.getGraphOptions(d,
                                                 options, d.is_percentage, chartOptions);
              if (chOptions) {
                new Highcharts.Chart(chOptions);
              }
            }
          });
          _this.allGraphsRendered = true;
        }
      });

      if (options.rollUpBy === 'measure_id') {
        _this.setUpSortGraphs();
      }
      if (selectedMeasure !== '') {
        $('#overlay').fadeIn(300);
        var measureId = '#measure_' + selectedMeasure.substring(selectedMeasure.indexOf('#') + 1);
        $(measureId).css('z-index', '99999');
        $('html, body').animate({
          scrollTop: $(measureId).offset().top,
        }, 1000);
        $('#overlay').on('click', function() {
          $('#overlay').stop().fadeOut(300);
        });
      }
      if (location.search.indexOf('sortBySavings') > -1) {
        $(_this.el.sortButtons).click();
      }
    })
      .fail(function(jqXHR, textStatus, error) {
        console.log('Error ' + error + ' when making request ' + jqXHR);
      });
  },

  setUpShowPractices: function() {
    $(this.el.showAll).on('click', function(e) {
      e.preventDefault();
      $('#practices li.hidden').each(function(i, item) {
        $(item).removeClass('hidden');
      });
      $(this).hide();
    });
  },

  setUpMap: function(options) {
    var _this = this;
    if ($('#' + _this.el.mapPanel).length) {
      var map = L.mapbox.map(_this.el.mapPanel,
                             'mapbox.streets').setView([52.905, -1.79], 6);
      map.scrollWheelZoom.disable();
      var url = config.apiHost + '/api/1.0/org_location/?org_type=' +
          options.orgType.toLowerCase();
      url += '&q=' + options.orgId;
      var layer = L.mapbox.featureLayer()
          .loadURL(url)
          .on('ready', function() {
            if (layer.getBounds().isValid()) {
              map.fitBounds(layer.getBounds(), {maxZoom: 12});
              layer.setStyle({fillColor: '#ff00ff',
                              fillOpacity: 0.2,
                              weight: 0.5,
                              color: '#333',
                              radius: 10});
            } else {
              $('#map-container').html('');
            }
          })
          .addTo(map);
    }
  },

  setUpSortGraphs: function() {
    var _this = this;
    var chartsByPercentile = $(_this.el.chart);
    var chartsBySaving = $(chartsByPercentile).filter(function(a) {
      return $(this).data('costsaving') !== 0;
    });
    chartsBySaving.sort(function(a, b) {
      return $(b).data('costsaving') - $(a).data('costsaving');
    });
    if (chartsBySaving.length === 0) {
      chartsBySaving = chartsBySaving.add(
        $(_this.el.noCostSavingWarning).clone().removeClass('hidden')
      );
    }
    $(_this.el.sortButtons).click(function() {
      $(this).addClass('active').siblings().removeClass('active');
      if ($(this).data('orderby') === 'savings') {
        $(_this.el.charts).fadeOut(function() {
          $(_this.el.charts).html(chartsBySaving).fadeIn();
        });
      } else {
        $(_this.el.charts).fadeOut(function() {
          $(_this.el.charts).html(chartsByPercentile).fadeIn();
        });
      }
    });
  },

  startDataDownload: function(allChartData, chartId) {
    var chartData = this.getChartDataById(allChartData, chartId);
    var dataTable = this.getChartDataAsTable(chartData);
    var csvData = this.formatTableAsCSV(dataTable);
    downloadjs(csvData, chartId+'_data.csv', 'text/csv');
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
    var headers = ['date', 'numerator', 'denominator', 'ratio', 'percentile', 'cost_savings'];
    var keyPercentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90];
    headers = headers.concat(keyPercentiles.map(function(n) { return n + 'th percentile'; }));
    var percentilesByDate = this.getPercentilesByDate(chartData, keyPercentiles);
    var table = chartData.data.map(function(d) {
      return [
          d.date, d.numerator, d.denominator, d.calc_value, d.percentile, d.cost_savings
        ]
        .concat(percentilesByDate[d.date]);
    });
    table.unshift(headers);
    return table;
  },

  getPercentilesByDate: function(chartData, keyPercentiles) {
    var percentilesByDate = {};
    _.each(keyPercentiles, function(percentile) {
      _.each(chartData.globalCentiles[percentile], function(percentileData) {
        var date = percentileData.date;
        if ( ! percentilesByDate[date]) {
          percentilesByDate[date] = [];
        }
        percentilesByDate[date].push(percentileData.y);
      });
    });
    return percentilesByDate;
  },

  formatTableAsCSV: function(table) {
    return table.map(this.formatRowAsCSV.bind(this)).join('\n');
  },

  formatRowAsCSV: function(row) {
    return row.map(this.formatCellAsCSV.bind(this)).join(',');
  },

  formatCellAsCSV: function(cell) {
    cell = cell ? cell.toString() : '';
    if (cell.match(/[,"\r\n]/)) {
      return '"' + cell.replace(/"/g, '""') + '"';
    } else {
      return cell;
    }
  }
};

domready(function() {
  measures.setUp();
});
