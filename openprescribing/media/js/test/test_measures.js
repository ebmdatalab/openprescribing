var expect = require('chai').expect;
var mu = require('../src/measure_utils');
var _ = require('underscore');

describe('Measures', function() {
  describe('#getCentilesAndYAxisExtent', function() {
    it('should calculate global series and y-extent correctly', function() {
      var globalData = [{
        data: [
        {
          date: '2015-01-01',
          percentiles: {
            practice: {10: 46, 90: 97}
          }
        },
        {
          date: '2015-02-01',
          percentiles: {
            practice: {10: 25, 90: 82}
          }
        }
        ],
        id: 'ace'
      }
      ],
      options = {
        rollUpBy: 'org_id',
        measure: 'ace',
        orgType: 'practice'
      },
      centiles = ["10", "20", "30", "40", "50", "60", "70", "80", "90"];
      var result = mu.getCentilesAndYAxisExtent(globalData, options, centiles);
      expect(result.globalYMax.y).to.equal(97);
      expect(result.globalYMin.y).to.equal(25);
      expect(result.globalCentiles['10'][0].x).to.equal(1420070400000);
      expect(result.globalCentiles['10'][0].y).to.equal(46);
      expect(result.globalCentiles['90'][0].x).to.equal(1420070400000);
      expect(result.globalCentiles['90'][0].y).to.equal(97);
    });

    it('should do nothing when the charts are multiple measures', function() {
      var globalData = [],
      options = {
        rollUpBy: 'measure_id'
      },
      centiles = ["10", "20", "30", "40", "50", "60", "70", "80", "90"];
      var result = mu.getCentilesAndYAxisExtent(globalData, options, centiles);
      expect(result.globalYMax).to.equal(0);
      expect(result.globalYMin).to.equal(0);
    });
  });

  describe('annotateData', function () {
    it('rolls up by organisation and calculates means', function() {
      var org_data = [{
        data: [
          {
            pct_id: '04N',
            pct_name: 'NHS RUSHCLIFFE CCG',
            date: '2015-01-01',
            calc_value: 8,
            percentile: 20
          },
          {
            pct_id: '04N',
            pct_name: 'NHS RUSHCLIFFE CCG',
            date: '2015-02-01',
            calc_value: 9,
            percentile: 21
          },
          {
            pct_id: '03V',
            pct_name: 'NHS CORBY CCG',
            date: '2015-01-01',
            calc_value: 10,
            percentile: 40
          },
          {
            pct_id: '03V',
            pct_name: 'NHS CORBY CCG',
            date: '2015-02-01',
            calc_value: 12,
            percentile: 37
          },
          {
            pct_id: '99P',
            pct_name: 'NHS NORTH, EAST AND WEST DEVON CCG',
            date: '2015-01-01',
            calc_value: null,
            percentile: null
          },
          {
            pct_id: '99P',
            pct_name: 'NHS NORTH, EAST AND WEST DEVON CCG',
            date: '2015-02-01',
            calc_value: null,
            percentile: null
          }
        ],
        id:"ace",
        is_cost_based: true,
        is_percentage: true,
        name: "High-cost ACE inhibitors",
        numerator_short: "High-cost ACEs quantity",
        title: "TBA"
      }];
      var summarise_months = 6;
      var result = mu.annotateData(
        org_data,
        { rollUpBy: 'org_id', orgType: 'ccg'}, summarise_months);
      expect(result.length).to.equal(3);
      var corby = _.findWhere(result, {name: 'NHS CORBY CCG'});
      expect(corby.meanPercentile).to.equal(38.5);
      expect(corby.isPercentage).to.be.true;
      expect(corby.data.length).to.equal(2);
      var devon = _.findWhere(result, {name: 'NHS NORTH, EAST AND WEST DEVON CCG'});
      expect(devon.meanPercentile).to.equal(null);
      expect(devon.isPercentage).to.be.true;
      expect(devon.data.length).to.equal(2);
    });
  });

  describe('sortData', function () {
    it("sorts as expected", function () {
      var data = [
        {
          id: 1,
          meanPercentile: 40,
          lowIsGood: true
        },
        {
          id: 2,
          meanPercentile: 60,
          lowIsGood: true
        },
        {
          id: 3,
          meanPercentile: 50,
          lowIsGood: false
        },
        {
          id: 4,
          meanPercentile: 50,
          lowIsGood: true
        },
        {
          id: 5,
          meanPercentile: 40,
          lowIsGood: false,
        },
        {
          id: 6,
          meanPercentile: null,
          lowIsGood: false
        },
        {
          id: 7,
          meanPercentile: 40,
          lowIsGood: null
        }
      ];
      var result = mu.sortData(data);
      var positions = _.map(result, function(d) {return d.id});
      expect(positions).to.eql([2,5,3,4,1,7,6]);
    });
  });

  describe('#_rollUpByOrg', function() {
    it('rolls up by CCG', function() {
      var data = {
        data: [
        {
          pct_id: '04N',
          pct_name: 'NHS RUSHCLIFFE CCG',
          date: '2015-01-01',
          calc_value: 8
        },
        {
          pct_id: '04N',
          pct_name: 'NHS RUSHCLIFFE CCG',
          date: '2015-02-01',
          calc_value: 9
        },
        {
          pct_id: '03V',
          pct_name: 'NHS CORBY CCG',
          date: '2015-01-01',
          calc_value: 10
        },
        {
          pct_id: '03V',
          pct_name: 'NHS CORBY CCG',
          date: '2015-02-01',
          calc_value: 12
        }
        ],
        id:"ace",
        is_cost_based: true,
        is_percentage: true,
        name: "High-cost ACE inhibitors",
        numerator_short: "High-cost ACEs quantity",
        title: "TBA"
      };
      var result = mu._rollUpByOrg(data, 'CCG');
      expect(result.length).to.equal(2);
      expect(result[0].data[0].date).to.equal('2015-01-01');
    });

    it('rolls up by practice', function() {
      var data = {
        data: [
        {
          practice_id: 'A81001',
          practice_name: 'foo',
          date: '2015-01-01',
          calc_value: 8
        },
        {
          practice_id: 'A81001',
          practice_name: 'foo',
          date: '2015-02-01',
          calc_value: 9
        },
        {
          practice_id: 'A81002',
          practice_name: 'bar',
          date: '2015-01-01',
          calc_value: 10
        },
        {
          practice_id: 'A81002',
          practice_name: 'bar',
          date: '2015-02-01',
          calc_value: 12
        }
        ],
        id:"ace",
        is_cost_based: true,
        is_percentage: true,
        name: "High-cost ACE inhibitors",
        numerator_short: "High-cost ACEs quantity",
        title: "TBA"
      };
      var result = mu._rollUpByOrg(data, 'practice');
      expect(result.length).to.equal(2);
      expect(result[0].data[0].date).to.equal('2015-01-01');
    });
  });

  describe('#_getSavingAndPercentilePerItem', function() {

    it('should get mean cost saving and percentile across last N months', function() {
      var data = [{
        data: [
        {date: '2015-01-01', percentile: 21, cost_savings: { 10: 1, 50: 7 }},
        {date: '2015-02-01', percentile: 22, cost_savings: { 10: 1, 50: 7 }},
        {date: '2015-03-01', percentile: 19, cost_savings: { 10: 1, 50: 7 }},
        {date: '2015-04-01', percentile: 16, cost_savings: { 10: 1, 50: 7 }},
        {date: '2015-05-01', percentile: 15, cost_savings: { 10: 1, 50: 7 }},
        {date: '2015-06-01', percentile: 19, cost_savings: { 10: 1, 50: 12 }},
        {date: '2015-07-01', percentile: 18, cost_savings: { 10: 1, 50: 81 }},
        {date: '2015-08-01', percentile: 16, cost_savings: { 10: 1, 50: 12.8 }},
        {date: '2015-09-01', percentile: 13, cost_savings: { 10: 1, 50: 12.4 }},
        {date: '2015-10-01', percentile: 12, cost_savings: { 10: 1, 50: 10 }},
        {date: '2015-11-01', percentile: 12, cost_savings: { 10: 1, 50: 8 }},
        {date: '2015-12-01', percentile: 7, cost_savings: { 10: 1, 50: 7 }},
        ]
      }];
      var result = mu._getSavingAndPercentilePerItem(data, 6);
      expect(result[0].meanPercentile).to.equal(13);
      expect(result[0].costSaving10th).to.equal(6);
      expect(result[0].costSaving50th).to.equal(131.2);
    });

    it('should handle intermittent null elements correctly', function() {
      var data = [{
        data: [
        {date: '2015-07-01', percentile: 2, cost_savings: { 50: -20 }},
        {date: '2015-08-01', percentile: null, cost_savings: null},
        {date: '2015-09-01', percentile: 3, cost_savings: { 50: -10 }},
        {date: '2015-10-01', percentile: 2, cost_savings: { 50: -10 }},
        {date: '2015-11-01', percentile: 0, cost_savings: { 50: -10 }},
        {date: '2015-12-01', percentile: 4, cost_savings: { 50: -10 }},
        ]
      }];
      var result = mu._getSavingAndPercentilePerItem(data, 6);
      expect(result[0].meanPercentile).to.equal(11/5);
      expect(result[0].costSaving50th).to.equal(-60);
    });

    it('should handle entirely null data correctly', function() {
      var data = [{
        data: [
        {date: '2015-07-01', percentile: null, cost_savings: null},
        {date: '2015-08-01', percentile: null, cost_savings: null},
        {date: '2015-09-01', percentile: null, cost_savings: null},
        {date: '2015-10-01', percentile: null, cost_savings: null},
        {date: '2015-11-01', percentile: null, cost_savings: null},
        {date: '2015-12-01', percentile: null, cost_savings: null},
        ]
      }];
      var result = mu._getSavingAndPercentilePerItem(data, 6);
      expect(result[0].meanPercentile).to.equal(null);
      expect(result[0].costSaving50th).to.equal(0);
    });

    it('should handle a short data array', function() {
      var data = [{
        data: [
        {date: '2015-10-01', percentile: 12, cost_savings: { 50: 10 }},
        {date: '2015-11-01', percentile: 12, cost_savings: { 50: 8 }},
        {date: '2015-12-01', percentile: 6, cost_savings: { 50: 7 }},
        ]
      }];
      var result = mu._getSavingAndPercentilePerItem(data, 6);
      expect(result[0].meanPercentile).to.equal(10);
      expect(result[0].costSaving50th).to.equal(25);
    });

    it('should handle an empty data array', function() {
      var data = [{
        data: []
      }];
      var result = mu._getSavingAndPercentilePerItem(data, 6);
      expect(result[0].data.length).to.equal(0);
    });
  });

  describe('#getPerformanceSummary', function() {
    it('handles empty data', function() {
      var options = {
        rollUpBy: 'org_id',
        isCostBasedMeasure: true,
        orgId: null,
        orgType: 'CCG',
        measure: 'ace'
      };
      var result = mu.getPerformanceSummary([], options, null);
      var str = "This organisation hasn't prescribed on any of these measures.";
      expect(result.performanceDescription).to.equal(str);
    });

  });

  describe('#addChartAttributes', function() {
    it('should not error when a given measure is missing', function () {
      var data = [{
        'data': [],
        'isPercentage': false,
        'id': 'somethingMissing',
      }];
      expect(
        function () {
          mu.addChartAttributes(
            data, [], [], [], {'orgType': '', 'rollUpBy': 'measure_id'}, 0);
        }).to.not.throw(TypeError);
    });

    it('copies selected properties from the global data', function() {
      var data = [{id: 'ace', data: []}],
      globalData = [{id: 'ace', low_is_good: true, numerator_is_list_of_bnf_codes: true}],
      globalCentiles = [],
      centiles = [],
      options = {rollUpBy: 'measure_id'};
      var result = mu.addChartAttributes(data, globalData, globalCentiles,
        centiles, options, 6);
      expect(result[0].lowIsGood).to.be.true;
      expect(result[0].numeratorCanBeQueried).to.be.true;
    });
  });

  describe('#_addHighchartsXAndY', function() {
    it('should convert global data correctly', function() {
      var data = [
      { date: '2015-01-01', percentiles: { 'ccg': { '10': 2.1} }},
      { date: '2015-02-01', percentiles: { 'ccg': { '10': 2.4} }},
      { date: '2015-03-01', percentiles: { 'ccg': { '10': 2.2} }}
      ];
      var options = {'orgType': 'ccg'};
      var result = mu._addHighchartsXAndY(data, true, false, options, '10');
      expect(result.length).to.equal(3);
      expect(result[0].x).to.equal(1420070400000);
      expect(result[0].y).to.equal(2.1);
    });

    it('should multiply percentages by 100 for display purposes', function() {
      var data = [
      { date: '2015-01-01', calc_value: '0.08'},
      { date: '2015-02-01', calc_value: '0.04'},
      { date: '2015-03-01', calc_value: '0.05'}
      ];
      var options = {};
      var result = mu._addHighchartsXAndY(data, false, true, options, null);
      expect(result.length).to.equal(3);
      expect(result[0].x).to.equal(1420070400000);
      expect(result[0].y).to.equal(8);
    });
  });

  describe('#_getChartOptions', function() {

    it('sets correct Highcharts options for % measures', function() {
      var d = {
        data: [{x: 0, y: 60}, {x: 10, y: 0}],
        numeratorShort: 'foo',
        denominatorShort: 'bar'
      },
      options = {
        rollUpBy: 'org_id',
        globalYMax: {y: 100},
        globalYMin: {y: 10}
      },
      chartOptions = {dashOptions: { chart: {}, legend: {}}};
      var result = mu._getChartOptions(d, true,
        options, chartOptions);
      expect(result.yAxis.title.text).to.equal('%');
      expect(result.yAxis.min).to.equal(0);
      expect(result.yAxis.max).to.equal(100);
      var point = {
        x: '2015-01-01',
        point: {
          numerator: 10,
          denominator: 30,
          percentile: 60,
          y: 0.3333333
        },
        series: {
          name: 'Foo',
          options: {
            isNationalSeries: true,
            showTooltip: false
          }
        }
      };
      var tooltip = result.tooltip.formatter.call(point);
      expect(tooltip).to.equal(false);

      var point = {
        x: '2015-01-01',
        point: {
          numerator: 10,
          denominator: 30,
          percentile: 60,
          y: 0.3333333
        },
        series: {
          name: 'Foo',
          options: {
            isNationalSeries: false,
            showTooltip: true
          }
        }
      };
      var tooltip = result.tooltip.formatter.call(point);
      var str = '<b>Foo in Jan 2015</b><br/>foo: 10<br/>bar: 30<br/>Measure: 0.333% (60th percentile)';
      expect(tooltip).to.equal(str);
    });

    it('reverses the yAxis when low is bad', function() {
      var d = {
        lowIsGood: false,
        data: [{x: 0, y: 60}, {x: 10, y: 0}]
      },
      options = {
        rollUpBy: 'org_id',
        globalYMax: {y: 100},
        globalYMin: {y: 10}
      },
      chartOptions = {dashOptions: { chart: {}, legend: {}}};
      var result = mu._getChartOptions(d, true,
        options, chartOptions);
      expect(result.yAxis.reversed).to.equal(true);
      d.lowIsGood = true;
      result = mu._getChartOptions(d, true,
        options, chartOptions);
      expect(result.yAxis.reversed).not.to.equal(true);
    });

    it('does not reverse the yAxis when low_is_good is null', function() {
      var d = {
        lowIsGood: null,
        data: [{x: 0, y: 60}, {x: 10, y: 0}]
      },
      options = {
        rollUpBy: 'org_id',
        globalYMax: {y: 100},
        globalYMin: {y: 10}
      },
      chartOptions = {dashOptions: { chart: {}, legend: {}}};
      var result = mu._getChartOptions(d, true,
        options, chartOptions);
      expect(result.yAxis.reversed).to.be.undefined;
    });

    it('sets correct Highcharts options for non-% measures', function() {
      var d = {
        data: [{x: 0, y: 90}, {x: 10, y: 10}],
        numeratorShort: 'foo',
        denominatorShort: 'bar'
      },
      options = {
        rollUpBy: 'org_id',
        globalYMax: { y: 50},
        globalYMin: { y: 0}
      },
      chartOptions = { dashOptions: { chart: {}, legend: {}}};
      var result = mu._getChartOptions(d, false,
        options, chartOptions);
      expect(result.yAxis.title.text).to.equal('Measure');
      expect(result.yAxis.min).to.equal(0);
      expect(result.yAxis.max).to.equal(90);
      var point = {
        x: '2015-01-01',
        point: {
          numerator: 10,
          denominator: 30,
          percentile: 60,
          y: 0.3333333
        },
        series: {
          name: 'Bar',
          options: {
            isNationalSeries: false,
            showTooltip: true
          }
        }
      };
      var tooltip = result.tooltip.formatter.call(point);
      var str = '<b>Bar in Jan 2015</b><br/>foo: 10<br/>';
      str += 'bar: 30<br/>Measure: 0.333 (60th percentile)';
      expect(tooltip).to.equal(str);
    });
  });

  describe('#getGraphOptions', function() {
    it('should amalgamate the series correctly', function() {
      var d = {
        data: [{x: 0, y: 12}, {x: 10, y: 10}],
        numeratorShort: 'foo',
        denominatorShort: 'bar',
        globalCentiles: {
          10: [{ x: 0, y: 2}, { x: 10, y: 3}],
          50: [{ x: 0, y: 45}, { x: 10, y: 46}],
          90: [{ x: 0, y: 88}, { x: 10, y: 92}],
        }
      },
      options = {
        orgId: '99P',
        orgType: 'CCG',
        rollUpBy: 'org_id',
        globalYMax: { y: 50},
        globalYMin: { y: 0}
      },
      chartOptions = { dashOptions: { chart: {}, legend: {}}};
      var result = mu.getGraphOptions(d, options, true, chartOptions);
      expect(result.series.length).to.equal(4);
      expect(result.series[0].name).to.equal('This CCG');
      expect(result.series[2].name).to.equal('50th percentile nationally');
      expect(result.series[2].isNationalSeries).to.equal(true);
      expect(result.series[2].dashStyle).to.equal('longdash');

    });
  });

  describe('#getChartDataAsTable', function() {
    it('returns chart data in tabular form', function() {
      var result = mu.getChartDataAsTable({
        "chartId": "ktt9_uti_antibiotics",
        "chartTitle": "Antibiotic stewardship: three-day courses for uncomplicated UTIs",
        "orgType": "CCG",
        "data": [
          {
            "denominator": 1744,
            "numerator": 11627.8333333333,
            "percentile": 97.5961538461538,
            "calc_value": 6.66733562691132,
            "pct_id": "99E",
            "pct_name": "NHS BASILDON AND BRENTWOOD CCG",
            "date": "2017-01-01",
          },
          {
            "denominator": 1615,
            "numerator": 10641.5,
            "percentile": 97.5961538461538,
            "calc_value": 6.58916408668731,
            "pct_id": "99E",
            "pct_name": "NHS BASILDON AND BRENTWOOD CCG",
            "date": "2017-02-01"
          },
          {
            "denominator": 1822,
            "numerator": 12102.9166666667,
            "percentile": 98.0769230769231,
            "calc_value": 6.64265459202342,
            "pct_id": "99E",
            "pct_name": "NHS BASILDON AND BRENTWOOD CCG",
            "date": "2017-03-01"
          }
        ],
        "globalCentiles": {
          "10": [
            {
              "y": 5.182546810483497,
              "date": "2017-01-01"
            },
            {
              "y": 5.214408749095638,
              "date": "2017-02-01"
            },
            {
              "y": 5.248553447914695,
              "date": "2017-03-01"
            }
          ],
          "20": [
            {
              "y": 5.4174508079030925,
              "date": "2017-01-01"
            },
            {
              "y": 5.413822826078597,
              "date": "2017-02-01"
            },
            {
              "y": 5.4361293677134706,
              "date": "2017-03-01"
            }
          ],
          "30": [
            {
              "y": 5.518345114305625,
              "date": "2017-01-01"
            },
            {
              "y": 5.575019921790236,
              "date": "2017-02-01"
            },
            {
              "y": 5.572179441817108,
              "date": "2017-03-01"
            }
          ],
          "50": [
            {
              "y": 5.7430555555555545,
              "date": "2017-01-01"
            },
            {
              "y": 5.7453920649796935,
              "date": "2017-02-01"
            },
            {
              "y": 5.7919745484400655,
              "date": "2017-03-01"
            }
          ],
          "40": [
            {
              "y": 5.63159773123116,
              "date": "2017-01-01"
            },
            {
              "y": 5.670616327418811,
              "date": "2017-02-01"
            },
            {
              "y": 5.702130340910575,
              "date": "2017-03-01"
            }
          ],
          "60": [
            {
              "y": 5.878912354447853,
              "date": "2017-01-01"
            },
            {
              "y": 5.85411959737778,
              "date": "2017-02-01"
            },
            {
              "y": 5.880026704460748,
              "date": "2017-03-01"
            }
          ],
          "70": [
            {
              "y": 5.964220413424124,
              "date": "2017-01-01"
            },
            {
              "y": 5.937731172383994,
              "date": "2017-02-01"
            },
            {
              "y": 5.9794797683156915,
              "date": "2017-03-01"
            }
          ],
          "90": [
            {
              "y": 6.284994437637084,
              "date": "2017-01-01"
            },
            {
              "y": 6.323238055692184,
              "date": "2017-02-01"
            },
            {
              "y": 6.296265612219995,
              "date": "2017-03-01"
            }
          ],
          "80": [
            {
              "y": 6.088481618366197,
              "date": "2017-01-01"
            },
            {
              "y": 6.160359753080579,
              "date": "2017-02-01"
            },
            {
              "y": 6.119981581449648,
              "date": "2017-03-01"
            }
          ]
        }
      });
      expect(result).to.deep.equal([
        ['date', 'org_id', 'org_name', 'numerator', 'denominator', 'ratio', 'percentile',
          '10th percentile', '20th percentile', '30th percentile', '40th percentile',
          '50th percentile', '60th percentile', '70th percentile', '80th percentile',
          '90th percentile'],
        ['2017-01-01', '99E', 'NHS BASILDON AND BRENTWOOD CCG',
          11627.8333333333, 1744, 6.66733562691132, 97.5961538461538,
          5.182546810483497, 5.4174508079030925, 5.518345114305625, 5.63159773123116,
          5.7430555555555545, 5.878912354447853, 5.964220413424124, 6.088481618366197,
          6.284994437637084],
        ['2017-02-01', '99E', 'NHS BASILDON AND BRENTWOOD CCG', 10641.5, 1615,
          6.58916408668731, 97.5961538461538,
          5.214408749095638, 5.413822826078597, 5.575019921790236,
          5.670616327418811, 5.7453920649796935, 5.85411959737778,
          5.937731172383994, 6.160359753080579, 6.323238055692184],
        ['2017-03-01', '99E', 'NHS BASILDON AND BRENTWOOD CCG',
          12102.9166666667, 1822, 6.64265459202342, 98.0769230769231,
          5.248553447914695, 5.4361293677134706, 5.572179441817108,
          5.702130340910575, 5.7919745484400655, 5.880026704460748,
          5.9794797683156915, 6.119981581449648, 6.296265612219995]
      ]);
    });
  });
});
