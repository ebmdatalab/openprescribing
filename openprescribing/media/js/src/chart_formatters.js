import humanize from "humanize";
import _ from "underscore";

const ORG_TYPES = {
  practice: {
    name: "practice",
    title: "Practice",
  },
  ccg: {
    name: "CCG",
    title: "CCG",
  },
  pcn: {
    name: "PCN",
    title: "PCN",
  },
  stp: {
    name: "STP",
    title: "STP",
  },
  regional_team: {
    name: "regional team",
    title: "Regional Team",
  },
};

ORG_TYPES.CCG = ORG_TYPES.ccg;

const formatters = {
  getFriendlyNamesForChart(options) {
    const f = {};
    f.friendlyOrgs = this.getFriendlyOrgs(options.org, options.orgIds);
    f.friendlyNumerator = this.getFriendlyNumerator(options.numIds);
    f.friendlyDenominator = this.getFriendlyDenominator(
      options.denom,
      options.denomIds
    );
    f.partialDenominator = this.getPartialDenominator(
      options.activeOption,
      options.denom,
      f.friendlyDenominator
    );
    f.fullDenominator = this.getFullDenominator(
      options.activeOption,
      options.denom,
      f.friendlyDenominator
    );
    f.chartTitle = this.constructChartTitle(
      options.activeOption,
      options.denom,
      f.friendlyNumerator,
      f.friendlyDenominator,
      f.friendlyOrgs
    );
    f.chartSubTitle = this.constructChartSubTitle(options.activeMonth);
    f.yAxisTitle = this.constructYAxisTitle(
      options.activeOption,
      options.denom,
      f.friendlyNumerator,
      f.fullDenominator
    );
    f.filename = this.constructFilename(
      options.activeOption,
      f.friendlyNumerator,
      f.fullDenominator
    );
    f.yAxisFormatter = this.getYAxisLabelFormatter(options.chartValues);
    return f;
  },

  getFriendlyOrgs(org, orgIds) {
    let str = "";
    if (org === "all") {
      str = "all practices in NHS England";
    } else {
      if (org === "practice" && orgIds.length > 0) {
        str = this._getStringForIds(orgIds, true);
        if (_.any(_.map(orgIds, ({ id }) => id.length > 3))) {
          str += " <br/>and other practices in CCG";
        }
      } else {
        if (orgIds.length > 0) {
          str = this._getStringForIds(orgIds, false);
          str += ` <br/>and other ${this.getFriendlyOrgType(org)}s`;
        } else {
          str = `all ${this.getFriendlyOrgType(org)}s`;
        }
      }
    }
    return str;
  },

  getFriendlyOrgType(orgType) {
    const orgTypeDetails = ORG_TYPES[orgType];
    if (!orgTypeDetails) {
      throw `Unhandled orgType: ${orgType}`;
    }
    return orgTypeDetails.name;
  },

  getFriendlyOrgTypeTitle(orgType) {
    const orgTypeDetails = ORG_TYPES[orgType];
    if (!orgTypeDetails) {
      throw `Unhandled orgType: ${orgType}`;
    }
    return orgTypeDetails.title;
  },

  getFriendlyNumerator(numIds) {
    let str = "";
    if (numIds.length > 0) {
      str += this._getStringForIds(numIds, false);
    } else {
      str += "all prescribing";
    }
    return str;
  },

  getFriendlyDenominator(denom, denomIds) {
    let str = "";
    if (denom === "total_list_size") {
      str = "patients on list";
    } else if (denom === "astro_pu_cost") {
      str = "ASTRO-PUs";
    } else if (denom === "star_pu.oral_antibacterials_item") {
      str = "STAR-PUs for oral antibiotics";
    } else {
      if (denomIds.length > 0) {
        str = this._getStringForIds(denomIds, false);
      } else {
        str = "all prescribing";
      }
    }
    return str;
  },

  getPartialDenominator(activeOption, denom, friendlyDenominator) {
    let str;
    if (denom === "chemical") {
      str = activeOption == "items" ? "Items for " : "Spend on ";
      str += friendlyDenominator;
    } else {
      str = friendlyDenominator;
    }
    return str;
  },

  getFullDenominator(activeOption, denom, denomStr) {
    let str;
    if (denom === "chemical") {
      str = activeOption === "items" ? "1,000 items for " : "£1,000 spend on ";
      str += denomStr;
    } else if (denom == "nothing") {
      str = "";
    } else {
      str = ` 1,000 ${denomStr}`;
    }
    return str;
  },

  constructChartTitle(activeOption, denom, numStr, denomStr, orgStr) {
    let chartTitle = activeOption == "items" ? "Items for " : "Spend on ";
    chartTitle += numStr;
    chartTitle += chartTitle.length > 40 ? "<br/>" : "";
    if (denom !== "nothing") {
      chartTitle += ` vs ${denomStr}<br/>`;
    }
    chartTitle += ` by ${orgStr}`;
    return chartTitle;
  },

  constructChartSubTitle(month) {
    const monthDate = month ? new Date(month.replace(/-/g, "/")) : month;
    let subTitle = "in ";
    subTitle +=
      typeof Highcharts !== "undefined"
        ? Highcharts.dateFormat("%b '%y", monthDate)
        : month;
    return subTitle;
  },

  constructYAxisTitle(activeOption, denom, friendlyNumerator, fullDenominator) {
    let axisTitle = activeOption == "items" ? "Items for " : "Spend on ";
    axisTitle += friendlyNumerator;
    if (denom !== "nothing") {
      axisTitle += `<br/> per ${fullDenominator}`;
    }
    return axisTitle;
  },

  constructFilename(activeOption, friendlyNumerator, fullDenominator) {
    let axisTitle = activeOption == "items" ? "items for " : "spend on ";
    axisTitle += friendlyNumerator;
    axisTitle += ` per${fullDenominator}`;
    return axisTitle.toLowerCase();
  },

  constructTooltip(
    options,
    series_name,
    date,
    original_y,
    original_x,
    ratio,
    force_items
  ) {
    let tt = "";
    const activeOption = options.activeOption;
    let numDecimals;
    let p;
    numDecimals = activeOption === "items" ? 0 : 2;
    if (date !== null) {
      if (typeof date === "string") {
        date = date.replace(/-/g, "/");
      }
      date =
        typeof Highcharts !== "undefined"
          ? Highcharts.dateFormat("%b '%y", new Date(date))
          : date;
    } else {
      date =
        options.org == "practice" ? " since August 2010" : " since April 2013";
    }
    tt += series_name !== "Series 1" ? `<b>${series_name}</b><br/>` : "";

    tt += activeOption == "items" ? "Items for " : "Spend on ";
    tt += options.friendly.friendlyNumerator;
    tt += ` in ${date}: `;
    tt += force_items || options.activeOption === "items" ? "" : "£";
    tt +=
      typeof Highcharts !== "undefined"
        ? Highcharts.numberFormat(original_y, numDecimals)
        : original_y;

    if (options.denom !== "nothing") {
      tt += "<br/>";

      p = options.friendly.partialDenominator.charAt(0).toUpperCase();
      p += options.friendly.partialDenominator.substring(1);
      tt += `${p} in ${date}: `;
      if (options.activeOption !== "items") {
        tt += !force_items && options.denom === "chemical" ? "£" : "";
      }
      tt +=
        typeof Highcharts !== "undefined"
          ? Highcharts.numberFormat(original_x, numDecimals)
          : original_x;
      tt += "<br/>";
      tt += `${options.friendly.yAxisTitle.replace("<br/>", "")}: `;
      tt += force_items || options.activeOption === "items" ? "" : "£";
      tt +=
        typeof Highcharts !== "undefined"
          ? Highcharts.numberFormat(ratio)
          : ratio;
      // The line chart tooltips will only ever show items, regardless
      // of what global items have been set elsewhere.
      if (force_items) {
        tt = tt.replace(/Spend on/g, "Items for");
      }
    }
    return tt;
  },

  getYAxisLabelFormatter({ y }) {
    if (y === "y_actual_cost") {
      return function () {
        return `£${this.axis.defaultLabelFormatter.call(this)}`;
      };
    } else {
      return function () {
        return this.axis.defaultLabelFormatter.call(this);
      };
    }
  },

  _getStringForIds(ids, is_practices) {
    const maxLength = 70;
    let str = "";
    _.each(ids, (e, i) => {
      const id = e.display_id ? e.display_id : e.id;
      if (is_practices && e.id.length === 3) {
        str += "practices in ";
      }
      str += e.name ? e.name : id;
      str += i === ids.length - 1 ? "" : " + ";
    });
    str = humanize.truncatechars(str, maxLength);
    return str;
  },
};

export default formatters;
