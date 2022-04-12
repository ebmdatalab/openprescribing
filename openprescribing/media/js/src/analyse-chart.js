import "bootstrap";
import Cookies from "cookies-js";
import downloadjs from "downloadjs";
import Highcharts from "Highcharts";
import $ from "jquery";
import _ from "underscore";
import barChart from "./analyse-bar-chart";
import hashHelper from "./analyse-hash";
import lineChart from "./analyse-line-chart";
import map from "./analyse-map";
import formatters from "./chart_formatters";
import utils from "./chart_utils";
import chartOptions from "./highcharts-options";

Highcharts.setOptions({
  global: { useUTC: false },
});

const analyseChart = {
  el: {
    resultsEl: $("#results"),
    chartEl: $("#chart"),
    errorContainer: $("#error"),
    errorMessage: $("#error-message"),
    highlightOrgType: $("#highlightType"),
    highlightNotFound: $("#itemNotFound"),
    loadingEl: $(".loading-wrapper"),
    loadingMessage: $("#chart-loading p"),
    slider: $("#chart-date-slider"),
    playslider: $("#play-slider"),
    submitButton: $("#update"),
    tabs: $("#tabs li"),
    tabChart: $("#chart-tab"),
    tabMap: $("#map-tab"),
    tabSummary: $("#summary-tab"),
    tabPanelChart: $("#chart-panel"),
    title: ".chart-title",
    subtitle: ".chart-sub-title",
    rowCount: "#data-rows-count",
    alertForm: "#alert-form",
    outliersToggle: ".outliers-toggle",
    summaryTotals: $("#js-summary-totals"),
  },

  renderChart(globalOptions) {
    // console.log('renderChart', globalOptions);
    // For older Internet Explorer, we deliberately want to
    // delay execution in places, to prevent slow-running script errors.
    this.isOldIe = utils.getIEVersion();
    this.scriptDelay = this.isOldIe ? 1500 : 0;
    this.globalOptions = globalOptions;
    this.el.submitButton.button("loading");
    this.el.errorContainer.hide();
    this.el.summaryTotals.hide();
    this.el.loadingEl.show();
    this.getBackendData();
  },

  clearAllData() {
    this.globalOptions.data.numeratorData = [];
    this.globalOptions.data.denominatorData = [];
    this.globalOptions.data.combinedData = [];
    $("#data-link").off();
  },

  showErrorMessage(status, error) {
    let errorHtml;
    if (error !== null) {
      errorHtml +=
        '<p class="alert alert-danger">Sorry, something went wrong.</p>';
      errorHtml += `<p>This is what we know: ${status}: ${error}</p>`;
    } else {
      errorHtml = `<p class='alert alert-danger'>${status}</p>`;
    }
    this.el.errorMessage.html(errorHtml);
    this.el.errorContainer.show();
    this.el.resultsEl.hide();
    this.el.loadingEl.hide();
    this.el.submitButton.button("reset");
  },

  getBackendData() {
    this.clearAllData();
    this.globalOptions.urls = utils.constructQueryURLs(this.globalOptions);
    const _this = this;
    _this.el.loadingMessage.text("Fetching data...");
    $.when(
      $.ajax(_this.globalOptions.urls.numeratorUrl),
      $.ajax(_this.globalOptions.urls.denominatorUrl)
    )
      .done((response1, response2) => {
        _this.el.loadingMessage.text("Parsing data...");
        _this.globalOptions.data.numeratorData = response1[0];
        _this.globalOptions.data.denominatorData = response2[0];
        _this.el.loadingMessage.text("Rendering chart...");
        setTimeout(() => {
          _this.loadChart();
        }, _this.scriptDelay);
      })
      .fail((status, error) => {
        const msg = _.has(status, "responseText")
          ? status.responseText
          : "Sorry, something went wrong.";
        _this.showErrorMessage(msg.replace(/"/g, ""), null);
      });
  },

  setOutlierLinkText() {
    const _this = this;
    const link = $(_this.el.outliersToggle).find("a");
    const items = $(_this.el.outliersToggle).find("span.outliers");
    let outliers = _.values(this.globalOptions.skippedOutliers);
    let pronoun;
    if (outliers.length === 1) {
      pronoun = "it";
    } else {
      pronoun = "them";
    }
    outliers = [outliers.slice(0, -1).join(", "), outliers.slice(-1)[0]].join(
      outliers.length < 2 ? "" : " and "
    );
    items.html(outliers);
    if (this.globalOptions.hideOutliers) {
      link.text(`Show ${pronoun} in the charts anyway.`);
    } else {
      link.text(`Remove ${pronoun} from the chart.`);
    }
  },

  loadChart() {
    const _this = this;
    this.el.submitButton.button("reset");
    this.globalOptions.activeOption = "items";

    // Set option that defines if we should show a link to show or
    // hide practices with ratios suggestive of small list sizes...
    if (typeof _this.el.outliersToggle === "undefined") {
      // Defined on page load when provided as a query param in the
      // URL.
      if (Cookies.get("hide_small_lists") === "1") {
        this.globalOptions.hideOutliers = true;
      } else {
        this.globalOptions.hideOutliers = false;
      }
    }
    this.setUpData();
    if (this.globalOptions.hasOutliers) {
      _this.setOutlierLinkText();
      $(_this.el.outliersToggle).show();
    }
    this.globalOptions.allMonths = utils.getAllMonthsInData(this.globalOptions);
    this.globalOptions.activeMonth =
      this.globalOptions.allMonths[this.globalOptions.allMonths.length - 1];
    this.globalOptions.friendly = formatters.getFriendlyNamesForChart(
      this.globalOptions
    );
    this.hash = hashHelper.setHashParams(this.globalOptions);
    this.hash += $(this.el.submitButton).data("clicked")
      ? "&source=button"
      : "&source=pageload";
    ga("send", "pageview", `/analyse_dummy_search?${this.hash}`);
    ga("send", {
      hitType: "event",
      eventCategory: "search_button",
      eventAction: "click",
      eventLabel: _this.hash,
    });
    if (this.globalOptions.data.combinedData.length > 0) {
      this.el.loadingEl.hide();
      this.el.resultsEl.show();
      this.globalOptions.barChart = barChart.setUp(
        chartOptions.barOptions,
        this.globalOptions
      );
      if (this.isOldIe) {
        $("#data-link")
          .replaceWith(
            "<div class='alert alert-danger'>Sorry, you must use a newer web browser to make use of this feature</strong>"
          )
          .show();
      } else {
        this.addDataDownload();
      }
      // For now, don't render the map and line chart in older browsers -
      // they are just too slow.
      // This could be fixed by adding more pauses in the data calculations,
      // and making the data calculations more efficient.
      if (!this.isOldIe) {
        $(_this.el.tabChart).removeClass("hidden");
        $(_this.el.tabMap).removeClass("hidden");
        _this.globalOptions.lineChart = lineChart.setUp(
          chartOptions.lineOptions,
          _this.globalOptions
        );
        map.setup(_this.globalOptions);
      }
      // TODO: Text for tabs. Tidy this up.
      let summaryTab = "";
      const numOrgs = this.globalOptions.orgIds.length;
      if (this.globalOptions.org === "practice") {
        if (numOrgs) {
          const isPractice = this.globalOptions.orgIds[0].id.length > 3;
          summaryTab = isPractice ? "Show vs others in CCG" : "Show summary";
        } else {
          summaryTab = "Show for all CCGs";
        }
      } else {
        const orgTypeName = formatters.getFriendlyOrgType(
          this.globalOptions.org
        );
        summaryTab = `${
          (numOrgs ? "Show vs other " : "Show all ") + orgTypeName
        }s`;
      }
      $(this.el.tabSummary).find("a").text(summaryTab);
      $(_this.el.title).html(_this.globalOptions.friendly.chartTitle);
      $(_this.el.subtitle).html(_this.globalOptions.friendly.chartSubTitle);
      this.setUpSlider();
      this.setUpChartEvents();
      this.setUpSaveUrl();
      this.setUpSaveUrlUI();
      this.setUpAlertSubscription();
      this.displayTotals();
    } else {
      this.showErrorMessage(
        "No data found for this query. Please try again.",
        null
      );
    }
  },

  setUpData() {
    // console.log('setUpData');
    const xData = this.globalOptions.data.denominatorData;
    const yData = this.globalOptions.data.numeratorData;
    this.globalOptions.chartValues = utils.setChartValues(this.globalOptions);
    // Combines the datasets and calculates the ratios.
    const combinedData = utils.combineXAndYDatasets(
      xData,
      yData,
      this.globalOptions
    );
    this.globalOptions.data.combinedData = combinedData;
  },

  setUpAlertSubscription() {
    // Record the current encoded analysis in the hidden URL field
    // in custom alerts signup form
    const _this = this;
    const alertForm = $(_this.el.alertForm);
    const title = encodeURIComponent(
      _this.globalOptions.friendly.chartTitle.replace(/<br\/>/g, "")
    );
    alertForm.find('[name="url"]').val(this.hash);
    alertForm.find('[name="name"]').val(title);
    alertForm.show();
  },

  setUpSaveUrlUI() {
    // Don't hide the dropdown modal after a "copy-to-clipboard"
    // click; on any other click, do hide it.
    $(".save-url-button.dropdown").on("hide.bs.dropdown", () => {
      let close = true;
      const btn = $(".save-url-dropdown .btn");
      if (btn.data("clicked")) {
        btn.removeData("clicked");
        close = false;
      }
      return close;
    });
    $(".save-url-dropdown .btn").on("click", function () {
      $(this).data("clicked", true);
    });

    // Move the button to the currently selected tab
    $(".save-url-button").hide();
    $(".save-url-button").appendTo(".nav-tabs .active.saveable").show();

    // Set up the clipboard functionality, including a fallback for
    // unsupported browsers
    if (!utils.getIEVersion()) {
      const clipboard = new Clipboard(".save-url-dropdown .btn");
      clipboard.on("success", () => {
        $("#save-url-text").attr("title", "Copied!").tooltip().tooltip("show");
      });
      clipboard.on("error", () => {
        let errorMsg = "";
        if (/iPhone|iPad/i.test(navigator.userAgent)) {
          errorMsg = "No support :(";
        } else if (/Mac/i.test(navigator.userAgent)) {
          errorMsg = "Press ⌘-C to copy";
        } else {
          errorMsg = "Press Ctrl-C to copy";
        }
        $("#save-url-text").attr("title", errorMsg).tooltip("show");
      });
    }
  },

  addDataDownload() {
    const _this = this;
    const csvHeader = ["date", "id", "name", "y_items", "y_actual_cost"];
    let sampleItem;
    let csvRows;
    let encodedUri;
    let filename;
    sampleItem = this.globalOptions.data.combinedData[0];
    if ("astro_pu_cost" in sampleItem) {
      csvHeader.push("astro_pu_cost");
    } else if ("total_list_size" in sampleItem) {
      csvHeader.push("total_list_size");
    } else if ("star_pu.oral_antibacterials_item" in sampleItem) {
      csvHeader.push("star_pu.oral_antibacterials_item");
    } else {
      csvHeader.push("x_items");
      csvHeader.push("x_actual_cost");
    }
    csvRows = [csvHeader.join(",")];
    _.each(this.globalOptions.data.combinedData, (d) => {
      let str = "";
      _.each(csvHeader, (i, count) => {
        str += i === "name" ? '"' : "";
        str += d[i];
        str += i === "name" ? '"' : "";
        str += count !== csvHeader.length - 1 ? "," : "";
      });
      csvRows.push(str);
    });
    encodedUri = `data:text/csv,${encodeURIComponent(csvRows.join("\n"))}`;
    filename = `${this.globalOptions.friendly.filename}.csv`;
    $("#data-link").on("click", (e) => {
      e.preventDefault();
      ga("send", {
        hitType: "event",
        eventCategory: "data_link",
        eventAction: "click",
        eventLabel: _this.hash,
      });
      downloadjs(encodedUri, filename, "text/csv");
    });
    $(this.el.rowCount).text(
      `(${this.globalOptions.data.combinedData.length} rows)`
    );
    $("#data-link").show();
  },

  setUpSaveUrl() {
    // Set the input box URL, and make it selected on click
    $("#save-url-text")
      .val(window.location.href)
      .click(function () {
        $(this).select();
      });
  },

  setUpChartEvents() {
    const _this = this;
    // Tab clicks.
    $(document).on("shown.bs.tab", 'a[data-toggle="tab"]', function (e) {
      $(window).resize(); // CSS hack.
      const chart = _this.el.chartEl.highcharts();
      if (typeof chart != "undefined") {
        // Don't break in IE8
        chart.reflow();
      }
      const target = $(this).data("target");
      if (target === "#chart-panel" || target === "#data-panel") {
        // Only show the time slider for the "show over time" panel
        $("#chart-options").hide();
      } else {
        $("#chart-options").show();
      }
      if (target === "#map-panel") {
        if (!_this.isOldIe) {
          map.resize();
        }
      }
      // update the URL
      const tabid = target.substring(1, target.length - 6);
      _this.globalOptions.selectedTab = tabid;
      _this.hash = hashHelper.setHashParams(_this.globalOptions);
      _this.setUpSaveUrl();
      _this.setUpSaveUrlUI();
      _this.setUpAlertSubscription();
    });
    // Outlier toggle
    $(_this.el.outliersToggle)
      .find(".toggle")
      .on("click", function (e) {
        e.preventDefault();
        if (_this.outlierToggleUpdating) return;
        _this.outlierToggleUpdating = true;
        if (_this.globalOptions.hasOutliers) {
          if (_this.globalOptions.hideOutliers) {
            _this.globalOptions.hideOutliers = false;
            Cookies.set("hide_small_lists", "0");
          } else {
            // set a cookie
            _this.globalOptions.hideOutliers = true;
            Cookies.set("hide_small_lists", "1");
          }
          _this.setOutlierLinkText();
          _this.hash = hashHelper.setHashParams(_this.globalOptions);
          _this.setUpData();
          _this.globalOptions.barChart = barChart.setUp(
            chartOptions.barOptions,
            _this.globalOptions
          );
          if (!this.isOldIe) {
            _this.globalOptions.lineChart = lineChart.setUp(
              chartOptions.lineOptions,
              _this.globalOptions
            );
            map.setup(_this.globalOptions).then(() => {
              _this.outlierToggleUpdating = false;
            });
          } else {
            _this.outlierToggleUpdating = false;
          }
        }
      });

    // Items/spending toggle.
    $("#items-spending-toggle .btn").on("click", function (e) {
      e.preventDefault();
      ga("send", {
        hitType: "event",
        eventCategory: "items_spending_toggle",
        eventAction: "click",
        eventLabel: _this.hash,
      });
      $("#items-spending-toggle .btn")
        .removeClass("btn-info")
        .addClass("btn-default");
      $(this).addClass("btn-info").removeClass("btn-default");
      _this.globalOptions.activeOption = $(this).data("type");
      _this.globalOptions.barChart.zoom();
      _this.updateCharts();
    });
    // select the correct view tab
    $(
      `a[data-toggle="tab"][href="#${this.globalOptions.selectedTab}-panel"]`
    ).tab("show");
  },

  updateCharts() {
    let yAxisMax;
    const _this = this;
    _this.globalOptions.chartValues = utils.setChartValues(_this.globalOptions);
    _this.globalOptions.friendly = formatters.getFriendlyNamesForChart(
      _this.globalOptions
    );
    $(_this.el.title).html(_this.globalOptions.friendly.chartTitle);
    $(_this.el.subtitle).html(_this.globalOptions.friendly.chartSubTitle);
    if (_this.globalOptions.chartValues.ratio === "ratio_actual_cost") {
      yAxisMax = _this.globalOptions.maxRatioActualCost;
    } else {
      yAxisMax = _this.globalOptions.maxRatioItems;
    }
    // console.log('ratio: ' + _this.globalOptions.chartValues.ratio);
    // console.log(_this.globalOptions);
    barChart.update(
      _this.globalOptions.barChart,
      _this.globalOptions.activeMonth,
      _this.globalOptions.chartValues.ratio,
      _this.globalOptions.friendly.yAxisTitle,
      _this.globalOptions.friendly.yAxisFormatter,
      _this.globalOptions.playing,
      yAxisMax
    );
    if (!_this.isOldIe) {
      map.updateMap(_this.globalOptions.activeOption, _this.globalOptions);
    }
  },

  setUpSlider() {
    const _this = this;
    const sliderMax = this.globalOptions.allMonths.length - 1;
    _this.el.playslider.on("click", (e) => {
      _this.globalOptions.playing = true;
      const _that = _this;
      const increment = (now, fx) => {
        $("#chart-date-slider").val(now);
        _that.onChange(true);
      };
      const complete = () => {
        _this.globalOptions.playing = false;
      };
      $({ n: 0 }).animate(
        { n: sliderMax },
        {
          duration: sliderMax * 400,
          step: increment,
          complete,
        }
      );
    });

    if (this.el.slider.val()) {
      this.el.slider.noUiSlider(
        {
          range: {
            min: 0,
            max: sliderMax,
          },
        },
        true
      );
      this.el.slider.val(sliderMax);
      this.el.slider.noUiSlider_pips({
        mode: "count",
        values: 10,
        density: 5,
        stepped: true,
        format: {
          to(val) {
            return formatDate(_this.globalOptions.allMonths[val]);
          },
          from(val) {
            return _this.globalOptions.allMonths.indexOf[val] + 1;
          },
        },
      });
    } else {
      this.el.slider
        .noUiSlider({
          step: 1,
          start: [sliderMax],
          range: {
            min: 0,
            max: sliderMax,
          },
        })
        .on({
          change() {
            _this.onChange($(this).val());
          },
        });
      this.el.slider.noUiSlider_pips({
        mode: "count",
        values: 10,
        density: 5,
        stepped: true,
        format: {
          to(val) {
            return formatDate(_this.globalOptions.allMonths[val]);
          },
          from(val) {
            return _this.globalOptions.allMonths.indexOf[val] + 1;
          },
        },
      });
    }
  },

  onChange(suppressAnalytics) {
    const _this = this;
    if (!suppressAnalytics) {
      ga("send", {
        hitType: "event",
        eventCategory: "time_slider",
        eventAction: "slide",
        eventLabel: _this.hash,
      });
    }
    const monthIndex = parseInt(this.el.slider.val());
    this.globalOptions.activeMonth = this.globalOptions.allMonths[monthIndex];
    this.updateCharts();
  },

  displayTotals() {
    const selectedOrgs = getOrgSelection(
      this.globalOptions.org,
      this.globalOptions.orgIds
    );
    const allMonths = this.globalOptions.allMonths;
    const lastMonth = allMonths[allMonths.length - 1];
    const twelveMonthsAgo = allMonths[allMonths.length - 12];
    const financialYearStart = getFinancialYearStart(lastMonth);
    const data = this.globalOptions.data.numeratorData;
    const activeMonth = this.globalOptions.activeMonth;
    let itemsMonthTotal = 0;
    let itemsYearTotal = 0;
    let itemsFinancialYearTotal = 0;
    let costMonthTotal = 0;
    let costYearTotal = 0;
    let costFinancialYearTotal = 0;
    let entry;
    for (let i = 0; i < data.length; i++) {
      entry = data[i];
      // We include an org both if its ID is selected, or if it is a practice
      // belonging to a CCG which is itself selected (only for practices do we
      // have this mixture of selected org types)
      if (
        selectedOrgs &&
        !selectedOrgs[entry.row_id] &&
        !selectedOrgs[entry.ccg]
      ) {
        continue;
      }
      if (entry.date === activeMonth) {
        itemsMonthTotal += entry.items;
        costMonthTotal += entry.actual_cost;
      }
      if (entry.date >= twelveMonthsAgo) {
        itemsYearTotal += entry.items;
        costYearTotal += entry.actual_cost;
        if (entry.date >= financialYearStart) {
          itemsFinancialYearTotal += entry.items;
          costFinancialYearTotal += entry.actual_cost;
        }
      }
    }
    const el = this.el.summaryTotals;
    el.find(".js-friendly-numerator").text(
      this.globalOptions.friendly.friendlyNumerator
    );
    el.find(".js-orgs-description").text(
      getOrgsDescription(this.globalOptions.org, this.globalOptions.orgIds)
    );
    el.find(".js-selected-month").text(formatDate(activeMonth));
    el.find(".js-financial-year-range").text(
      formatDateRange(financialYearStart, lastMonth)
    );
    el.find(".js-year-range").text(formatDateRange(twelveMonthsAgo, lastMonth));
    el.find(".js-cost-month-total").text(formatNum(costMonthTotal));
    el.find(".js-cost-year-total").text(formatNum(costYearTotal));
    el.find(".js-cost-financial-year-total").text(
      formatNum(costFinancialYearTotal)
    );
    el.find(".js-items-month-total").text(formatNum(itemsMonthTotal));
    el.find(".js-items-year-total").text(formatNum(itemsYearTotal));
    el.find(".js-items-financial-year-total").text(
      formatNum(itemsFinancialYearTotal)
    );
    el.show();
  },
};

function formatDate(dateStr) {
  return Highcharts.dateFormat("%b '%y", new Date(dateStr));
}

function formatNum(n) {
  return Highcharts.numberFormat(n, 0);
}

function getFinancialYearStart(dateStr) {
  const date = new Date(dateStr);
  // Months are zero-indexed so 3 is April
  const financialYear =
    date.getMonth() >= 3 ? date.getFullYear() : date.getFullYear() - 1;
  const yearStart = new Date(financialYear, 3, 1);
  return Highcharts.dateFormat("%Y-%m-%d", yearStart);
}

function formatDateRange(fromDateStr, toDateStr) {
  const fromDate = new Date(fromDateStr);
  const toDate = new Date(toDateStr);
  const formatStr =
    fromDate.getFullYear() === toDate.getFullYear() ? "%b" : "%b '%y";
  const fromDateFormatted = Highcharts.dateFormat(formatStr, fromDate);
  const toDateFormatted = Highcharts.dateFormat("%b '%y", toDate);
  if (fromDateStr !== toDateStr) {
    return `${fromDateFormatted}\u2014${toDateFormatted}`;
  } else {
    // Handle the case where the start and end of the range is the same
    return toDateFormatted;
  }
}

function getOrgSelection(orgType, orgs) {
  // Given the current behaviour of the Analyse form it shouldn't be possible
  // to get practice level data without selecting some practices, and it's
  // not obvious how we should handle this if we do
  if (orgs.length === 0) {
    if (orgType === "practice") {
      throw "Unhandled selection: all practices";
    } else {
      // A selection of "false" means "select everything"
      return false;
    }
  }
  const selectedOrgs = {};
  for (let i = 0; i < orgs.length; i++) {
    selectedOrgs[orgs[i].id] = true;
  }
  return selectedOrgs;
}

function getOrgsDescription(orgType, orgs) {
  const orgTypeName = formatters.getFriendlyOrgType(orgType);
  if (orgs.length === 0) return `all ${orgTypeName}s in NHS England`;
  return orgs.map(({ name }) => name).join(" + ");
}

export default analyseChart;
