var _ = require('underscore');
var humanize = require('humanize');

var formatters = {

  getFriendlyNamesForChart: function(options) {
    var f = {};
    f.friendlyOrgs = this.getFriendlyOrgs(options.org, options.orgIds);
    f.friendlyNumerator = this.getFriendlyNumerator(options.numIds);
    f.friendlyDenominator = this.getFriendlyDenominator(options.denom,
                                                            options.denomIds);
    f.partialDenominator = this.getPartialDenominator(options.activeOption,
                                                          options.denom,
                                                          f.friendlyDenominator);
    f.fullDenominator = this.getFullDenominator(options.activeOption,
                                                    options.denom,
                                                    f.friendlyDenominator);
    f.chartTitle = this.constructChartTitle(options.activeOption,
                                            options.denom,
                                                f.friendlyNumerator,
                                                f.friendlyDenominator,
                                                f.friendlyOrgs);
    f.chartSubTitle = this.constructChartSubTitle(options.activeMonth);
    f.yAxisTitle = this.constructYAxisTitle(options.activeOption,
                                            options.denom,
                                            f.friendlyNumerator,
                                            f.fullDenominator);
    f.filename = this.constructFilename(options.activeOption,
                                        f.friendlyNumerator,
                                        f.fullDenominator);
    f.yAxisFormatter = this.getYAxisLabelFormatter(options.chartValues);
    return f;
  },

  getFriendlyOrgs: function(org, orgIds) {
    var str = '';
    if (org === 'all') {
      str = 'all practices in NHS England';
    } else {
      if (org === 'practice' && orgIds.length > 0) {
        str = this._getStringForIds(orgIds, true);
        if (_.any(_.map(orgIds, function(d) { return d.id.length > 3; }))) {
          str += ' <br/>and other practices in CCG';
        }
      } else {
        if (orgIds.length > 0) {
          str = this._getStringForIds(orgIds, false);
          str += ' <br/>and other ' + this.getFriendlyOrgType(org) + 's';
        } else {
          str = 'all ' + this.getFriendlyOrgType(org) + 's';
        }
      }
    }
    return str;
  },

  getFriendlyOrgType: function(orgType) {
    switch(orgType) {
      case 'practice':
        return 'practice';
      case 'ccg':
      case 'CCG':
        return 'CCG';
      case 'stp':
        return 'STP';
      case 'regional_team':
        return 'regional team';
      default:
        throw 'Unhandled orgType: ' + orgType;
    }
  },

  getFriendlyNumerator: function(numIds) {
    var str = '';
    if (numIds.length > 0) {
      str += this._getStringForIds(numIds, false);
    } else {
      str += 'all prescribing';
    }
    return str;
  },

  getFriendlyDenominator: function(denom, denomIds) {
    var str = '';
    if (denom === 'total_list_size') {
      str = 'patients on list';
    } else if (denom === 'astro_pu_cost') {
      str = 'ASTRO-PUs';
    } else if (denom === 'star_pu.oral_antibacterials_item') {
      str = 'STAR-PUs for oral antibiotics';
    } else {
      if (denomIds.length > 0) {
        str = this._getStringForIds(denomIds, false);
      } else {
        str = 'all prescribing';
      }
    }
    return str;
  },

  getPartialDenominator: function(activeOption, denom, friendlyDenominator) {
    var str;
    if (denom === 'chemical') {
      str = (activeOption == 'items') ? 'Items for ' : 'Spend on ';
      str += friendlyDenominator;
    } else {
      str = friendlyDenominator;
    }
    return str;
  },

  getFullDenominator: function(activeOption, denom, denomStr) {
    var str;
    if (denom === 'chemical') {
      str = (activeOption === 'items') ? '1,000 items for ' : '£1,000 spend on ';
      str += denomStr;
    } else if (denom == 'nothing') {
      str = '';
    } else {
      str = ' 1,000 ' + denomStr;
    }
    return str;
  },

  constructChartTitle: function(activeOption, denom, numStr, denomStr, orgStr) {
    var chartTitle = (activeOption == 'items') ? 'Items for ' : 'Spend on ';
    chartTitle += numStr;
    chartTitle += (chartTitle.length > 40) ? '<br/>' : '';
    if (denom !== 'nothing') {
      chartTitle += ' vs ' + denomStr + '<br/>';
    }
    chartTitle += ' by ' + orgStr;
    return chartTitle;
  },

  constructChartSubTitle: function(month) {
    var monthDate = (month) ? new Date(month.replace(/-/g, '/')) : month;
    var subTitle = 'in ';
    subTitle += (typeof Highcharts !== 'undefined') ? Highcharts.dateFormat('%b \'%y', monthDate) : month;
    return subTitle;
  },

  constructYAxisTitle: function(activeOption, denom, friendlyNumerator, fullDenominator) {
    var axisTitle = (activeOption == 'items') ? 'Items for ' : 'Spend on ';
    axisTitle += friendlyNumerator;
    if (denom !== 'nothing') {
      axisTitle += '<br/> per ' + fullDenominator;
    }
    return axisTitle;
  },

  constructFilename: function(activeOption, friendlyNumerator, fullDenominator) {
    var axisTitle = (activeOption == 'items') ? 'items for ' : 'spend on ';
    axisTitle += friendlyNumerator;
    axisTitle += ' per' + fullDenominator;
    return axisTitle.toLowerCase();
  },

  constructTooltip: function(options, series_name, date, original_y, original_x, ratio, force_items) {
    var tt = '', activeOption = options.activeOption, numDecimals, p;
    numDecimals = (activeOption === 'items') ? 0 : 2;
    if (date !== null) {
      if (typeof date === 'string') {
        date = date.replace(/-/g, '/');
      }
      date = (typeof Highcharts !== 'undefined') ? Highcharts.dateFormat('%b \'%y', new Date(date)) : date;
    } else {
      date = (options.org == 'practice') ? ' since August 2010' : ' since April 2013';
    }
    tt += (series_name !== 'Series 1') ?
                '<b>' + series_name + '</b><br/>' : '';

    tt += (activeOption == 'items') ? 'Items for ' : 'Spend on ';
    tt += options.friendly.friendlyNumerator;
    tt += ' in ' + date + ': ';
    tt += (force_items || options.activeOption === 'items') ? '' : '£';
    tt += (typeof Highcharts !== 'undefined') ? Highcharts.numberFormat(original_y, numDecimals) : original_y;

    if (options.denom !== 'nothing') {
      tt += '<br/>';

      p = options.friendly.partialDenominator.charAt(0).toUpperCase();
      p += options.friendly.partialDenominator.substring(1);
      tt += p + ' in ' + date + ': ';
      if (options.activeOption !== 'items') {
        tt += (!force_items && options.denom === 'chemical') ? '£' : '';
      }
      tt += (typeof Highcharts !== 'undefined') ? Highcharts.numberFormat(original_x, numDecimals) : original_x;
      tt += '<br/>';
      tt += options.friendly.yAxisTitle.replace('<br/>', '') + ': ';
      tt += (force_items || options.activeOption === 'items') ? '' : '£';
      tt += (typeof Highcharts !== 'undefined') ? Highcharts.numberFormat(ratio) : ratio;
      // The line chart tooltips will only ever show items, regardless
      // of what global items have been set elsewhere.
      if (force_items) {
        tt = tt.replace(/Spend on/g, 'Items for');
      }
    }
    return tt;
  },

  getYAxisLabelFormatter: function(chartValues) {
    if (chartValues.y === 'y_actual_cost') {
      return function() {
        return '£' + this.axis.defaultLabelFormatter.call(this);
      };
    } else {
      return function() {
        return this.axis.defaultLabelFormatter.call(this);
      };
    }
  },

  _getStringForIds: function(ids, is_practices) {
    var maxLength = 70;
    var str = '';
    _.each(ids, function(e, i) {
      var id = (e.display_id) ? e.display_id : e.id;
      if ((is_practices) && (e.id.length === 3)) {
        str += 'practices in ';
      }
      str += (e.name) ? e.name : id;
      str += (i === (ids.length - 1)) ? '' : ' + ';
    });
    str = humanize.truncatechars(str, maxLength);
    return str;
  },
};
module.exports = formatters;
