import downloadjs from "downloadjs";
import Highcharts from "Highcharts";
import csvUtils from "./csv-utils";
import chartOptions from "./highcharts-options";

function downloadCSVData(name, headers, rows) {
  const table = [headers].concat(rows);
  const csvData = csvUtils.formatTableAsCSV(table);
  const filename = csvUtils.getFilename(name);
  downloadjs(csvData, filename, "text/csv");
  return false;
}

function getElementCleanText() {
  return $(this).text().replace(/\s\s+/g, " ").trim();
}

$(() => {
  $(".js-submit-on-change").on("change", function () {
    this.form.submit();
  });

  function rowToPoint(row, valueKey) {
    const point = {
      date: parseDate(row.month),
      tariffCost: row.tariff_cost,
      addCost: row.additional_cost,
      isEstimate: row.is_estimate,
      isIncomplete: row.is_incomplete_month,
    };
    point.x = point.date;
    point.y = point[valueKey];
    return point;
  }

  function parseDate(dateStr) {
    const parts = dateStr.split("-");
    return Date.UTC(parts[0], parts[1] - 1, parts[2]);
  }

  const data = JSON.parse(
    document.getElementById("monthly-totals-data").innerHTML
  );
  let options = chartOptions.baseOptions;
  options = JSON.parse(JSON.stringify(options));

  const additionalCosts = data.map((row) => rowToPoint(row, "addCost"));
  const actualCosts = additionalCosts.filter(({ isEstimate }) => !isEstimate);
  const estimatedCosts = additionalCosts.filter(
    ({ isEstimate, isIncomplete }) => isEstimate && !isIncomplete
  );
  const incompleteCosts = additionalCosts.filter(
    ({ isEstimate, isIncomplete }) => isEstimate && isIncomplete
  );

  options.title.text = "Additional cost of price concessions";
  options.chart.type = "column";
  options.chart.marginBottom = 86;
  options.legend.layout = "horizontal";
  options.legend.align = "right";
  options.legend.verticalAlign = "bottom";
  options.legend.x = 0;
  options.legend.y = 4;
  options.legend.itemMarginBottom = 4;
  // Undo settings from highcharts-options and restore to defaults
  options.legend.itemStyle = { font: "", color: "#333", fontWeight: "normal" };
  options.plotOptions.series = { stacking: "normal" };
  options.yAxis.title = { enabled: true, text: "Cost (£)" };
  options.tooltip = {
    useHTML: true,
    style: {
      pointerEvents: "auto",
    },
    formatter() {
      const template =
        "<strong>{date}</strong><br>" +
        "<strong>£{value}</strong> {estimated} additional cost{incomplete}<br>" +
        '<a href="?breakdown_date={date_param}">View cost breakdown &rarr;</a>';
      const params = {
        "{date}": Highcharts.dateFormat("%B %Y", this.x),
        "{value}": Highcharts.numberFormat(this.y, 0),
        "{estimated}": this.point.isEstimate ? "projected" : "",
        "{incomplete}": this.point.isIncomplete
          ? "<br>based on concessions so far this month"
          : "",
        "{date_param}": Highcharts.dateFormat("%Y-%m-%d", this.x),
      };
      return template.replace(/{.+?}/g, (param) => params[param]);
    },
    valueDecimals: 0,
    valuePrefix: "£",
  };
  options.series = [
    { name: "Estimated cost", data: actualCosts, color: "rgba(0, 0, 255, .8)" },
    {
      name: "Projected cost",
      data: estimatedCosts,
      color: "rgba(255, 0, 0, .8)",
    },
    {
      name: "Projected cost (based on concessions so far this month)",
      data: incompleteCosts,
      color: "rgba(255, 128, 0, .8)",
    },
  ];
  const chart = Highcharts.chart("monthly-totals-chart", options);
});

$(() => {
  const breakdownData = JSON.parse(
    document.getElementById("breakdown-data").innerHTML
  );
  if (!breakdownData) return;
  const $wrapper = $("#breakdown-table-wrapper");
  const urlTemplate = breakdownData.url_template;
  const headers = $wrapper.find("table th").map(getElementCleanText).get();

  $wrapper.find("table").DataTable({
    data: breakdownData.table,
    pageLength: 25,
    order: [],
    columnDefs: [
      { targets: [0], visible: false },
      {
        targets: [1],
        render(data, type, row) {
          return `<a href="${urlTemplate.replace(
            "{bnf_code}",
            row[0]
          )}">${data}</a>`;
        },
      },
      { targets: [2, 3, 4], className: "text-right" },
      {
        targets: [2],
        render: $.fn.dataTable.render.number(",", ".", 0, ""),
      },
      {
        targets: [3, 4],
        render: $.fn.dataTable.render.number(",", ".", 0, "£"),
      },
    ],
  });

  $wrapper
    .find(".js-download-data")
    .on("click", () =>
      downloadCSVData(breakdownData.filename, headers, breakdownData.table)
    );

  $wrapper.removeClass("hide");
});
