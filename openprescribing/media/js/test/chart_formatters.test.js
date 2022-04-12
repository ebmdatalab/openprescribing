import { describe, expect, it } from "vitest";
import formatters from "../src/chart_formatters";

describe("Formatters", () => {
  describe("#getFriendlyNamesForChart", () => {
    it("should construct the chart title from options", () => {
      const options = {
        chartValues: {
          y: "y_actual_cost",
        },
        org: "practice",
        orgIds: [],
        denom: "chemical",
        denomIds: [{ id: 5234 }, { id: 534 }],
        num: "chemical",
        numIds: [{ id: 514 }, { id: 564 }],
      };
      const titles = formatters.getFriendlyNamesForChart(options);
      expect(titles.friendlyOrgs).to.equal("all practices");
      expect(titles.friendlyNumerator).to.equal("514 + 564");
      expect(titles.friendlyDenominator).to.equal("5234 + 534");
      expect(titles.partialDenominator).to.equal("Spend on 5234 + 534");
      expect(titles.fullDenominator).to.equal("£1,000 spend on 5234 + 534");
    });
  });

  describe("#getFriendlyOrgs", () => {
    it("should return a friendly string for organisations", () => {
      let str = formatters.getFriendlyOrgs("all", []);
      expect(str).to.equal("all practices in NHS England");
      str = formatters.getFriendlyOrgs("CCG", []);
      expect(str).to.equal("all CCGs");
      str = formatters.getFriendlyOrgs("practice", []);
      expect(str).to.equal("all practices");
      str = formatters.getFriendlyOrgs("practice", [
        { id: "03V" },
        { id: "11A" },
      ]);
      expect(str).to.equal("practices in 03V + practices in 11A");
      str = formatters.getFriendlyOrgs("practice", [{ id: "P12353" }]);
      expect(str).to.equal("P12353 <br/>and other practices in CCG");
    });
  });

  describe("#getFriendlyNumerator", () => {
    it("should return a friendly string for numerator", () => {
      let str = formatters.getFriendlyNumerator([{ id: "a" }, { id: "b" }]);
      expect(str).to.equal("a + b");
      str = formatters.getFriendlyNumerator([]);
      expect(str).to.equal("all prescribing");
    });
  });

  describe("#getFriendlyDenominator", () => {
    it("should return a friendly string for denominator", () => {
      let str = formatters.getFriendlyDenominator("chemical", [
        { id: "a" },
        { id: "b" },
      ]);
      expect(str).to.equal("a + b");
      str = formatters.getFriendlyDenominator("chemical", []);
      expect(str).to.equal("all prescribing");
      str = formatters.getFriendlyDenominator("total_list_size", []);
      expect(str).to.equal("patients on list");
      str = formatters.getFriendlyDenominator("astro_pu_cost", []);
      expect(str).to.equal("ASTRO-PUs");
      str = formatters.getFriendlyDenominator(
        "star_pu.oral_antibacterials_item",
        []
      );
      expect(str).to.equal("STAR-PUs for oral antibiotics");
    });
  });

  describe("#getPartialDenominator", () => {
    it("should return a partial string for denominator", () => {
      let str = formatters.getPartialDenominator("items", "chemical", "a + b");
      expect(str).to.equal("Items for a + b");
      str = formatters.getPartialDenominator(
        "actual_cost",
        "chemical",
        "a + b"
      );
      expect(str).to.equal("Spend on a + b");
      str = formatters.getPartialDenominator(
        "actual_cost",
        "total_list_size",
        "a + b"
      );
      expect(str).to.equal("a + b");
      str = formatters.getPartialDenominator(
        "actual_cost",
        "astro_pu_cost",
        "a + b"
      );
      expect(str).to.equal("a + b");
    });
  });

  describe("#getFullDenominator", () => {
    it("should return a full string for denominator", () => {
      let str = formatters.getFullDenominator("items", "chemical", "a + b");
      expect(str).to.equal("1,000 items for a + b");
      str = formatters.getFullDenominator("actual_cost", "chemical", "a + b");
      expect(str).to.equal("£1,000 spend on a + b");
      str = formatters.getFullDenominator(
        "actual_cost",
        "total_list_size",
        "patients on list"
      );
      expect(str).to.equal(" 1,000 patients on list");
      str = formatters.getFullDenominator(
        "actual_cost",
        "astro_pu_cost",
        "ASTRO-PUs"
      );
      expect(str).to.equal(" 1,000 ASTRO-PUs");
    });
  });

  describe("#constructChartTitle", () => {
    it("should construct the chart title from options", () => {
      let title = formatters.constructChartTitle(
        "actual_cost",
        "chemical",
        "514 + 564",
        "5234 + 534",
        "all practices"
      );
      expect(title).to.equal(
        "Spend on 514 + 564 vs 5234 + 534<br/> by all practices"
      );
      title = formatters.constructChartTitle(
        "items",
        "chemical",
        "514 + 564 + 564 + 564 + 564 + 564",
        "5234 + 534",
        "all practices"
      );
      let expected = "Items for 514 + 564 + 564 + 564 + 564 + 564<br/>";
      expected += " vs 5234 + 534<br/> by all practices";
      expect(title).to.equal(expected);
      title = formatters.constructChartTitle(
        "actual_cost",
        "nothing",
        "514 + 564",
        "5234 + 534",
        "all practices"
      );
      expect(title).to.equal("Spend on 514 + 564 by all practices");
    });
  });

  describe("#constructChartSubTitle", () => {
    it("should construct the chart title from options", () => {
      const title = formatters.constructChartSubTitle("2014-01-01");
      expect(title).to.equal("in 2014-01-01");
    });
  });

  describe("#constructYAxisTitle", () => {
    it("should construct the y-axis title from options", () => {
      const title = formatters.constructYAxisTitle(
        "actual_cost",
        "chemical",
        "14 + 15",
        "1,000 patients on list"
      );
      expect(title).to.equal(
        "Spend on 14 + 15<br/> per 1,000 patients on list"
      );
    });
  });

  describe("#constructTooltip", () => {
    it("should construct the tooltip from options", () => {
      const options = {
        activeOption: "actual_cost",
        org: "practice",
        denom: "chemical",
        friendly: {
          friendlyNumerator: "514 + 564",
          partialDenominator: "5234 + 534",
          yAxisTitle: "Spend on <br/>something",
        },
      };
      const str = formatters.constructTooltip(
        options,
        "03V",
        "2014-01-01",
        10,
        14,
        1.4
      );
      let expected = "<b>03V</b><br/>";
      expected += "Spend on 514 + 564 in 2014/01/01: £10<br/>";
      expected += "5234 + 534 in 2014/01/01: £14<br/>";
      expected += "Spend on something: £1.4";
      expect(str).to.equal(expected);
    });

    it("should force items where necessary", () => {
      const options = {
        activeOption: "actual_cost",
        org: "practice",
        denom: "chemical",
        friendly: {
          friendlyNumerator: "514 + 564",
          partialDenominator: "5234 + 534",
          yAxisTitle: "Spend on <br/>something",
        },
      };
      const str = formatters.constructTooltip(
        options,
        "03V",
        "2014-01-01",
        10,
        14,
        1.4,
        true
      );
      let expected = "<b>03V</b><br/>";
      expected += "Items for 514 + 564 in 2014/01/01: 10<br/>";
      expected += "5234 + 534 in 2014/01/01: 14<br/>";
      expected += "Items for something: 1.4";
      expect(str).to.equal(expected);
    });

    it("should handle non-chemical denominators", () => {
      const options = {
        activeOption: "actual_cost",
        org: "practice",
        denom: "astro_pu_cost",
        friendly: {
          friendlyNumerator: "514 + 564",
          partialDenominator: "5234 + 534",
          yAxisTitle: "Spend on <br/>something",
        },
      };
      const str = formatters.constructTooltip(
        options,
        "03V",
        "2014-01-01",
        10,
        14,
        1.4,
        false
      );
      let expected = "<b>03V</b><br/>";
      expected += "Spend on 514 + 564 in 2014/01/01: £10<br/>";
      expected += "5234 + 534 in 2014/01/01: 14<br/>";
      expected += "Spend on something: £1.4";
      expect(str).to.equal(expected);
    });
  });

  describe("#_getStringForIds", () => {
    it("should join multiple ids with plusses", () => {
      const str = formatters._getStringForIds([{ id: 2 }, { id: 3 }], true);
      expect(str).to.equal("2 + 3");
    });
    it('should prepend "practices in" when second arg is true', () => {
      const str = formatters._getStringForIds([{ id: "03V" }], true);
      expect(str).to.equal("practices in 03V");
    });
    it("should elide long lists to max length", () => {
      const str = formatters._getStringForIds([
        { id: "asdfghjk qwerty zxcvb" },
        { id: "asdfghjk qwerty zxcvb" },
        { id: "asdfghjk qwerty zxcvb" },
        { id: "asdfghjk qwerty zxcvb" },
        { id: "asdfghjk qwerty zxcvb" },
        { id: "asdfghjk qwerty zxcvb" },
        { id: "asdfghjk qwerty zxcvb" },
      ]);
      expect(str).to.equal(
        "asdfghjk qwerty zxcvb + asdfghjk " +
          "qwerty zxcvb + asdfghjk qwerty zxcvb …"
      );
    });
  });
});
