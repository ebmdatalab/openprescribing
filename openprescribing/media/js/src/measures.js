import domready from "domready";
import Handlebars from "handlebars";
import Highcharts from "Highcharts";
import $ from "jquery";
import L from "mapbox.js";
import _ from "underscore";
import utils from "./chart_utils";
import chartOptions from "./highcharts-options";
import mu from "./measure_utils";

Highcharts.setOptions({
  global: { useUTC: false },
});

L.mapbox.accessToken = window.MAPBOX_PUBLIC_TOKEN;

const measures = {
  el: {
    chart: "#charts .chart",
    charts: "#charts",
    mapPanel: "map-measure",
    perfSummary: "#perfsummary",
    showAll: ".showall",
    sortButtons: ".btn-group > .btn",
    summaryTemplate: "#summary-panel",
    panelTemplate: "#measure-panel",
    noCostSavingWarning: "#no-cost-saving-warning",
  },

  setUp() {
    const _this = this;
    _this.isOldIe = utils.getIEVersion();
    const summaryTemplate = Handlebars.compile(
      $(_this.el.summaryTemplate).html()
    );
    const panelTemplate = Handlebars.compile($(_this.el.panelTemplate).html());
    const NUM_MONTHS_FOR_RANKING = 6;
    const centiles = ["10", "20", "30", "40", "50", "60", "70", "80", "90"];
    const selectedMeasure = window.location.hash.substring(1);
    _this.allGraphsRendered = false;
    _this.graphsToRenderInitially = 24;
    const options = JSON.parse(
      document.getElementById("measure-options").innerHTML
    );
    _this.setUpShowChildren();
    _this.setUpMap(options);

    $.when($.ajax(options.panelMeasuresUrl), $.ajax(options.globalMeasuresUrl))
      .done((panelMeasures, globalMeasures) => {
        let chartData = panelMeasures[0].measures;
        const globalData = globalMeasures[0].measures;

        _.extend(
          options,
          mu.getCentilesAndYAxisExtent(globalData, options, centiles)
        );
        chartData = mu.annotateData(chartData, options, NUM_MONTHS_FOR_RANKING);
        chartData = mu.addChartAttributes(
          chartData,
          globalData,
          options.globalCentiles,
          centiles,
          options,
          NUM_MONTHS_FOR_RANKING
        );
        chartData = mu.sortData(chartData);
        const perf = mu.getPerformanceSummary(
          chartData,
          options,
          NUM_MONTHS_FOR_RANKING
        );
        $(_this.el.perfSummary).html(summaryTemplate(perf));
        let html = "";
        _.each(chartData, (d) => {
          html = panelTemplate(d);
          $(d.chartContainerId).append(html);
        });
        $(_this.el.charts)
          .find("a[data-download-chart-id]")
          .on("click", function () {
            return _this.handleDataDownloadClick(
              chartData,
              $(this).data("download-chart-id")
            );
          });
        _.each(chartData, (d, i) => {
          if (i < _this.graphsToRenderInitially) {
            const chOptions = mu.getGraphOptions(
              d,
              options,
              d.is_percentage,
              chartOptions
            );
            if (chOptions) {
              new Highcharts.Chart(chOptions);
            }
          }
        });
        $(".loading-wrapper").hide();
        // On long pages, render remaining graphs only after scroll,
        // to stop the page choking on first load.
        $(window).scroll(() => {
          if (_this.allGraphsRendered === false) {
            _.each(chartData, (d, i) => {
              if (i >= _this.graphsToRenderInitially) {
                const chOptions = mu.getGraphOptions(
                  d,
                  options,
                  d.is_percentage,
                  chartOptions
                );
                if (chOptions) {
                  new Highcharts.Chart(chOptions);
                }
              }
            });
            _this.allGraphsRendered = true;
          }
        });

        if (options.rollUpBy === "measure_id") {
          _this.setUpSortGraphs();
        }
        _this.highlightSelectedMeasure(selectedMeasure);
        if (location.search.includes("sortBySavings")) {
          $(_this.el.sortButtons).click();
        }
      })
      .fail((jqXHR, textStatus, error) => {
        console.log(`Error ${error} when making request ${jqXHR}`);
      });
  },

  highlightSelectedMeasure(selectedMeasure) {
    if (!selectedMeasure || selectedMeasure === "") return;
    const measureEl = document.getElementById(`measure_${selectedMeasure}`);
    if (!measureEl) return;
    const $measureEl = $(measureEl);
    $("#overlay").fadeIn(300);
    $measureEl.css("z-index", "99999");
    $("html, body").animate(
      {
        scrollTop: $measureEl.offset().top,
      },
      1000
    );
    $("#overlay").on("click", () => {
      $("#overlay").stop().fadeOut(300);
    });
  },

  setUpShowChildren() {
    $(this.el.showAll).on("click", function (e) {
      console.log("click");
      e.preventDefault();
      $(this)
        .closest(".child-entity-list")
        .find(".hidden")
        .removeClass("hidden");
      $(this).hide();
    });
  },

  setUpMap(options) {
    const _this = this;
    if ($(`#${_this.el.mapPanel}`).length) {
      const maxZoom = _this.zoomLevelForOrgType(options.orgType);
      const map = L.mapbox.map(_this.el.mapPanel, null, { zoomControl: false });
      map.setView([52.905, -1.79], maxZoom);
      map.addLayer(L.mapbox.styleLayer("mapbox://styles/mapbox/streets-v11"));
      map.scrollWheelZoom.disable();
      const layer = L.mapbox
        .featureLayer()
        .loadURL(options["orgLocationUrl"])
        .on("ready", () => {
          if (layer.getBounds().isValid()) {
            map.fitBounds(layer.getBounds(), { maxZoom });
            layer.setStyle({
              fillColor: "#ff00ff",
              fillOpacity: 0.2,
              weight: 0.5,
              color: "#333",
              radius: 10,
            });
          } else {
            $("#map-container").html("");
          }
        })
        .addTo(map);
    }
  },

  zoomLevelForOrgType(orgType) {
    switch (orgType) {
      case "practice":
        return 12;
      case "pcn":
        return 7;
      default:
        return 5;
    }
  },

  setUpSortGraphs() {
    const _this = this;
    const chartsByPercentile = $(_this.el.chart);
    const nonCostSavingCharts = $(chartsByPercentile).filter(function (a) {
      return !$(this).data("costsaving");
    });
    chartsBySaving = $(_this.el.chart).sort(
      (a, b) => $(b).data("costsaving") - $(a).data("costsaving")
    );
    if (nonCostSavingCharts.length === chartsByPercentile.length) {
      chartsBySaving = chartsBySaving.add(
        $(_this.el.noCostSavingWarning).clone().removeClass("hidden")
      );
    }
    $(_this.el.sortButtons).click(function () {
      $(this).addClass("active").siblings().removeClass("active");
      if ($(this).data("orderby") === "savings") {
        $(_this.el.charts).fadeOut(() => {
          nonCostSavingCharts.hide();
          $(_this.el.charts).html(chartsBySaving).fadeIn();
        });
      } else {
        $(_this.el.charts).fadeOut(() => {
          nonCostSavingCharts.show();
          $(_this.el.charts).html(chartsByPercentile).fadeIn();
        });
      }
    });
  },

  handleDataDownloadClick(chartData, chartId) {
    const browserSupported = !this.isOldIe;
    ga("send", {
      hitType: "event",
      eventCategory: "measure_data",
      eventAction: browserSupported ? "download" : "failed_download",
      eventLabel: chartId,
    });
    if (browserSupported) {
      mu.startDataDownload(chartData, chartId);
    } else {
      window.alert("Sorry, you must use a newer web browser to download data");
    }
    return false;
  },
};

domready(() => {
  measures.setUp();
});
