import { describe, expect, it } from "vitest";
import utils from "../src/chart_utils";

describe("Utils", () => {
  describe("#constructQueryURLs", () => {
    it("should correctly construct urls", () => {
      const options = {
        org: "practice",
        orgIds: [{ id: "Y020405" }],
        num: "chemical",
        numIds: [{ id: "1234" }, { id: "5678" }],
        denom: "chemical",
        denomIds: [{ id: "9876" }],
      };
      const urls = utils.constructQueryURLs(options);
      expect(urls.numeratorUrl).to.equal(
        "/api/1.0/spending_by_org/?format=json&org_type=practice&code=1234,5678&org=Y020405"
      );
      expect(urls.denominatorUrl).to.equal(
        "/api/1.0/spending_by_org/?format=json&org_type=practice&code=9876&org=Y020405"
      );
    });
    it("should correctly construct urls for all spending", () => {
      const options = {
        org: "all",
        orgIds: [],
        num: "chemical",
        numIds: [{ id: "1234" }, { id: "5678" }],
        denom: "chemical",
        denomIds: [{ id: "9876" }],
      };
      const urls = utils.constructQueryURLs(options);
      expect(urls.numeratorUrl).to.equal(
        "/api/1.0/spending/?format=json&code=1234,5678"
      );
      expect(urls.denominatorUrl).to.equal(
        "/api/1.0/spending/?format=json&code=9876"
      );
    });
    it("should correctly construct urls for ASTRO-PU", () => {
      const options = {
        org: "practice",
        orgIds: [{ id: "Y020405" }, { id: "J04052" }],
        num: "chemical",
        numIds: [{ id: "1234" }, { id: "5678" }],
        denom: "astro_pu_cost",
        denomIds: [{ id: "9876" }, { id: "5678" }],
      };
      const urls = utils.constructQueryURLs(options);
      expect(urls.numeratorUrl).to.equal(
        "/api/1.0/spending_by_org/?format=json&org_type=practice&code=1234,5678&org=Y020405,J04052"
      );
      expect(urls.denominatorUrl).to.equal(
        "/api/1.0/org_details/?format=json&org_type=practice&keys=astro_pu_cost&org=Y020405,J04052"
      );
    });
    it("should correctly construct urls for list size", () => {
      const options = {
        org: "CCG",
        orgIds: [{ id: "03V" }, { id: "03Q" }],
        num: "chemical",
        numIds: [{ id: "1234" }, { id: "5678" }],
        denom: "total_list_size",
        denomIds: [{ id: "9876" }, { id: "5678" }],
      };
      const urls = utils.constructQueryURLs(options);
      expect(urls.numeratorUrl).to.equal(
        "/api/1.0/spending_by_org/?format=json&org_type=ccg&code=1234,5678"
      );
      expect(urls.denominatorUrl).to.equal(
        "/api/1.0/org_details/?format=json&org_type=ccg&keys=total_list_size"
      );
    });
  });

  describe("_idsToString", () => {
    it("should chain arrays of IDs nicely", () => {
      const str = [{ id: "123" }, { id: "456" }];
      const output = utils.idsToString(str);
      expect(output).to.eql("123,456");
    });
    it("should handle empty arrays nicely", () => {
      const str = [];
      const output = utils.idsToString(str);
      expect(output).to.eql("");
    });
  });

  describe("#combineXAndYDatasets", () => {
    it("should fail gracefully with two empty datasets", () => {
      const xData = [];
      const yData = [];
      const opts = {
        chartValues: {
          y: "actual_cost",
          ratio: "ratio_actual_cost",
          x: "actual_cost",
          x_val: "actual_cost",
        },
      };
      const combinedData = utils.combineXAndYDatasets(xData, yData, opts);
      expect(combinedData).to.eql([]);
    });
    it("should hide outliers where ratio is greater than 1000", () => {
      const xData = [
        {
          actual_cost: "1",
          items: 1,
          row_id: "XXX",
          row_name: "XXX",
          date: "2014-03-01",
        },
        {
          actual_cost: "1000",
          items: 1000,
          row_id: "YY1",
          row_name: "YYY",
          date: "2014-03-01",
        },
        {
          actual_cost: "1000",
          items: 1000,
          row_id: "YY2",
          row_name: "YYY",
          date: "2014-03-01",
        },
        {
          actual_cost: "1000",
          items: 1000,
          row_id: "YY3",
          row_name: "YYY",
          date: "2014-03-01",
        },
        {
          actual_cost: "1000",
          items: 1000,
          row_id: "YY4",
          row_name: "YYY",
          date: "2014-03-01",
        },
      ];
      const yData = [
        {
          actual_cost: "1000",
          items: 1000,
          row_id: "XXX",
          row_name: "XXX",
          date: "2014-03-01",
        },
        {
          actual_cost: "1",
          items: 1,
          row_id: "YY1",
          row_name: "YYY",
          date: "2014-03-01",
        },
        {
          actual_cost: "1",
          items: 1,
          row_id: "YY2",
          row_name: "YYY",
          date: "2014-03-01",
        },
        {
          actual_cost: "1",
          items: 1,
          row_id: "YY3",
          row_name: "YYY",
          date: "2014-03-01",
        },
        {
          actual_cost: "1",
          items: 1,
          row_id: "YY4",
          row_name: "YYY",
          date: "2014-03-01",
        },
      ];
      const opts = {
        denom: "total_list_size",
        hideOutliers: true,
        chartValues: {
          y: "y_actual_cost",
          ratio: "ratio_actual_cost",
          x: "actual_cost",
          x_val: "x_actual_cost",
        },
      };
      const combinedData = utils.combineXAndYDatasets(xData, yData, opts);
      expect(combinedData.length).to.equal(4);
    });
    it("should combine multiple datasets properly", () => {
      const yData = [
        {
          actual_cost: "480",
          items: 1,
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-03-01",
        },
        {
          actual_cost: "320",
          items: 2,
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-03-01",
        },
        {
          actual_cost: "415",
          items: 3,
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-04-01",
        },
        {
          actual_cost: "325",
          items: 4,
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-04-01",
        },
      ];
      const xData = [
        {
          actual_cost: "12",
          items: 0,
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-03-01",
        },
        {
          actual_cost: "10",
          items: 1,
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-03-01",
        },
        {
          actual_cost: "15",
          items: 2,
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-04-01",
        },
        {
          actual_cost: "9",
          items: 3,
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-04-01",
        },
      ];
      const opts = {
        chartValues: {
          y: "y_actual_cost",
          ratio: "ratio_actual_cost",
          x: "actual_cost",
          x_val: "x_actual_cost",
        },
      };
      const combinedData = utils.combineXAndYDatasets(xData, yData, opts);
      expect(combinedData.length).to.equal(4);
      expect(combinedData[0].row_id).to.equal("O3Q");
      expect(combinedData[0].row_name).to.equal("NHS Corby");
      expect(combinedData[0].name).to.equal("NHS Corby (O3Q)");
      expect(combinedData[0].id).to.equal("O3Q");
      expect(combinedData[0].date).to.equal("2014-03-01");
      expect(combinedData[0].y_actual_cost).to.equal(480);
      expect(combinedData[0].x_actual_cost).to.equal(12);
      expect(combinedData[0].y_items).to.equal(1);
      expect(combinedData[0].x_items).to.equal(0);
      expect(combinedData[0].ratio_actual_cost).to.equal((480 / 12) * 1000);
      expect(combinedData[0].ratio_items).to.equal(null);
    });
    it("should combine datasets with missing rows and with total_list_size denominator", () => {
      const xData = [
        {
          total_list_size: "12",
          setting: 4,
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-03-01",
        },
        {
          total_list_size: "10",
          setting: 4,
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-03-01",
        },
      ];
      const yData = [
        {
          actual_cost: "480",
          items: "15",
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-03-01",
        },
        {
          actual_cost: "500",
          items: "11",
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-04-01",
        },
      ];
      const opts = {
        chartValues: {
          y: "y_actual_cost",
          x: "total_list_size",
          x_val: "total_list_size",
          ratio: "ratio_actual_cost",
        },
      };
      const combinedData = utils.combineXAndYDatasets(xData, yData, opts);
      expect(combinedData.length).to.equal(3);

      expect(combinedData[0].row_id).to.equal("O3V");
      expect(combinedData[0].date).to.equal("2014-03-01");
      expect(combinedData[0].y_actual_cost).to.equal(0);
      expect(combinedData[0].y_items).to.equal(0);
      expect(combinedData[0].total_list_size).to.equal(10);
      expect(combinedData[0].ratio_actual_cost).to.equal(0);
      expect(combinedData[0].ratio_items).to.equal(0);

      expect(combinedData[1].row_id).to.equal("O3Q");
      expect(combinedData[1].date).to.equal("2014-03-01");
      expect(combinedData[1].y_actual_cost).to.equal(480);
      expect(combinedData[1].y_items).to.equal(15);
      expect(combinedData[1].x_items).to.equal(0);
      expect(combinedData[1].x_actual_cost).to.equal(0);
      expect(combinedData[1].total_list_size).to.equal(12);
      expect(combinedData[1].ratio_actual_cost).to.equal((480 / 12) * 1000);
      expect(combinedData[1].ratio_items).to.equal((15 / 12) * 1000);

      expect(combinedData[2].row_id).to.equal("O3V");
      expect(combinedData[2].date).to.equal("2014-04-01");
      expect(combinedData[2].y_actual_cost).to.equal(500);
      expect(combinedData[2].total_list_size).to.equal(0);
      expect(combinedData[2].ratio_actual_cost).to.equal(null);
      expect(combinedData[2].ratio_items).to.equal(null);
    });
    it("should combine datasets with STAR-PU denominator", () => {
      const xData = [
        {
          star_pu: { oral_antibacterials_item: "12" },
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-03-01",
        },
        {
          star_pu: { oral_antibacterials_item: "10" },
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-03-01",
        },
      ];
      const yData = [
        {
          actual_cost: "480",
          items: "15",
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-03-01",
        },
        {
          actual_cost: "500",
          items: "11",
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-04-01",
        },
      ];
      const opts = {
        chartValues: {
          y: "y_actual_cost",
          x: "star_pu.oral_antibacterials_item",
          x_val: "star_pu.oral_antibacterials_item",
          ratio: "ratio_actual_cost",
        },
      };
      const combinedData = utils.combineXAndYDatasets(xData, yData, opts);
      expect(combinedData.length).to.equal(3);

      expect(combinedData[1].row_id).to.equal("O3Q");
      expect(combinedData[1].date).to.equal("2014-03-01");
      expect(combinedData[1].y_items).to.equal(15);
      expect(combinedData[1]["star_pu.oral_antibacterials_item"]).to.equal(12);
      expect(combinedData[1].ratio_items).to.equal((15 / 12) * 1000);

      expect(combinedData[0].row_id).to.equal("O3V");
      expect(combinedData[0].date).to.equal("2014-03-01");
      expect(combinedData[0].y_items).to.equal(0);
      expect(combinedData[0]["star_pu.oral_antibacterials_item"]).to.equal(10);
      expect(combinedData[0].ratio_items).to.equal(0);

      expect(combinedData[2].row_id).to.equal("O3V");
      expect(combinedData[2].date).to.equal("2014-04-01");
      expect(combinedData[2].y_items).to.equal(11);
      expect(combinedData[2]["star_pu.oral_antibacterials_item"]).to.equal(0);
      expect(combinedData[2].ratio_items).to.equal(null);
    });
    it('should not multiply Y by 1,000 for "nothing" denominator', () => {
      const xData = [
        {
          nothing: 1,
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-03-01",
        },
      ];
      const yData = [
        {
          actual_cost: "480",
          items: "15",
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-03-01",
        },
      ];
      const opts = {
        chartValues: {
          y: "y_actual_cost",
          x: "nothing",
          x_val: "nothing",
          ratio: "nothing",
        },
      };
      const combinedData = utils.combineXAndYDatasets(xData, yData, opts);
      expect(combinedData[0].y_actual_cost).to.equal(480);
      expect(combinedData[0].ratio_actual_cost).to.equal(480);
    });
    it("should exclude rows with non-standard settings", () => {
      const xData = [
        {
          star_pu: { oral_antibacterials_item: "12" },
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-03-01",
        },
        {
          star_pu: { oral_antibacterials_item: "10" },
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-03-01",
        },
      ];
      const yData = [
        {
          actual_cost: "480",
          setting: 4,
          items: "15",
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-03-01",
        },
        {
          actual_cost: "500",
          setting: 3,
          items: "11",
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-04-01",
        },
      ];
      const opts = {
        chartValues: {
          y: "y_actual_cost",
          x: "star_pu.oral_antibacterials_item",
          x_val: "star_pu.oral_antibacterials_item",
          ratio: "ratio_actual_cost",
        },
      };
      const combinedData = utils.combineXAndYDatasets(xData, yData, opts);
      expect(combinedData.length).to.equal(2);
      expect(combinedData[1].row_id).to.equal("O3Q");
      expect(combinedData[1].date).to.equal("2014-03-01");
      expect(combinedData[0].row_id).to.equal("O3V");
      expect(combinedData[0].date).to.equal("2014-03-01");
    });
  });

  describe("_sortByDateAndRatio", () => {
    it("should return sorted data", () => {
      const combinedData = [
        {
          ratio_items: 12,
          y: 105,
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-03-01",
        },
        {
          ratio_items: 10,
          y: 204,
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-03-01",
        },
        {
          ratio_items: 15,
          y: 128,
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-04-01",
        },
        {
          ratio_items: 9,
          y: 179,
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-04-01",
        },
      ];
      utils.sortByDateAndRatio(combinedData, "ratio_items");
      expect(combinedData[0].ratio_items).to.equal(10);
      expect(combinedData[1].ratio_items).to.equal(12);
      expect(combinedData[2].ratio_items).to.equal(9);
      expect(combinedData[3].ratio_items).to.equal(15);
    });
  });
  // describe('#getDataForLineChart', function () {
  //     it('should create the data structure needed for the line charts', function () {
  //         var combinedData = [
  //           { 'ratio_actual_cost': 12, 'y_actual_cost': 105, 'x_actual_cost': 10, 'id': 'O3Q', 'name': 'NHS Corby', 'date': '2014-03-01'},
  //           { 'ratio_actual_cost': 10, 'y_actual_cost': 204, 'x_actual_cost': 11, 'id': 'O3V', 'name': 'NHS Vale of York', 'date': '2014-03-01'},
  //           { 'ratio_actual_cost': 15, 'y_actual_cost': 128, 'x_actual_cost': 12, 'id': 'O3Q', 'name': 'NHS Corby', 'date': '2014-04-01'},
  //           { 'ratio_actual_cost': 9, 'y_actual_cost': 179, 'x_actual_cost': 13, 'id': 'O3V', 'name': 'NHS Vale of York', 'date': '2014-04-01'}
  //         ];
  //         var values = {
  //             y: 'y_actual_cost',
  //             x: 'actual_cost',
  //             x_val: 'x_actual_cost',
  //             ratio: 'ratio_actual_cost'
  //         };
  //         var lineSeries = utils.getDataForLineChart(combinedData, values);
  //         expect(lineSeries.length).to.equal(2);
  //         expect(lineSeries[0].id).to.equal('O3Q');
  //         expect(lineSeries[0].name).to.equal('NHS Corby');
  //         expect(lineSeries[0].data[0].x).to.equal(1396310400000);
  //         expect(lineSeries[0].data[0].y).to.equal(12);
  //         expect(lineSeries[0].data[0].original_x).to.equal(10);
  //         expect(lineSeries[0].data[0].original_y).to.equal(105);
  //         expect(lineSeries[1].id).to.equal('O3V');
  //         expect(lineSeries[1].name).to.equal('NHS Vale of York');
  //         expect(lineSeries[1].data[0].x).to.equal(1396310400000);
  //         expect(lineSeries[1].data[0].y).to.equal(10);
  //         expect(lineSeries[1].data[0].original_x).to.equal(11);
  //         expect(lineSeries[1].data[0].original_y).to.equal(204);
  //     });
  // });

  // describe('#getDataForBarChart', function () {
  //     it('should create the data structure needed for the bar charts', function () {
  //         var combinedData = [
  //           { 'ratio_actual_cost': 12, 'y_actual_cost': 105, 'x_actual_cost': 10, 'id': 'O3Q', 'name': 'NHS Corby', 'date': '2014-03-01'},
  //           { 'ratio_actual_cost': 10, 'y_actual_cost': 204, 'x_actual_cost': 11, 'id': 'O3V', 'name': 'NHS Vale of York', 'date': '2014-03-01'},
  //           { 'ratio_actual_cost': 15, 'y_actual_cost': 128, 'x_actual_cost': 12, 'id': 'O3Q', 'name': 'NHS Corby', 'date': '2014-04-01'},
  //           { 'ratio_actual_cost': 9, 'y_actual_cost': 179, 'x_actual_cost': 13, 'id': 'O3V', 'name': 'NHS Vale of York', 'date': '2014-04-01'}
  //         ];
  //         var values = {
  //             y: 'y_actual_cost',
  //             x: 'actual_cost',
  //             x_val: 'x_actual_cost',
  //             ratio: 'ratio_actual_cost'
  //         };
  //         var barSeries = utils.getDataForBarChart(combinedData, values);
  //         // expect(lineSeries.length).to.equal(2);
  //         // expect(lineSeries[0].id).to.equal('O3Q');
  //         // expect(lineSeries[0].name).to.equal('NHS Corby');
  //         // expect(lineSeries[0].data[0].x).to.equal(1396310400000);
  //         // expect(lineSeries[0].data[0].y).to.equal(12);
  //         // expect(lineSeries[0].data[0].original_x).to.equal(10);
  //         // expect(lineSeries[0].data[0].original_y).to.equal(105);
  //         // expect(lineSeries[1].id).to.equal('O3V');
  //         // expect(lineSeries[1].name).to.equal('NHS Vale of York');
  //         // expect(lineSeries[1].data[0].x).to.equal(1396310400000);
  //         // expect(lineSeries[1].data[0].y).to.equal(10);
  //         // expect(lineSeries[1].data[0].original_x).to.equal(11);
  //         // expect(lineSeries[1].data[0].original_y).to.equal(204);
  //     });
  // });

  describe("#indexDataByRowNameAndMonth", () => {
    it("should return an object indexed by row_name and date", () => {
      const data = [
        {
          x: 12,
          y: 105,
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-03-01",
        },
        {
          x: 10,
          y: 204,
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-03-01",
        },
        {
          x: 15,
          y: 128,
          row_id: "O3Q",
          row_name: "NHS Corby",
          date: "2014-04-01",
        },
        {
          x: 9,
          y: 179,
          row_id: "O3V",
          row_name: "NHS Vale of York",
          date: "2014-04-01",
        },
      ];
      const dataByName = utils.indexDataByRowNameAndMonth(data);
      expect(Object.keys(dataByName)).to.eql(["NHS Corby", "NHS Vale of York"]);
      expect(dataByName["NHS Corby"]["2014-03-01"].x).to.equal(12);
      expect(dataByName["NHS Corby"]["2014-03-01"].y).to.equal(105);
      expect(dataByName["NHS Vale of York"]["2014-03-01"].x).to.equal(10);
      expect(dataByName["NHS Vale of York"]["2014-03-01"].y).to.equal(204);
      expect(dataByName["NHS Corby"]["2014-04-01"].x).to.equal(15);
      expect(dataByName["NHS Corby"]["2014-04-01"].y).to.equal(128);
      expect(dataByName["NHS Vale of York"]["2014-04-01"].x).to.equal(9);
      expect(dataByName["NHS Vale of York"]["2014-04-01"].y).to.equal(179);
    });
  });

  describe("#getAllMonthsInData", () => {
    it("should return a range of months", () => {
      const options = {
        data: {
          combinedData: [
            { row_id: "O3Q", row_name: "NHS Corby", date: "2010-04-01" },
            { row_id: "O3V", row_name: "NHS Vale of York", date: "2011-02-01" },
          ],
        },
      };
      const months = utils.getAllMonthsInData(options);
      expect(months.length).to.equal(11);
      expect(months).to.eql([
        "2010-04-01",
        "2010-05-01",
        "2010-06-01",
        "2010-07-01",
        "2010-08-01",
        "2010-09-01",
        "2010-10-01",
        "2010-11-01",
        "2010-12-01",
        "2011-01-01",
        "2011-02-01",
      ]);
    });
    it("should start in Aug 2013 for CCGs", () => {
      const options = {
        org: "CCG",
        data: {
          combinedData: [
            { row_id: "O3Q", row_name: "NHS Corby", date: "2013-04-01" },
            { row_id: "O3V", row_name: "NHS Vale of York", date: "2013-09-01" },
          ],
        },
      };
      const months = utils.getAllMonthsInData(options);
      expect(months).to.eql([
        "2013-04-01",
        "2013-05-01",
        "2013-06-01",
        "2013-07-01",
        "2013-08-01",
        "2013-09-01",
      ]);
    });
  });

  describe("#calculateMinMaxByDate", () => {
    it("should return (min,max) tuples, indexed by date", () => {
      const combinedData = [
        { date: "2010-04-01", ratio_items: 1, ratio_actual_cost: 10 },
        { date: "2010-04-01", ratio_items: 8, ratio_actual_cost: 80 },
        { date: "2010-04-01", ratio_items: 9, ratio_actual_cost: 90 },
        { date: "2010-04-01", ratio_items: 10, ratio_actual_cost: 100 },
        { date: "2010-04-02", ratio_items: 10, ratio_actual_cost: 100 },
        { date: "2010-04-02", ratio_items: 20, ratio_actual_cost: 200 },
      ];
      const minMax = utils.calculateMinMaxByDate(combinedData);
      expect(minMax["2010-04-01"].ratio_actual_cost[0]).to.equal(10);
      expect(minMax["2010-04-01"].ratio_actual_cost[1]).to.equal(100);
      expect(minMax["2010-04-02"].ratio_actual_cost[0]).to.equal(100);
      expect(minMax["2010-04-02"].ratio_actual_cost[1]).to.equal(200);
    });
  });

  describe("#setChartValues", () => {
    it("should construct the values used by the chart", () => {
      const options = {
        activeOption: "items",
        denom: "chemical",
      };
      const values = utils.setChartValues(options);
      expect(values.y).to.equal("y_items");
      expect(values.x).to.equal("items");
      expect(values.x_val).to.equal("x_items");
      expect(values.ratio).to.equal("ratio_items");
    });

    it("should construct values when spending is active", () => {
      const options = {
        activeOption: "actual_cost",
        denom: "chemical",
      };
      const values = utils.setChartValues(options);
      expect(values.y).to.equal("y_actual_cost");
      expect(values.x).to.equal("actual_cost");
      expect(values.x_val).to.equal("x_actual_cost");
      expect(values.ratio).to.equal("ratio_actual_cost");
    });

    it("should construct values for non-chemical denominator", () => {
      const options = {
        activeOption: "items",
        denom: "astro_pu_cost",
      };
      const values = utils.setChartValues(options);
      expect(values.y).to.equal("y_items");
      expect(values.x).to.equal("astro_pu_cost");
      expect(values.x_val).to.equal("astro_pu_cost");
      expect(values.ratio).to.equal("ratio_items");
    });
  });
});
