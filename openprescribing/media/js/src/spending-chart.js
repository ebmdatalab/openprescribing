var $ = require('jquery');
var Highcharts = require('Highcharts');
var downloadjs = require('downloadjs');

var chartOptions = require('./highcharts-options');
var csvUtils = require('./csv-utils');


function downloadCSVData(name, headers, rows) {
  var table = [headers].concat(rows);
  var csvData = csvUtils.formatTableAsCSV(table);
  var filename = csvUtils.getFilename(name);
  downloadjs(csvData, filename, 'text/csv');
  return false;
}


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


$(function() {
  var breakdownData = JSON.parse(document.getElementById('breakdown-data').innerHTML);
  if ( ! breakdownData) return;
  var $wrapper = $('#breakdown-table-wrapper');
  var urlTemplate = breakdownData.url_template;
  $wrapper.find('table').DataTable({
    data: breakdownData.table,
    pageLength: 25,
    order: [],
    columnDefs: [
      {targets: [0], visible: false},
      {
        targets: [1],
        render: function(data, type, row) {
          return '<a href="'+urlTemplate.replace('{bnf_code}', row[0])+'">'+data+'</a>';
        }
      },
      {targets: [2, 3, 4], className: "text-right"},
      {
        targets: [2],
        render: $.fn.dataTable.render.number(',', '.', 0, '' )
      },
      {
        targets: [3, 4],
        render: $.fn.dataTable.render.number(',', '.', 0, '£' )
      }
    ]
  });
  $wrapper.find('.js-download-data').on('click', function() {
    return downloadCSVData(
      breakdownData.filename,
      ['BNF Code', 'Presentation', 'Quantity', 'Tariff Cost', 'Additional Cost'],
      breakdownData.table
    );
  });
  $wrapper.removeClass('hide');
});
