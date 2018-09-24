var $ = require('jquery');
var domready = require('domready');

require('bootstrap');
var Highcharts = require('Highcharts');
require('Highcharts-export')(Highcharts);
require('Highcharts-more')(Highcharts);
var chroma = require('chroma-js');
var _ = require('underscore');

domready(function() {
  if (typeof bubble_data_url !== 'undefined') {
    var highchartsOptions = {
      chart: {
        type: 'bubble',
        plotBorderWidth: 1,
        zoomType: 'xy',
      },

      legend: {
        enabled: false,
      },

      title: {
        text: 'Price-per-unit cost of <br>' + generic_name,
      },
      subtitle: {
        text: null,
      },
      plotOptions: {
        bubble: {
          minSize: 3,
        },
      },
      xAxis: {
        type: 'category',
        gridLineWidth: 1,
        title: {
          text: null,
        },
        labels: {
          style: {
            textOverflow: 'clip',
          },
          formatter: function() {
            var label = this.value.name || '';
            if (this.value.is_generic) {
              label += ' <span style="color: red">';
              label += '(prescribed generically)</span>';
            }
            return label;
          }
        },
      },

      yAxis: {
        gridLineWidth: 1,
        title: {
          text: 'PPU',
        },
        labels: {
          formatter: function() {
            if (this.value < 0) {
              return '';
            } else {
              return '£' + this.value;
            }
          }
        },
        plotLines: [{
          color: 'black',
          dashStyle: 'dot',
          width: 2,
          value: 12,
          label: {
            y: 15,
            style: {
              fontStyle: 'italic',
            },
            text: 'Mean PPU for ' + highlight_name,
          },
          zIndex: 3,
        }],
      },
      tooltip: {
        useHTML: true,
        headerFormat: '',
        pointFormat: '{point.z:,.0f} units of {point.name} @ £{point.y:,.2f}',
        followPointer: true,
      },

      series: [{
        data: [
        ],
      }],

    };
    /** Sets color on each presentation on a green-red scale according
     * to its mean PPU */
    function setGenericColours(data) {
      var scale = chroma.scale(['green', 'yellow', 'red']);
      var means = _.map(data.series, function(d) {
        return d.mean_ppu;
      });
      var maxPPU = _.max(means);
      var minPPU = _.min(means);
      var maxRange = maxPPU - minPPU;
      _.each(data.series, function(d) {
        var ratio = (d.mean_ppu - minPPU) / maxRange;
        d.color = scale(ratio).hex();
      });
    }
    $.getJSON(
      bubble_data_url,
      function(data) {
        setGenericColours(data);
        // Categories are treated as 1-indexed in the series data so we add an
        // intial blank value here
        data.categories.unshift(null);
        var options = $.extend(true, {}, highchartsOptions);
        options.chart.width = $('.tab-content').width();
        options.subtitle.text = 'for prescriptions within NHS England';
        options.series[0].data = data.series;
        options.yAxis.plotLines[0].value = data.plotline;
        options.xAxis.categories = data.categories;
        $('#all_practices_chart').highcharts(options);
      }
    );
    $.getJSON(
      bubble_data_url + '&focus=1',
      function(data) {
        setGenericColours(data);
        // Categories are treated as 1-indexed in the series data so we add an
        // intial blank value here
        data.categories.unshift(null);
        var options = $.extend(true, {}, highchartsOptions);
        // Set the width explicitly, because highcharts can't tell the
        // width of a hidden tab container
        options.chart.width = $('.tab-content').width();
        options.subtitle.text = 'for prescriptions within ' + highlight_name;
        options.series[0].data = data.series;
        options.yAxis.plotLines[0].value = data.plotline;
        options.xAxis.categories = data.categories;
        $('#highlight_chart').highcharts(options);
      }
    );
  }
});
