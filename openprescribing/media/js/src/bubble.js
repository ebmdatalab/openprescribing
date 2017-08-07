global.jQuery = require('jquery');
global.$ = global.jQuery;
require('bootstrap');
require('Highcharts');
require('Highcharts-export');
require('Highcharts-more');
var chroma = require('chroma-js');
var _ = require('underscore');

jQuery(document).ready(function() {
  var highchartsOptions = {
    chart: {
      type: 'bubble',
      plotBorderWidth: 1,
      zoomType: 'xy'
    },

    legend: {
      enabled: false
    },

    title: {
      text: 'Price-per-unit cost of <br>' + generic_name
    },
    subtitle: {
      text: null
    },
    plotOptions: {
      bubble: {
        minSize: 3
      }
    },
    xAxis: {
      type: 'category',
      gridLineWidth: 1,
      title: {
        text: null
      },
      labels: {
        style: {
          textOverflow: 'none'
        }
      }
    },

    yAxis: {
      gridLineWidth: 1,
      title: {
        text: 'PPU'
      },
      labels: {
        format: '£{value}'
      },
      plotLines: [{
        color: 'black',
        dashStyle: 'dot',
        width: 2,
        value: 12,
        label: {
          y: 15,
          style: {
            fontStyle: 'italic'
          },
          text: 'Mean PPU for ' + highlight_name
        },
        zIndex: 3
      }]
    },
    tooltip: {
      useHTML: true,
      headerFormat: '',
      pointFormat: '{point.z:,.0f} units of {point.name} @ £{point.y:,.2f}',
      followPointer: true
    },

    series: [{
      data: [
      ]
    }]

  };
  /** Sets color on each presentation on a green-red scale according
   * to its mean PPU */
  function setGenericColours(data) {
    var scale = chroma.scale(['green', 'yellow', 'red']);
    var means = _.map(data.series, function(d) {
      return d.mean_ppu
    });
    var maxPPU = _.max(means);
    var minPPU = _.min(means);
    var maxRange = maxPPU - minPPU;
    _.each(data.series, function(d) {
      var ratio = (d.mean_ppu - minPPU) / maxRange;
      d.color = scale(ratio).hex();
    });
  }
  /*** Add some text indicating which presentation is the generic
   */
  function labelGenericInSeries(data) {
    var generic_index = _.findIndex(data.categories, function(x) {
      return x.is_generic });
    if (generic_index > -1 ) {
      var generic_name = data.categories[generic_index].name;
      _.each(data.series, function(d) {
        if (d.name === generic_name) {
          d.name += '<span style="color: red"> (prescribed generically)</span>';
        }
      });
    }
  }

  $.getJSON(
    bubble_data_url,
    function(data) {
      setGenericColours(data);
      labelGenericInSeries(data);
      var options = $.extend(true, {}, highchartsOptions);
      options.chart.width = $('.tab-content').width();
      options.subtitle.text = 'for prescriptions within NHS England';
      options.series[0].data = data.series;
      options.yAxis.plotLines[0].value = data.plotline;
      $('#all_practices_chart').highcharts(options);
    }
  );
  $.getJSON(
    bubble_data_url + '&focus=1',
    function(data) {
      setGenericColours(data);
      labelGenericInSeries(data);
      var options = $.extend(true, {}, highchartsOptions);
      // Set the width explicitly, because highcharts can't tell the
      // width of a hidden tab container
      options.chart.width = $('.tab-content').width();
      options.subtitle.text = 'for prescriptions within ' + highlight_name;
      options.series[0]['data'] = data.series;
      options.yAxis.plotLines[0].value = data.plotline;
      $('#highlight_chart').highcharts(options);
    }
  );
});
