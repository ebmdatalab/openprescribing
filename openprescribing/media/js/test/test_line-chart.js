var expect = require('chai').expect;
var lineChart = require('../src/line-chart');
var combinedData = [
  { 'ratio_actual_cost': 12, 'y_actual_cost': 105, 'x_actual_cost': 10, 'astro_pu_cost': 10, 'id': 'O3Q', 'name': 'NHS Corby', 'date': '2014-03-01'},
  { 'ratio_actual_cost': 10, 'y_actual_cost': 204, 'x_actual_cost': 11, 'astro_pu_cost': 11, 'id': 'O3V', 'name': 'NHS Vale of York', 'date': '2014-03-01'},
  { 'ratio_actual_cost': 15, 'y_actual_cost': 128, 'x_actual_cost': 12, 'astro_pu_cost': 12, 'id': 'O3Q', 'name': 'NHS Corby', 'date': '2014-04-01'},
  { 'ratio_actual_cost': 9, 'y_actual_cost': 179, 'x_actual_cost': 13,'astro_pu_cost': 13,  'id': 'O3V', 'name': 'NHS Vale of York', 'date': '2014-04-01'}
];

describe('LineChart', function () {
    describe('#getDataForLineChart', function () {
        it('should correctly construct the line chart series', function () {
            var chartValues = {y: "y_actual_cost", ratio: "ratio_actual_cost",
                               x_val: "x_actual_cost", x: "actual_cost"};
            var series = lineChart.getDataForLineChart(combinedData, chartValues, []);
            expect(series.length).to.equal(2);
            expect(series[0].id).to.equal('O3Q');
            expect(series[0].name).to.equal('NHS Corby');
            expect(series[0].data.length).to.equal(2);
            expect('color' in series[0]).to.equal(false);
            var dataPoint = series[0].data[0];
            expect(dataPoint.y).to.equal(12);
            expect(dataPoint.x).to.equal(1393632000000);
            expect(dataPoint.original_y).to.equal(105);
            expect(dataPoint.original_x).to.equal(10);
        });

        it('should correctly construct the line chart series for other x_val', function () {
            var chartValues = {y: "y_actual_cost", ratio: "ratio_actual_cost",
                               x_val: "astro_pu_cost", x: "astro_pu_cost"};
            var series = lineChart.getDataForLineChart(combinedData, chartValues, []);
            expect(series.length).to.equal(2);
            expect(series[0].id).to.equal('O3Q');
            expect(series[0].name).to.equal('NHS Corby');
            expect(series[0].data.length).to.equal(2);
            var dataPoint = series[0].data[0];
            expect(dataPoint.y).to.equal(12);
            expect(dataPoint.x).to.equal(1393632000000);
            expect(dataPoint.original_y).to.equal(105);
            expect(dataPoint.original_x).to.equal(10);
        });

        it('should correctly highlight any active organisations', function () {
            var chartValues = {y: "y_actual_cost", ratio: "ratio_actual_cost",
                               x_val: "x_actual_cost", x: "actual_cost"};
            var series = lineChart.getDataForLineChart(combinedData, chartValues, ['O3Q']);
            expect(series[0].color).to.equal('rgba(255, 64, 129, 0.6)');
            expect(series[0].zIndex).to.equal(1000);
            expect(series[1].color).to.equal('rgba(204, 204, 204, 0.6)');
            expect(series[1].zIndex).to.equal(1);
        });

        it('should handle an empty data array', function () {
            var series = lineChart.getDataForLineChart([], {}, []);
            expect(series.length).to.equal(0);
        });

    });
});
