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
      text: 'Sugar and fat intake per country'
    },

    subtitle: {
      text: 'Source: <a href="http://www.euromonitor.com/">Euromonitor</a> and <a href="https://data.oecd.org/">OECD</a>'
    },

    xAxis: {
      tickMarkPlacement: 'between',
      gridLineWidth: 1,
      title: {
        text: 'Drugs'
      },
      categories: null
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
      headerFormat: '<table>',
      pointFormat: '<tr><th colspan="2"><h3>{point.name}</h3></th></tr>' +
        '<tr><th>PPU:</th><td>£{point.y}</td></tr>' +
        '<tr><th>Total quantity:</th><td>{point.z} units</td></tr>',
      footerFormat: '</table>',
      followPointer: true
    },

    series: [{
      data: [
      ]
    }]

  };
  function setGenericColours(data) {
    var scale = chroma.scale(['green', 'red']);
    var maxY = _.max(_.map(data.series, function(d) { return d.y }));
    var minY = _.min(_.map(data.series, function(d) { return d.y }));
    var maxRange = maxY - minY;
    _.each(data.series, function(d) {
      var ratio = (d.y - minY) / maxRange;
      d.color = scale(ratio).hex();
    });
  }

  $.getJSON(
    bubble_data_url,
    function(data) {
      setGenericColours(data);
      var options = $.extend(true, {}, highchartsOptions);
      options.series[0]['data'] = data.series;
      options.title.text = 'England-wide distribution of PPU for {{ name }}';
      options.xAxis.categories = data.categories;
      options.yAxis.plotLines[0].value = data.plotline;
      $('#all_practices_chart').highcharts(options);
    }
  );
});
