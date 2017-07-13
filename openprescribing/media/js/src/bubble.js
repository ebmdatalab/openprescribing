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
      text: null
    },
    xAxis: {
      //tickMarkPlacement: 'between',#

      type: 'category',
      gridLineWidth: 1,
      title: {
        text: 'Presentation'
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
          text: 'Mean PPU for entity'
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
      options.series[0]['data'] = data.series;
      options.title.text = 'England-wide distribution of PPU for ' + entity_name;
      console.log(data.categories);
      console.log(data.series);
      options.yAxis.plotLines[0].value = data.plotline;
      $('#all_practices_chart').highcharts(options);
    }
  );
  $.getJSON(
    bubble_data_url + '&focus=1',
    function(data) {
      setGenericColours(data);
      var options = $.extend(true, {}, highchartsOptions);
      options.series[0]['data'] = data.series;
      options.title.text = 'CCG-wide distribution of PPU for ' + entity_name;
      console.log(data.categories);
      console.log(data.series);
      options.yAxis.plotLines[0].value = data.plotline;
      $('#highlight_chart').highcharts(options);
    }
  );
});
