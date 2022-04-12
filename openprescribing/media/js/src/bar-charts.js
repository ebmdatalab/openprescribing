import domready from "domready";
import Highcharts from "Highcharts";
import $ from "jquery";
import _ from "underscore";
import chartOptions from "./highcharts-options";

let newChartOptions = chartOptions;

const barChart = {
  initialiseData(data) {
    _.each(data, (d) => {
      const dates = d.date.split("-");
      const date = Date.UTC(dates[0], dates[1] - 1, dates[2]);
      d.x = date;
      d.actual_cost = parseFloat(d.actual_cost);
      d.items = parseFloat(d.items);
    });
    return data;
  },

  getYValueOfData(data, graphType) {
    _.each(data, (d) => {
      d.y = d[graphType];
    });
    return data;
  },

  getChartTitle(graphType) {
    let title = "Total ";
    title += graphType === "actual_cost" ? "spending" : "items";
    if (pageType !== "ccg" && pageType !== "practice") {
      title += " across all practices in England";
    }
    return title;
  },

  getYAxisTitle(graphType) {
    const title = graphType === "actual_cost" ? "Spending" : "Items";
    return title;
  },

  initialiseChartOptions({ baseOptions }, graphType) {
    const _this = this;
    const options = baseOptions;
    options.chart.showCrosshair = false;
    options.chart.marginTop = 40;
    options.chart.spacingTop = 20;
    options.chart.type = "column";
    options.legend.enabled = false;
    options.yAxis.title = {
      text: _this.getYAxisTitle(graphType),
    };
    options.yAxis.labels = {
      formatter() {
        const str = _this.graphType == "actual_cost" ? "£" : "";
        return str + this.axis.defaultLabelFormatter.call(this);
      },
    };
    options.title.text = _this.getChartTitle(graphType);
    options.tooltip = {
      formatter() {
        let str = "<b>";
        str += _this.graphType === "actual_cost" ? "£" : "";
        str += Highcharts.numberFormat(this.y, 0);
        str += _this.graphType === "actual_cost" ? "" : " items";
        str += "</b>";
        str += ` in ${Highcharts.dateFormat("%b '%y", new Date(this.x))}`;
        return str;
      },
    };
    return options;
  },

  updateChart(data, graphType, chart) {
    const _this = this;
    _this.graphType = graphType;
    const newYAxisOptions = {
      title: {
        text: _this.getYAxisTitle(graphType),
      },
    };
    chart.yAxis[0].update(newYAxisOptions, false);
    const newData = _this.getYValueOfData(data, graphType);
    // See: https://api.highcharts.com/class-reference/Highcharts.Series#setData
    // args below are: redraw=false, animation=false, updatePoints=false
    chart.series[0].setData(newData, false, false, false);
    chart.setTitle({ text: _this.getChartTitle(graphType) }, false);
    chart.redraw();
  },

  setUp() {
    const _this = this;
    _this.graphType = "items";
    $.ajax({
      type: "GET",
      url: filename,
      error() {
        $(".status").html("<p>Sorry, something went wrong.</p>");
      },
      success(response) {
        $(".status").hide();
        newChartOptions = _this.initialiseChartOptions(
          newChartOptions,
          _this.graphType
        );
        let data = _this.initialiseData(response);
        data = _this.getYValueOfData(data, _this.graphType);
        if (data.length) {
          $("#trends").show();
          newChartOptions.series = [
            {
              name: _this.graphType,
              data: data,
            },
          ];
          const chart = new Highcharts.Chart(newChartOptions);
          // Bind events.
          $("#graphtype .btn").on("click", function (e) {
            e.preventDefault();
            $("#graphtype .btn")
              .removeClass("btn-info")
              .addClass("btn-default");
            $(this).addClass("btn-info").removeClass("btn-default");
            _this.graphType = $(this).data("type");
            _this.updateChart(data, _this.graphType, chart);
          });
        } else {
          $("#trends, #download-data").hide();
          $("#no-data").show();
        }
      },
    });
  },
};

domready(() => {
  barChart.setUp();
});
