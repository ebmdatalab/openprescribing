import moment from "moment";
import _ from "underscore";
import config from "./config";

const utils = {
  getIEVersion() {
    const ie = (() => {
      let undef;
      let v = 3;
      const div = document.createElement("div");
      const all = div.getElementsByTagName("i");
      while (
        ((div.innerHTML = `<!--[if gt IE ${++v}]><i></i><![endif]-->`), all[0])
      );
      return v > 4 ? v : undef;
    })();
    if (typeof ie !== "undefined" && ie <= 9) {
      return true;
    } else {
      return false;
    }
  },

  constructQueryURLs(options) {
    let numeratorUrl = `${config.apiHost}/api/1.0`;
    if (options.org && options.org !== "all") {
      numeratorUrl += `/spending_by_org/?format=json&org_type=${options.org.toLowerCase()}`;
    } else {
      numeratorUrl += "/spending/?format=json";
    }
    const num_ids = options.numIds;
    if (num_ids.length > 0) {
      numeratorUrl += `&code=${this.idsToString(num_ids)}`;
    }
    const org_ids = options.orgIds;
    if (org_ids.length > 0 && options.org === "practice") {
      numeratorUrl += "&org=";
      _.each(org_ids, (d, i) => {
        if ("ccg" in d && d.ccg) {
          numeratorUrl += d.ccg;
        } else {
          numeratorUrl += d.id;
        }
        numeratorUrl += i !== org_ids.length - 1 ? "," : "";
      });
    }
    let denominatorUrl = `${config.apiHost}/api/1.0`;
    if (options.denom === "chemical") {
      if (options.org && options.org !== "all") {
        denominatorUrl += `/spending_by_org/?format=json&org_type=${options.org.toLowerCase()}`;
      } else {
        denominatorUrl += "/spending/?format=json";
      }
      const denom_ids = options.denomIds;
      if (denom_ids.length > 0) {
        denominatorUrl += `&code=${this.idsToString(denom_ids)}`;
      }
    } else {
      denominatorUrl += "/org_details/?format=json";
      denominatorUrl += `&org_type=${options.org.toLowerCase()}`;
      denominatorUrl += `&keys=${options.denom}`;
    }
    if (org_ids.length > 0 && options.org === "practice") {
      denominatorUrl += "&org=";
      _.each(org_ids, (d, i) => {
        if ("ccg" in d && d.ccg) {
          denominatorUrl += d.ccg;
        } else {
          denominatorUrl += d.id;
        }
        denominatorUrl += i !== org_ids.length - 1 ? "," : "";
      });
    }
    return {
      denominatorUrl: denominatorUrl.replace("?&", "?"),
      numeratorUrl: numeratorUrl.replace("?&", "?"),
    };
  },

  idsToString(ids) {
    let str = "";
    _.each(ids, ({ id }, i) => {
      str += id;
      str += i !== ids.length - 1 ? "," : "";
    });
    return str;
  },

  combineXAndYDatasets(xData, yData, options) {
    // Glue the x and y series data points together, and returns a
    // dataset with a row for each organisation and each month.  Also
    // calculates ratios for cost and items, and optionally filters
    // out CCGs or practices with significant numbers of ratios where
    // the denominator is greater than the numerator.
    const isSpecialDenominator =
      options.chartValues.x_val !== "x_actual_cost" &&
      options.chartValues.x_val !== "x_items" &&
      typeof options.chartValues.x_val !== "undefined";
    let combinedData = this.combineDatasets(
      xData,
      yData,
      options.chartValues.x,
      options.chartValues.x_val
    );
    combinedData = this.calculateRatiosForData(
      combinedData,
      isSpecialDenominator,
      options.chartValues.x_val
    );
    this.sortByDateAndRatio(combinedData, "ratio_items");
    return this.partitionOutliers(combinedData, options);
  },

  partitionOutliers(combinedData, options) {
    // Optionally separate practices or CCGs that have a number of
    // data points that are extreme outliers (which we count as the
    // upper quartile plus 20 times the interquartile range)
    const byDate = _.groupBy(combinedData, "date");
    const candidates = {};
    _.mapObject(byDate, (val, key) => {
      let ratios = _.pluck(val, "ratio_items");
      ratios.sort((a, b) => a - b);
      // Discount zero values when calculating outliers
      ratios = _.filter(ratios, (d) => d > 0);
      const l = ratios.length;
      const LQ = ratios[Math.round(l / 4) - 1];
      const UQ = ratios[Math.round((3 * l) / 4) - 1];
      const IQR = UQ - LQ;
      const cutoff = UQ + 20 * IQR;
      const outliers = _.filter(val, ({ ratio_items }) => ratio_items > cutoff);
      _.each(outliers, ({ id, row_name }) => {
        candidates[id] = row_name;
      });
    });
    const skipIds = _.keys(candidates);
    const filteredData = _.filter(
      combinedData,
      ({ id }) => !_.contains(skipIds, id)
    );
    if (filteredData.length !== combinedData.length) {
      options.hasOutliers = true;
      options.skippedOutliers = candidates;
    }
    // If the option is set, actually hide these practices or CCGs
    if (options.hideOutliers) {
      combinedData = filteredData;
    }
    return combinedData;
  },

  combineDatasets(xData, yData, x_val, x_val_key) {
    const xDataDict = _.reduce(
      xData,
      (p, c) => {
        const key = `${c.row_id}-${c.date}`;
        p[key] = {
          row_id: c.row_id,
          row_name: c.row_name,
          date: c.date,
          setting: c.setting,
          x_actual_cost: +c.actual_cost || 0,
          x_items: +c.items || 0,
          y_actual_cost: 0,
          y_items: 0,
        };
        if (x_val.slice(0, 8) == "star_pu.") {
          p[key][x_val_key] = +c["star_pu"][x_val.slice(8, x_val.length)];
        } else {
          p[key][x_val_key] = +c[x_val];
        }
        return p;
      },
      {}
    );
    const xAndYDataDict = _.reduce(
      yData,
      (p, c) => {
        const key = `${c.row_id}-${c.date}`;
        if (p[key]) {
          p[key].setting = c.setting;
          p[key].y_actual_cost = +c.actual_cost || 0;
          p[key].y_items = +c.items || 0;
        } else {
          p[key] = {
            row_id: c.row_id,
            row_name: c.row_name,
            date: c.date,
            setting: c.setting,
            x_actual_cost: 0,
            x_items: 0,
            y_actual_cost: +c.actual_cost || 0,
            y_items: +c.items || 0,
          };
          p[key][x_val_key] = 0;
        }
        return p;
      },
      xDataDict
    );

    const combined = _.values(xAndYDataDict);
    return _.filter(
      combined,
      (
        { setting } // Filter out non-prescribing practices. Ignore this for CCGs.
      ) => typeof setting === "undefined" || setting === 4
    );
  },

  calculateRatiosForData(data, isSpecialDenominator, x_val_key) {
    const ratio_actual_cost_x = isSpecialDenominator
      ? x_val_key
      : "x_actual_cost";
    const ratio_item_x = isSpecialDenominator ? x_val_key : "x_items";
    _.each(data, (d, i) => {
      d.name = "row_name" in d ? `${d.row_name} (${d.row_id})` : null;
      d.id = "row_id" in d ? d.row_id : null;
      if (d[ratio_item_x] !== null && d[ratio_item_x] > 0) {
        d.ratio_items = d.y_items / d[ratio_item_x];
        if (x_val_key !== "nothing") {
          d.ratio_items = d.ratio_items * 1000;
        }
      } else if (d[ratio_item_x] === 0) {
        d.ratio_items = null;
      }
      if (d[ratio_actual_cost_x] !== null && d[ratio_actual_cost_x] > 0) {
        d.ratio_actual_cost = d.y_actual_cost / d[ratio_actual_cost_x];
        if (x_val_key !== "nothing") {
          d.ratio_actual_cost = d.ratio_actual_cost * 1000;
        }
      } else if (d[ratio_actual_cost_x] === 0) {
        d.ratio_actual_cost = null;
      }
    });
    return data;
  },

  sortByDateAndRatio(data, ratio) {
    // The category data in the bar chart needs to be in order.
    data.sort((a, b) => {
      const aDate = new Date(a.date);
      const bDate = new Date(b.date);
      const x = aDate - bDate;
      return x === 0 ? a[ratio] - b[ratio] : x;
    });
  },

  createChartSeries(data) {
    // Create a deep copy of the data.
    const dataCopy = JSON.parse(JSON.stringify(data));
    const chartSeries = [
      {
        turboThreshold: 25000,
        data: dataCopy,
        color: "rgba(119, 152, 191, .5)",
      },
    ];
    return chartSeries;
  },

  indexDataByRowNameAndMonth(combinedData) {
    // Used in the maps.
    const newData = {};
    _.each(combinedData, (d) => {
      if (d.row_name in newData) {
        newData[d.row_name][d.date] = d;
      } else {
        newData[d.row_name] = {};
        newData[d.row_name][d.date] = d;
      }
    });
    return newData;
  },

  getAllMonthsInData({ data }) {
    const combinedData = data.combinedData;
    // Used for date slider.
    const monthRange = [];
    if (combinedData.length > 0) {
      const firstMonth = combinedData[0].date;
      const lastMonth = combinedData[combinedData.length - 1].date;
      const startDate = moment(firstMonth);
      const endDate = moment(lastMonth);
      if (endDate.isBefore(startDate)) {
        throw "End date must be greater than start date.";
      }
      while (startDate.isBefore(endDate) || startDate.isSame(endDate)) {
        monthRange.push(startDate.format("YYYY-MM-01"));
        startDate.add(1, "month");
      }
    }
    return monthRange;
  },

  calculateMinMaxByDate(combinedData) {
    // Used in maps.
    const minMaxByDate = {};
    const temp = {};
    _.each(combinedData, (d) => {
      if (d.date in temp) {
        temp[d.date].push(d);
      } else {
        temp[d.date] = [d];
      }
    });
    for (const date in temp) {
      minMaxByDate[date] = {};
      minMaxByDate[date].ratio_actual_cost = this.calculateMinMax(
        temp[date],
        "ratio_actual_cost"
      );
      minMaxByDate[date].ratio_items = this.calculateMinMax(
        temp[date],
        "ratio_items"
      );
    }

    return minMaxByDate;
  },

  calculateMinMax(arr, key) {
    return [_.min(_.pluck(arr, key)), _.max(_.pluck(arr, key))];
  },

  setChartValues({ activeOption, denom }) {
    const y = activeOption;
    const x = denom === "chemical" ? y : denom;
    const x_val = denom === "chemical" ? `x_${y}` : denom;
    return {
      y: `y_${y}`,
      x,
      x_val,
      ratio: `ratio_${y}`,
    };
  },
};

export default utils;
