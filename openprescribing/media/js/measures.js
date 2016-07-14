(function() {
  var _ = require('underscore');
  var mu = require('./src/measure_utils');
  var config = require('./src/config');
  var Highcharts = require('Highcharts');
  var chartOptions = require('./src/highcharts-options');
  var L = require('mapbox.js');
  var Handlebars = require('handlebars');
  Highcharts.setOptions({
    global: {useUTC: false}
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
      sortButtons: ".btn-group > .btn",
      summaryTemplate: '#summary-panel',
      panelTemplate: "#measure-panel"
    },

    setUp: function() {
      var _this = this;
      var summaryTemplate =
        Handlebars.compile($(_this.el.summaryTemplate).html());
      var panelTemplate =
        Handlebars.compile($(_this.el.panelTemplate).html());
      var NUM_MONTHS_FOR_RANKING = 6;
      var centiles = ['10', '20', '30', '40', '50', '60', '70', '80', '90'];

      _this.allGraphsRendered = false;
      _this.graphsToRenderInitially = 24;

      var options = measureData;
      options.rollUpBy = (options.measure) ? 'org_id' : 'measure_id';

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

          chartData = mu.annotateAndSortData(chartData, options,
            NUM_MONTHS_FOR_RANKING);
          chartData = mu.addChartAttributes(chartData, globalData,
            options.globalCentiles, centiles, options,
            NUM_MONTHS_FOR_RANKING);

          var perf = mu.getPerformanceSummary(chartData, options,
            NUM_MONTHS_FOR_RANKING);
          $(_this.el.perfSummary).html(summaryTemplate(perf));

          var html = '';
          _.each(chartData, function(d) {
            html += panelTemplate(d);
          });
          $(_this.el.charts).html(html);
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
        })
        .fail(function(jqXHR, textStatus, error) {
          console.log("Error " + error + " when making request " + jqXHR);
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
              color: "#333",
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
        return Number(a.costsaving) - Number(b.costsaving);
      });
      $(_this.el.sortButtons).click(function() {
        $(this).addClass("active").siblings().removeClass("active");
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
    }
  };

  measures.setUp();
})();
