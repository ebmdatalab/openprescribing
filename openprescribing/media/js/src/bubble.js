global.jQuery = require('jquery');
global.$ = global.jQuery;
require('bootstrap');
require('Highcharts');
require('Highcharts-export');
require('Highcharts-more');
var chroma = require('chroma-js');
var _ = require('underscore');

jQuery(document).ready(function(){
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
      text: 'Price-per-unit cost of ' + generic_name
    },
    subtitle: {
      text: null
    },
    xAxis: {
      type: 'category',
      gridLineWidth: 1,
      title: {
        text: null
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
  function setGenericColours(data) {
    var scale = chroma.scale(['green', 'yellow', 'red']);
    var maxPPU = _.max(_.map(data.series, function(d) { return d.mean_ppu }));
    var minPPU = _.min(_.map(data.series, function(d) { return d.mean_ppu }));
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
      var options = $.extend(true, {}, highchartsOptions);
      options.subtitle.text = 'for prescriptions within NHS England';
      options.series[0]['data'] = data.series;
      options.yAxis.plotLines[0].value = data.plotline;
      $('#all_practices_chart').highcharts(options);
    }
  );
  $.getJSON(
    bubble_data_url + '&focus=1',
    function(data) {
      setGenericColours(data);
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
