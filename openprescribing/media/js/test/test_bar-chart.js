var expect = require('chai').expect;
var barChart = require('../src/bar-chart');


describe('BarChart', function () {
    describe('#_indexDataByMonthAndRatio', function () {
        it('should construct the bar chart series', function () {
            var combinedData = [
              { 'ratio_actual_cost': 12, 'y_actual_cost': 105, 'x_actual_cost': 10, 'id': '03Q', 'name': 'NHS Corby', 'date': '2014-03-01'},
              { 'ratio_actual_cost': 10, 'y_actual_cost': 204, 'x_actual_cost': 11, 'id': '03V', 'name': 'NHS Vale of York', 'date': '2014-03-01'},
              { 'ratio_actual_cost': 15, 'y_actual_cost': 128, 'x_actual_cost': 12, 'id': '03Q', 'name': 'NHS Corby', 'date': '2014-04-01'},
              { 'ratio_actual_cost': 9, 'y_actual_cost': 179, 'x_actual_cost': 13, 'id': '03V', 'name': 'NHS Vale of York', 'date': '2014-04-01'}
            ];
            var indexedData = barChart._indexDataByMonthAndRatio(combinedData, ['03Q']);
            var costs = indexedData['2014-03-01'].ratio_actual_cost;
            expect(costs.length).to.equal(2);
            expect(costs[1].id).to.equal('03Q');
            expect(costs[1].y).to.equal(12);
            expect(costs[1].y_actual_cost).to.equal(105);
            expect(costs[1].x_actual_cost).to.equal(10);
            expect(costs[1].date).to.equal('2014-03-01');
        });

        it('should colour bars with active IDs', function () {
            var combinedData = [
              { 'ratio_actual_cost': 12, 'y_actual_cost': 105, 'x_actual_cost': 10, 'id': '03Q', 'name': 'NHS Corby', 'date': '2014-03-01'},
              { 'ratio_actual_cost': 10, 'y_actual_cost': 204, 'x_actual_cost': 11, 'id': '03V', 'name': 'NHS Vale of York', 'date': '2014-03-01'},
              { 'ratio_actual_cost': 15, 'y_actual_cost': 128, 'x_actual_cost': 12, 'id': '03Q', 'name': 'NHS Corby', 'date': '2014-04-01'},
              { 'ratio_actual_cost': 9, 'y_actual_cost': 179, 'x_actual_cost': 13, 'id': '03V', 'name': 'NHS Vale of York', 'date': '2014-04-01'}
            ];
            var indexedData = barChart._indexDataByMonthAndRatio(combinedData, ['03Q']);
            var costs = indexedData['2014-03-01'].ratio_actual_cost;
            expect(costs[1].color).to.equal('rgba(255, 64, 129, .8)');
            expect(costs[0].color).to.equal('rgba(119, 152, 191, .5)');
        });

        it('should sort the series by ratio_items ascending', function () {
            var combinedData = [
              { 'ratio_items': 12, 'y_actual_cost': 105, 'x_actual_cost': 10, 'id': 'O3Q', 'name': 'NHS Corby', 'date': '2014-03-01'},
              { 'ratio_items': 10, 'y_actual_cost': 204, 'x_actual_cost': 11, 'id': 'O3V', 'name': 'NHS Vale of York', 'date': '2014-03-01'},
              { 'ratio_items': 15, 'y_actual_cost': 128, 'x_actual_cost': 12, 'id': 'O3Q', 'name': 'NHS Corby', 'date': '2014-04-01'},
              { 'ratio_items': 9, 'y_actual_cost': 179, 'x_actual_cost': 13, 'id': 'O3V', 'name': 'NHS Vale of York', 'date': '2014-04-01'}
            ];
            var indexedData = barChart._indexDataByMonthAndRatio(combinedData, []);
            var items = indexedData['2014-03-01'].ratio_items;
            expect(items.length).to.equal(2);
            expect(items[0].id).to.equal('O3V');
            expect(items[0].y).to.equal(10);
        });

    });

// update
});
