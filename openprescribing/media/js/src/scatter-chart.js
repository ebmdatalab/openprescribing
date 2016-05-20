var utils = require('./chart_utils');

var scatterChart = {
  setUp: function(chartOptions, globalOptions) {
        // console.log('denominatorData', this.globalOptions.data.denominatorData[0]);
        // console.log('numeratorData', this.globalOptions.data.numeratorData[0]);
        // Set up chart options.
    var _this = this;
    var scatterOptions = chartOptions.scatterOptions;
    scatterOptions.series = utils.createChartSeries(this.globalOptions.data.summedData, this.globalOptions);
        // console.log('series[0]', scatterOptions.series[0]);
    scatterOptions.legend.enabled = false;
    scatterOptions.title.text = _this.globalOptions.chartTitle;
    scatterOptions.xAxis.title = {
      text: utils.constructXAxisTitle(this.globalOptions)
    };
    this.globalOptions.yAxisTitle = utils.constructYAxisTitle(this.globalOptions);
    scatterOptions.yAxis.title = {
      text: this.globalOptions.yAxisTitle
    };
        // if (this.globalOptions.scale === 'log') {
        //     scatterOptions.xAxis.type = 'logarithmic';
        //     scatterOptions.xAxis.min = 0.1;
        //     scatterOptions.yAxis.type = 'logarithmic';
        //     scatterOptions.yAxis.min = 0.1;
        //     this.el.scaleisLog.addClass('btn-info').removeClass('btn-default');
        //     this.el.scaleIsLinear.removeClass('btn-info').addClass('btn-default');
        // } else {
        //     scatterOptions.xAxis.type = 'linear';
        //     scatterOptions.xAxis.min = 0;
        //     scatterOptions.yAxis.type = 'linear';
        //     scatterOptions.yAxis.min = 0;
        //     this.el.scaleisLog.removeClass('btn-info').addClass('btn-default');
        //     this.el.scaleIsLinear.addClass('btn-info').removeClass('btn-default');
        // }
    this.el.loadingEl.hide();
    this.el.chartContainerEl.show();
    if ((this.globalOptions.denom == 'total_list_size') || (this.globalOptions.denom == 'astro_pu_cost')) {
      scatterOptions.xAxis.labels.formatter = null;
    } else {
      scatterOptions.xAxis.labels.formatter = function() {
        return '£' + this.axis.defaultLabelFormatter.call(this);
      };
    }
    this.globalOptions.chart = new Highcharts.Chart(scatterOptions);

        // Update the type of organisation that the user can highlight.
    this.el.highlightOrgType.text(this.globalOptions.org);
  }

    // initialiseHighlightOrgs: function() {
    //     var orgs = utils.getUniqueRowNames(this.globalOptions.data.activeMonthData);
    //     var $chartOrgs = $('#all-ccgs');
    //     $chartOrgs.html('');
    //     var options = '';
    //     _.each(orgs, function(d) {
    //         options += '<option value="' + d.id + '">' + d.name;
    //         options += ' (' + d.id + ')</option>';
    //     });
    //     $chartOrgs.append(options);
    // },
    //
    // setUpLogScaleButton: function() {
    //     // Not currently used.
    //     var _this = this;
    //     this.el.scaleButton.off('click');
    //     this.el.scaleButton.on('click', function() {
    //         $(this).find('.btn').toggleClass('btn-info btn-default');
    //         _this.globalOptions.scale = $(this).find('.btn-info').attr('id');
    //         _this.setUpChart();
    //         _this.highlightPointsInChart();
    //     });
    // },


    // setUpHighlightPoints: function() {
    //     // var _this = this;
    //     // _this.initialiseHighlightOrgs();
    //     // var forage = localforage.getItem('highlightPoints', function(err, values) {
    //     //     var points = values || [];
    //     //     points.forEach(function(e) {
    //     //         $("#all-ccgs option[value='" + e + "']").prop("selected", true);
    //     //     });
    //     //     _this.globalOptions.highlightedPoints = points;
    //     //     $('#all-ccgs').select2({
    //     //         allow_single_deselect: true
    //     //     }).change(function() {
    //     //         var codes = ($(this).val()) ? $(this).val() : [];
    //     //         _this.globalOptions.highlightedPoints = codes;
    //     //         _this.highlightPointsInChart();
    //     //         localforage.setItem('highlightPoints', codes);
    //     //     });
    //     //     _this.highlightPointsInChart();
    //     // });
    // },

    // highlightPointsInChart: function() {
    //     // console.log('highlightPointsInChart');
    //     var _this = this;
    //     _this.el.highlightNotFound.hide();
    //     // Remove hover state from all points in chart.
    //     var allPoints = _this.globalOptions.chart.series[0].data;
    //     _.each(allPoints, function(point) {
    //         if (_this.globalOptions.highlightedPoints.indexOf(point.id) > -1) {
    //             point.select(true, true);
    //         } else {
    //             point.select(false, true);
    //         }
    //     });
    //     _this.globalOptions.chart.tooltip.hide();
    // },

    // scaleButton: $('#useLogScale'),
    // scaleIsLog: $('#log'),
    // scaleIsLinear: $('#linear'),
};

module.exports = scatterChart;
