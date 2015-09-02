var expect = require('chai').expect;
global.window = require("jsdom")
                  .jsdom()
                  .parentWindow;
global.document = window.document;
var Dashboard = require('../dashboard');


// describe('Dashboard', function () {
//     describe('#convertData', function () {
//         it('should calculate the x and y value', function () {
//             var combinedData = [
//               { 'ratio_actual_cost': 12, 'y_actual_cost': 105, 'x_actual_cost': 10, 'id': '03Q', 'name': 'NHS Corby', 'date': '2014-03-01'},
//               { 'ratio_actual_cost': 10, 'y_actual_cost': 204, 'x_actual_cost': 11, 'id': '03V', 'name': 'NHS Vale of York', 'date': '2014-03-01'},
//               { 'ratio_actual_cost': 15, 'y_actual_cost': 128, 'x_actual_cost': 12, 'id': '03Q', 'name': 'NHS Corby', 'date': '2014-04-01'},
//               { 'ratio_actual_cost': 9, 'y_actual_cost': 179, 'x_actual_cost': 13, 'id': '03V', 'name': 'NHS Vale of York', 'date': '2014-04-01'}
//             ];
//             var data = Dashboard.convertData(combinedData);
//             expect(data.length).to.equal(2);
//             expect(data[1].x).to.equal('03Q');
//             expect(data[1].y).to.equal(12);
//         });
//     });
// });