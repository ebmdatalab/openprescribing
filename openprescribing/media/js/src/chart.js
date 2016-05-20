global.jQuery = require('jquery');
global.$ = global.jQuery;
require('Highcharts');
require('Highcharts-export');
var noUiSlider = require('noUiSlider');
var _ = require('underscore');

Highcharts.setOptions({
  global: {useUTC: false}
});

var chartOptions = require('./highcharts-options');
var hashHelper = require('./analyse-hash');
var utils = require('./chart_utils');
var formatters = require('./chart_formatters');
var map = require('./map');
var barChart = require('./bar-chart');
var lineChart = require('./line-chart');
var scatterChart = require('./scatter-chart');

var analyseChart = {

  el: {
    resultsEl: $('#results'),
    chartEl: $('#chart'),
    errorContainer: $('#error'),
    errorMessage: $('#error-message'),
    highlightOrgType: $('#highlightType'),
    highlightNotFound: $('#itemNotFound'),
    loadingEl: $('.loading-wrapper'),
    loadingMessage: $('#chart-loading p'),
    slider: $("#chart-date-slider"),
    submitButton: $('#update'),
    tabs: $('#tabs li'),
    tabChart: $('#chart-tab'),
    tabMap: $('#map-tab'),
    tabSummary: $('#summary-tab'),
    tabPanelChart: $('#chart-panel'),
    title: '.chart-title',
    subtitle: '.chart-sub-title',
    rowCount: ('#data-rows-count')
  },

  renderChart: function(globalOptions) {
        // console.log('renderChart', globalOptions);
        // For older Internet Explorer, we deliberately want to
        // delay execution in places, to prevent slow-running script errors.
    this.isOldIe = utils.getIEVersion();
    this.scriptDelay = (this.isOldIe) ? 1500 : 0;
    this.globalOptions = globalOptions;
    this.el.submitButton.button('loading');
    this.el.errorContainer.hide();
    this.el.loadingEl.show();
    this.getBackendData();
  },

  clearAllData: function() {
    this.globalOptions.data.numeratorData = [];
    this.globalOptions.data.denominatorData = [];
    this.globalOptions.data.combinedData = [];
    $('#data-link').off();
  },

  showErrorMessage: function(status, error) {
    var errorHtml;
    if (error !== null) {
      errorHtml += '<p>Sorry, something went wrong.</br>';
      errorHtml += 'This is what we know: ' + status + ': ' + error + '</p>';
    } else {
      errorHtml = "<p>" + status + "</p>";
    }
    this.el.errorMessage.html(errorHtml);
    this.el.errorContainer.show();
    this.el.resultsEl.hide();
    this.el.loadingEl.hide();
  },

  getBackendData: function() {
    this.clearAllData();
    this.globalOptions.urls = utils.constructQueryURLs(this.globalOptions);
    var _this = this;
    _this.el.loadingMessage.text('Fetching data...');
    $.when(
            $.ajax(_this.globalOptions.urls.numeratorUrl),
            $.ajax(_this.globalOptions.urls.denominatorUrl)
            ).done(function(response1, response2) {
              _this.el.loadingMessage.text('Parsing data...');
              _this.globalOptions.data.numeratorData = response1[0];
              _this.globalOptions.data.denominatorData = response2[0];
              _this.el.loadingMessage.text('Rendering chart...');
              setTimeout(function() {
                _this.loadChart();
              }, _this.scriptDelay);
            })
            .fail(function(status, error) {
              var msg = (_.has(status, 'responseText')) ? status.responseText :
                                 "Sorry, something went wrong.";
              _this.showErrorMessage(msg.replace(/"/g, ""), null);
            });
  },

  loadChart: function() {
    var _this = this;
    this.el.submitButton.button('reset');
    this.globalOptions.activeOption = 'items';
    this.setUpData();
    this.globalOptions.allMonths = utils.getAllMonthsInData(this.globalOptions.data.combinedData);
    this.globalOptions.activeMonth = this.globalOptions.allMonths[this.globalOptions.allMonths.length - 1];
    this.globalOptions.friendly = formatters.getFriendlyNamesForChart(this.globalOptions);
    this.hash = hashHelper.setHashParams(this.globalOptions);
    this.hash += ($(this.el.submitButton).data('clicked')) ? '&source=button' : '&source=pageload';
    ga('send', {
      'hitType': 'event',
      'eventCategory': 'search_button',
      'eventAction': 'click',
      'eventLabel': _this.hash
    });

    if (this.globalOptions.data.combinedData.length > 0) {
      this.addDataDownload();
      this.el.loadingEl.hide();
      this.el.resultsEl.show();
      this.globalOptions.barChart = barChart.setUp(chartOptions.barOptions,
                                                         this.globalOptions);

            // For now, don't render the map and line chart in older browsers -
            // they are just too slow.
            // This could be fixed by adding more pauses in the data calculations,
            // and making the data calculations more efficient.
      if (!this.isOldIe) {
        $(_this.el.tabChart).removeClass('hidden');
        $(_this.el.tabMap).removeClass('hidden');
        _this.globalOptions.lineChart = lineChart.setUp(chartOptions.lineOptions,
                                                               _this.globalOptions);
        map.setup(_this.globalOptions);
      }

            // TODO: Text for tabs. Tidy this up.
      var summaryTab = '';
      var numOrgs = this.globalOptions.orgIds.length;
      if (this.globalOptions.org === 'CCG') {
        summaryTab = (numOrgs) ? 'Show vs other CCGs' : 'Show all CCGs';
      } else {
        if (numOrgs) {
          var isPractice = (this.globalOptions.orgIds[0].id.length > 3);
          summaryTab = (isPractice) ? 'Show vs others in CCG' : 'Show summary';
        } else {
          summaryTab = 'Show for all CCGs';
        }
      }
      $(this.el.tabSummary).find('a').text(summaryTab);
      $(_this.el.title).html(_this.globalOptions.friendly.chartTitle);
      $(_this.el.subtitle).html(_this.globalOptions.friendly.chartSubTitle);
      this.setUpSlider();
      this.setUpChartEvents();
    } else {
      this.showErrorMessage("No data found for this query. Please try again.", null);
    }
  },

  setUpData: function() {
        // console.log('setUpData');
    var xData = this.globalOptions.data.denominatorData,
      yData = this.globalOptions.data.numeratorData;
    this.globalOptions.chartValues = utils.setChartValues(this.globalOptions);
        // Combines the datasets and calculates the ratios.
    var combinedData = utils.combineXAndYDatasets(xData, yData,
                                                      this.globalOptions.chartValues);
    this.globalOptions.data.combinedData = combinedData;
  },

  addDataDownload: function() {
    var _this = this;
    var csvHeader = ['date', 'id', 'name', 'y_items', 'y_actual_cost'],
      sampleItem, csvRows, encodedUri;
    sampleItem = this.globalOptions.data.combinedData[0];
    if ('astro_pu_cost' in sampleItem) {
      csvHeader.push('astro_pu_cost');
    } else if ('total_list_size' in sampleItem) {
      csvHeader.push('total_list_size');
    } else if ('star_pu.oral_antibacterials_item' in sampleItem) {
      csvHeader.push('star_pu.oral_antibacterials_item');
    } else {
      csvHeader.push('x_items');
      csvHeader.push('x_actual_cost');
    }
    csvRows = [csvHeader.join(",")];
    _.each(this.globalOptions.data.combinedData, function(d) {
      var str = '';
      _.each(csvHeader, function(i, count) {
        str += (i === 'name') ? '"' : '';
        str += d[i];
        str += (i === 'name') ? '"' : '';
        str += (count !== csvHeader.length - 1) ? ',' : '';
      });
      csvRows.push(str);
    });
    encodedUri = encodeURI("data:text/csv;charset=utf-8," + csvRows.join("\n"));
    $('#data-link').on('click', function(e) {
      e.preventDefault();
      ga('send', {
        'hitType': 'event',
        'eventCategory': 'data_link',
        'eventAction': 'click',
        'eventLabel':  _this.hash
      });
      window.open(encodedUri);
    });
    $(this.el.rowCount).text('(' + this.globalOptions.data.combinedData.length + ' rows)');
  },

  setUpChartEvents: function() {
    var _this = this;
        // Tab clicks.
    $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function(e) {
      $(window).resize(); // CSS hack.
      if (($(this).attr('href') === '#chart-panel') || ($(this).attr('href') === '#data-panel')) {
        $('#chart-options').hide();
      } else {
        $('#chart-options').show();
      }
      if ($(this).attr('href') === '#map-panel') {
        if (!_this.isOldIe) {
          map.resize();
        }
      }
    });
        // Items/spending toggle.
    $('#items-spending-toggle .btn').on('click', function(e) {
      e.preventDefault();
      ga('send', {
        'hitType': 'event',
        'eventCategory': 'items_spending_toggle',
        'eventAction': 'click',
        'eventLabel':  _this.hash
      });
      $('#items-spending-toggle .btn').removeClass('btn-info').addClass('btn-default');
      $(this).addClass('btn-info').removeClass('btn-default');
      _this.globalOptions.activeOption = $(this).data('type');
      _this.updateCharts();

    });
  },

  updateCharts: function() {
        // console.log('updateCharts', this.globalOptions.activeOption, this.globalOptions.activeMonth);
    var _this = this;
    _this.globalOptions.chartValues = utils.setChartValues(_this.globalOptions);
    _this.globalOptions.friendly = formatters.getFriendlyNamesForChart(_this.globalOptions);
    $(_this.el.title).html(_this.globalOptions.friendly.chartTitle);
    $(_this.el.subtitle).html(_this.globalOptions.friendly.chartSubTitle);
    barChart.update(_this.globalOptions.barChart,
                        _this.globalOptions.activeMonth,
                        _this.globalOptions.chartValues.ratio,
                        _this.globalOptions.friendly.yAxisTitle,
                        _this.globalOptions.friendly.yAxisFormatter);
    if (!_this.isOldIe) {
      map.update(_this.globalOptions.activeOption, _this.globalOptions.activeMonth,
                       _this.globalOptions.friendly.chartTitle,
                       _this.globalOptions.friendly.chartSubTitle);
    }
  },

  setUpSlider: function() {
    var sliderMax = this.globalOptions.allMonths.length - 1;
    var _this = this;
    if (this.el.slider.val()) {
      this.el.slider.noUiSlider({
        range: {
          min: 0,
          max: sliderMax
        }
      }, true);
      this.el.slider.val(sliderMax);
      this.el.slider.noUiSlider_pips({
        mode: 'count',
        values: 10,
        density: 5,
        stepped: true,
        format: {
          to: function(val) {
            var d = _this.globalOptions.allMonths[val];
            return Highcharts.dateFormat('%b \'%y',
                                  new Date(d.replace(/-/g, '/')));
          },
          from: function(val) {
            return _this.globalOptions.allMonths.indexOf[val] + 1;
          }
        }
      });
    } else {
      this.el.slider.noUiSlider({
        step: 1,
        start: [sliderMax],
        range: {
          min: 0,
          max: sliderMax
        }
      }).on({
        change: function() {
          _this.onChange($(this).val());
        }
      });
      this.el.slider.noUiSlider_pips({
        mode: 'count',
        values: 10,
        density: 5,
        stepped: true,
        format: {
          to: function(val) {
            var d = _this.globalOptions.allMonths[val];
            return Highcharts.dateFormat('%b \'%y',
                                  new Date(d.replace(/-/g, '/')));
          },
          from: function(val) {
            return _this.globalOptions.allMonths.indexOf[val] + 1;
          }
        }
      });
    }
  },

  onChange: function() {
    var _this = this;
    ga('send', {
      'hitType': 'event',
      'eventCategory': 'time_slider',
      'eventAction': 'slide',
      'eventLabel':  _this.hash
    });
    var monthIndex = parseInt(this.el.slider.val());
    this.globalOptions.activeMonth = this.globalOptions.allMonths[monthIndex];
    this.updateCharts();
  }

};
module.exports = analyseChart;
