import "bootstrap";
import domready from "domready";
import Highcharts from "Highcharts";
import "select2";
import _ from "underscore";
import chartOptions from "./highcharts-options";

const tariffChart = {
  reshapeData(data) {
    // Reshape data from API to a format that's easy to pass to
    // Highcharts
    const byVmpp = {};
    _.each(data, (d) => {
      const dates = d.date.split("-");
      const date = Date.UTC(dates[0], dates[1] - 1, dates[2]);
      if (!(d.vmpp in byVmpp)) {
        byVmpp[d.vmpp] = [];
      }
      byVmpp[d.vmpp].push({
        x: date,
        y: parseFloat(d.price_pence) / 100,
        tariff_category: d.tariff_category,
      });
      // Store price concession as a separate series
      const concessionKey = `${d.vmpp} (price concession)`;
      if (!(concessionKey in byVmpp)) {
        byVmpp[concessionKey] = [];
      }
      byVmpp[concessionKey].push({
        x: date,
        y: d.concession ? parseFloat(d.concession) / 100 : d.concession,
      });
    });
    return byVmpp;
  },

  hasConcession(vmppData) {
    return _.some(vmppData, ({ y }) => y > 0);
  },

  getZIndex(vmppdata) {
    // Show series with highest values nearest the front
    return _.max(_.pluck(vmppdata, "y"));
  },

  getMarkerSize(vmppdata) {
    // Normally, we don't show markers as they are quite ugly on
    // an area chart. However, if a series is only one item
    // long, you can't see it unless there is a marker.
    let markerSize = 0;
    if (_.filter(vmppdata, ({ y }) => y !== null).length < 2) {
      markerSize = 3;
    }
    return markerSize;
  },

  anySeriesHasDashStyle(data, style) {
    let hasStyle = false;
    try {
      _.each(data, ({ zones }) => {
        _.each(zones, ({ dashStyle }) => {
          if (dashStyle === style) {
            hasStyle = true;
            throw "found style";
          }
        });
      });
    } catch (e) {
      // style found
    }
    return hasStyle;
  },

  addDummySeriesForCategoryLabels(data) {
    // Given complete data series, return an array of strings
    // indicating any DT Categories that have been used in any of the
    // series. We use this array to decide which extra legend items to
    // display (e.g. to indicate that a dotted line means "Category
    // C")
    const _this = this;
    if (_this.anySeriesHasDashStyle(data, "line")) {
      data.push({ name: "Category A", data: [], color: "#fff" });
    }
    if (_this.anySeriesHasDashStyle(data, "dot")) {
      data.push({ name: "Category C", data: [], color: "#fff" });
    }
    if (_this.anySeriesHasDashStyle(data, "dash")) {
      data.push({ name: "Category M", data: [], color: "#fff" });
    }
    return data;
  },

  getCategoryZones(vmppdata) {
    // Zone calculations: line styles for highcharts, based on category
    const zones = [];
    let lastCat = null;
    let cat = null;
    let dashStyle;
    const dataWithDummy = vmppdata.concat([{ tariff_category: null }]);
    _.each(dataWithDummy, ({ tariff_category, x }) => {
      cat = tariff_category;
      if (!lastCat) {
        lastCat = cat;
      }
      if (cat !== lastCat) {
        switch (lastCat) {
          case "Part VIIIA Category A":
            dashStyle = "line";
            break;
          case "Part VIIIA Category C":
            dashStyle = "dot";
            break;
          case "Part VIIIA Category M":
            dashStyle = "dash";
            break;
          default:
          // do nothing
        }
        zones.push({ value: x, dashStyle });
      }
      lastCat = cat;
    });
    return zones;
  },

  initialiseData(data) {
    const _this = this;
    const byVmpp = this.reshapeData(data);
    // Decorate each series with extra Highcharts properties that are
    // computed based on all the values in that series; specifically,
    // a z-index which places series with highest values at the front,
    // and a "zoning" that allows us to indicate the Drug Tariff
    // Category of each presentation over time.
    const newData = [];
    const categoriesShown = [];
    for (const vmpp in byVmpp) {
      const isConcessionSeries = vmpp.includes("concession");
      if (byVmpp.hasOwnProperty(vmpp)) {
        if (isConcessionSeries && !_this.hasConcession(byVmpp[vmpp])) {
          continue;
        } else {
          const zIndex = _this.getZIndex(byVmpp[vmpp]);
          const markerSize = _this.getMarkerSize(byVmpp[vmpp]);
          const zones = _this.getCategoryZones(byVmpp[vmpp]);
          newData.push({
            name: vmpp,
            marker: { radius: markerSize },
            data: byVmpp[vmpp],
            zones,
            zoneAxis: "x",
            zIndex,
          });
        }
      }
    }
    // These dummy series are required so we can add dashed-line labels to the
    // legend
    return _this.addDummySeriesForCategoryLabels(newData);
  },

  initialiseChartOptions({ baseOptions }, { length }) {
    const options = baseOptions;
    options.chart.marginTop = 40;
    options.plotOptions = {
      series: {
        marker: {
          radius: 0,
        },
        fillOpacity: 0.4,
        connectNulls: false,
        pointPadding: 0,
        groupPadding: 0,
      },
    };
    options.chart.spacingTop = 20;
    options.chart.type = "area";
    options.title.text = chartTitle;
    // The following is a hack to show labels for the line-styling
    // which indicates DT Category (see dummary series above)
    options.legend = {
      useHTML: true,
      floating: false,
      symbolHeight: 0,
      symbolWidth: 0,
      itemMarginTop: 4,
      itemMarginBottom: 4,
      labelFormatter() {
        // The values for `stroke-dasharray` are taken from inspecting
        // the SVG generated by Highcharts fors its line, dash, and dot styles.
        let str = '<div><div style="width:30px;display:inline-block;';
        str += "padding:3px 2px 3px 2px;margin-right: 4px;text-align:center;";
        str += `color:#FFF;background-color:${this.color}">`;
        let stroke =
          '<svg width="30" height="5"><path d="M0 0 H30" stroke="black" ';
        stroke += 'stroke-width="2" stroke-dasharray="';
        if (this.name === "Category A") {
          str += `${stroke}none" /></svg>`;
        } else if (this.name === "Category C") {
          str += `${stroke}2,6" /></svg>`;
        } else if (this.name === "Category M") {
          str += `${stroke}8,6" /></svg>`;
        }
        str += "</div>";
        return str + this.name;
      },
    };
    options.tooltip = {
      pointFormatter() {
        let str = `<span style="color:${this.color}">\u25CF</span> `;
        str += `${this.series.name}: <b>£${this.y.toFixed(2)}`;
        if (this.tariff_category) {
          str += ` (${this.tariff_category}) `;
        }
        str += "</b><br/>";
        return str;
      },
    };
    // A legend is redudant when there is only one series shown
    if (length > 1) {
      options.legend.enabled = true;
    } else {
      options.legend.enabled = false;
    }
    options.yAxis.title = {
      text: "Price (£)",
    };
    return options;
  },

  setUp() {
    const _this = this;
    $(".tariff-selector").select2({
      placeholder: "Start typing a presentation name",
    });

    if (bnfCodes == "") {
      return;
    }

    $.ajax({
      type: "GET",
      url: `${baseUrl}?format=json&codes=${bnfCodes}`,
      error() {
        $(".status").html("<p>Sorry, something went wrong.</p>");
      },
      success(response) {
        $(".status").hide();
        const data = _this.initialiseData(response);
        let newChartOptions = chartOptions;
        newChartOptions = _this.initialiseChartOptions(newChartOptions, data);
        if (data.length) {
          $("#tariff").show();
          newChartOptions.series = data;
          const chart = new Highcharts.Chart(newChartOptions);
        } else {
          $("#tariff").hide();
          $("#no-data").show();
        }
      },
    });
  },
};

domready(() => {
  tariffChart.setUp();
});
