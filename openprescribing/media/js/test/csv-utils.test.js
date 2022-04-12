import { describe, expect, it } from "vitest";
import csvUtils from "../src/csv-utils";

describe("csvUtils", () => {
  describe("#formatTableAsCSV", () => {
    it("returns valid CSV", () => {
      const result = csvUtils.formatTableAsCSV([
        ["one", "two", "three"],
        [1, null, "with, comma"],
        [2, "a", 'with " double quote'],
      ]);
      expect(result).to.equal(
        'one,two,three\n1,,"with, comma"\n2,a,"with "" double quote"'
      );
    });
  });

  describe("#getFilename", () => {
    it("removes special characters from string and collaposes multiple spaces", () => {
      const result = csvUtils.getFilename('Hello $" 123-456.test_str : ');
      expect(result).to.equal("Hello 123-456.test_str.csv");
    });
  });
});
