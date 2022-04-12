import _ from "underscore";
import formatters from "./chart_formatters";
import utils from "./chart_utils";

const barChart = {
  setUp(barOptions, globalOptions) {
    // console.log('setUpBarChart');
    barOptions.yAxis.title = {
      text: globalOptions.friendly.yAxisTitle,
    };

    if (barOptions.yAxis.title.text.includes("<br/>")) {
      barOptions.yAxis.title.margin = 35;
    }
    barOptions.yAxis.labels = {
      formatter: globalOptions.friendly.yAxisFormatter,
    };

    const xAxisTitle = formatters.getFriendlyOrgTypeTitle(globalOptions.org);
    barOptions.xAxis.title = { text: xAxisTitle };

    const chartValues = globalOptions.chartValues;
    barOptions.tooltip = {
      formatter() {
        const chartValues = globalOptions.chartValues;
        const name = `${this.point.name} (${this.point.id})`;
        const month = this.point.date;
        const original_x = this.point.options[chartValues.x_val];
        const original_y = this.point.options[chartValues.y];
        const y = this.y;
        return formatters.constructTooltip(
          globalOptions,
          name,
          month,
          original_y,
          original_x,
          y
        );
      },
    };

    const activeOrgs = _.pluck(globalOptions.orgIds, "id");

    const convertedData = this._indexDataByMonthAndRatio(
      globalOptions.data.combinedData,
      activeOrgs
    );
    this.barData = convertedData.barData;
    globalOptions.maxRatioActualCost = convertedData.maxRatioActualCost;
    globalOptions.maxRatioItems = convertedData.maxRatioItems;

    // Ensure we always show ticks for any active (selected) orgs:
    barOptions.xAxis.tickPositioner = function () {
      const calculated = this.tickPositions;
      const activeOrgsIndex = [];
      _.each(this.series[0].options.data, ({ active }, i) => {
        if (active) {
          activeOrgsIndex.push(i);
        }
      });
      _.each(activeOrgsIndex, (d) => {
        const j = _.sortedIndex(calculated, d);
        calculated.splice(j, 0, d);
      });
      return calculated;
    };

    const activeMonth = globalOptions.activeMonth;
    const ratio = globalOptions.chartValues.ratio;
    const dataForMonth = this.barData[activeMonth][ratio];
    // Fix the y Axis

    if (ratio === "ratio_actual_cost") {
      barOptions.yAxis.max = globalOptions.maxRatioActualCost;
    } else {
      barOptions.yAxis.max = globalOptions.maxRatioItems;
    }
    barOptions.series = utils.createChartSeries(dataForMonth);
    barOptions.xAxis.categories = this._getCategoriesFromData(dataForMonth);

    return new Highcharts.Chart(barOptions);
  },

  _getCategoriesFromData(data) {
    return data.map(({ name }) => name);
  },

  update(chart, month, ratio, title, formatter, playing, yAxisMax) {
    const newYAxisOptions = {
      title: {
        text: title,
      },
      labels: {
        formatter,
      },
    };
    if (playing) {
      chart.animation = false;
    }
    chart.yAxis[0].update(newYAxisOptions, false);

    const data = month in this.barData ? this.barData[month][ratio] : [];
    chart.series[0].setData(data, false);
    chart.yAxis[0].setExtremes(null, yAxisMax);
    chart.xAxis[0].setCategories(this._getCategoriesFromData(data), false);

    try {
      chart.redraw();
    } catch (err) {
      chart.series[0].setData(data, true);
    }
  },

  _indexDataByMonthAndRatio(combinedData, activeOrgs) {
    const newData = {};
    _.each(combinedData, (d) => {
      d.name = d.row_name;
      if (_.contains(activeOrgs, d.id)) {
        d.color = "rgba(255, 64, 129, .8)";
        d.active = true;
      } else {
        d.color = "rgba(119, 152, 191, .5)";
        d.active = false;
      }
      const copy1 = $.extend(true, {}, d);
      const copy2 = $.extend(true, {}, d);
      if (d.date in newData) {
        newData[d.date].ratio_items.push(copy1);
        newData[d.date].ratio_actual_cost.push(copy2);
      } else {
        newData[d.date] = {
          ratio_items: [copy1],
          ratio_actual_cost: [copy2],
        };
      }
    });
    let maxRatioItems = 0;
    let maxRatioActualCost = 0;
    for (const month in newData) {
      _.each(newData[month].ratio_items, (d) => {
        d.y = d.ratio_items;
        if (d.y > maxRatioItems) {
          maxRatioItems = d.y;
        }
      });
      _.each(newData[month].ratio_actual_cost, (d) => {
        d.y = d.ratio_actual_cost;
        if (d.y > maxRatioActualCost) {
          maxRatioActualCost = d.y;
        }
      });
      newData[month].ratio_items = this._sortAndIndex(
        newData[month].ratio_items
      );
      newData[month].ratio_actual_cost = this._sortAndIndex(
        newData[month].ratio_actual_cost
      );
    }
    return {
      barData: newData,
      maxRatioItems,
      maxRatioActualCost,
    };
  },

  _sortAndIndex(data) {
    const sortedData = _.sortBy(data, "y");
    for (let index = 0; index < sortedData.length; index++) {
      sortedData[index].x = index;
    }
    return sortedData;
  },
};

export default barChart;
