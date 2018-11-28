var $ = require('jquery');
var Highcharts = require('Highcharts');

var chartOptions = require('./highcharts-options');

$(function() {

  $('.js-submit-on-change').on('change', function() {
    this.form.submit();
  });

  function rowToPoint(row, valueKey) {
    var point = {
      date: parseDate(row.month),
      tariffCost: row.tariff_cost,
      addCost: row.additional_cost,
      isEstimate: row.is_estimate
    };
    point.x = point.date;
    point.y = point[valueKey];
    return point;
  }

  function parseDate(dateStr) {
    var parts = dateStr.split('-');
    return Date.UTC(parts[0], parts[1] - 1, parts[2]);
  }

  var data = JSON.parse(document.getElementById('monthly-totals-data').innerHTML);
  var options = chartOptions.baseOptions;
  options = JSON.parse(JSON.stringify(options));

  var additionalCosts = data.map(function(row) { return rowToPoint(row, 'addCost'); });
  var actualCosts = additionalCosts.filter(function(point) { return ! point.isEstimate; });
  var estimatedCosts = additionalCosts.filter(function(point) { return point.isEstimate; });

  options.title.text = 'Additional cost of price concessions';
  options.chart.type = 'column';
  options.chart.marginBottom = 80;
  options.legend.layout = 'horizontal';
  options.legend.align = 'right';
  options.legend.verticalAlign = 'bottom';
  options.legend.x = 0;
  options.legend.y = 0;
  options.legend.itemMarginBottom = 4;
  options.plotOptions.series = {stacking: 'normal'};
  options.yAxis.title = {enabled: true, text: 'Cost (£)'};
  options.tooltip = {
    useHTML: true,
    style: {
      pointerEvents: 'auto'
    },
    formatter: function() {
      var template =
        '<strong>{date}</strong><br>' +
        '<strong>£{value}</strong> {estimated} additional cost<br>' +
        '<a href="?breakdown_date={date_param}">View cost breakdown &rarr;</a>';
      var params = {
        '{date}': Highcharts.dateFormat('%B %Y', this.x),
        '{value}': Highcharts.numberFormat(this.y, 0),
        '{estimated}': this.point.isEstimate ? 'estimated' : '',
        '{date_param}': Highcharts.dateFormat('%Y-%m-%d', this.x)
      };
      return template.replace(/{.+?}/g, function(param) {
        return params[param];
      });
    },
    valueDecimals: 0,
    valuePrefix: '£'
  };
  options.series = [
    {name: 'Actual cost', data: actualCosts, color: 'rgba(0, 0, 255, .8)'},
    {name: 'Estimated cost', data: estimatedCosts, color: 'rgba(255, 0, 0, .8)'}
  ];
  var chart = Highcharts.chart('monthly-totals-chart', options);
});
