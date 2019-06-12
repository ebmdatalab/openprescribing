var $ = require('jquery');
var _ = require('underscore');
var domready = require('domready');
var hashHelper = require('./analyse-hash');
var utils = require('./chart_utils');
var analyseChart = require('./analyse-chart');
var config = require('./config');
var bootstrap = require('bootstrap');
var select2 = require('select2');

var queryForm = {

  el: {
    org: '#org',
    orgIds: '#orgIds',
    orgHelp: '#org-help',
    numerator: '#num',
    numeratorIds: '#numIds',
    denominator: '#denom',
    denominatorIds: '#denomIds',
    numeratorHelp: '#numerator-help',
    denominatorHelp: '#denominator-help',
    numHelpText: '#numerator-help-text',
    denomHelpText: '#denominator-help-text',
    loading: '#loading-form',
    analyseOptions: '#analyse-options',
    update: '#update',
    chart: '#chart',
    results: '#results',
    oldBrowserWarning: '#old-browser',
  },
  // These are default values for the analyse form:
  globalOptions: {
    data: {},
    org: 'CCG',
    orgIds: [],
    num: 'chemical',
    numIds: [],
    denom: 'nothing',
    denomIds: [],
    highlightedPoints: [],
    reUpdate: false,
    selectedTab: 'summary', // One of 'summary', 'chart', 'map'
  },

  setUp: function() {
    this.initialiseGlobalOptionsFromHash(true);
    this.initialiseHelpText();
    var _this = this;
    if (utils.getIEVersion()) {
      $(_this.el.oldBrowserWarning).show();
    }
    this.initialiseFormValues().then(function() {
      _this.initialiseSelectElements();
      _this.updateFormElementsToMatchOptions(true);
      _this.initialiseFormEvents();
      $(_this.el.loading).hide();
      $(_this.el.analyseOptions).removeClass('invisible').hide().fadeIn();
      if (_this.checkIfButtonShouldBeEnabled(_this.globalOptions)) {
        analyseChart.renderChart(_this.globalOptions);
      }
    });
  },

  updateFormElementsToMatchOptions: function(isInitial) {
    // console.log('updateFormElementsToMatchOptions');
    isInitial = isInitial || false;
    var _this = this;
    if (isInitial) {
      // On first load, manually append all the values.
      // This is how select2 wants us to do it.
      _.each(_this.globalOptions.orgIds, function(d) {
        var option = $('<option selected></option>').text(d.name).val(d.id);
        $(_this.el.orgIds).append(option);
      });
      $(_this.el.orgIds).trigger('change');
      _.each(_this.globalOptions.numIds, function(d) {
        var option = $('<option selected></option>').text(d.name).val(d.id);
        $(_this.el.numeratorIds).append(option);
      });
      $(_this.el.numeratorIds).trigger('change');
      _.each(_this.globalOptions.denomIds, function(d) {
        var option = $('<option selected></option>').text(d.name).val(d.id);
        $(_this.el.denominatorIds).append(option);
      });
      $(_this.el.denominatorIds).trigger('change');
    } else {
      // We do this because a type change needs us to set the related
      // IDs to empty - e.g. if we change org type from CCGs to practices,
      // we want to empty the list of orgs.
      if (_this.globalOptions.orgIds.length === 0) {
        $(_this.el.orgIds).val('').trigger('change');
      }
      if (_this.globalOptions.numIds.length === 0) {
        $(_this.el.numeratorIds).val('').trigger('change');
      }
      if (_this.globalOptions.denomIds.length === 0) {
        $(_this.el.denominatorIds).val('').trigger('change');
      }
    }

    // Hide or show CCG matches.
    if (this.globalOptions.org !== 'all') {
      $(this.el.orgIds).parent().fadeIn();
      if (this.globalOptions.org === 'practice') {
        $(this.el.orgHelp).text('Hint: add a CCG to see all its practices');
        $(this.el.orgHelp).fadeIn();
      } else if (this.globalOptions.org === 'CCG') {
        $(this.el.orgHelp).text('Hint: leave blank to see national totals');
        $(this.el.orgHelp).fadeIn();
      }
    } else {
      $(this.el.orgHelp).fadeOut();
      $(this.el.orgIds).parent().fadeOut();
    }

    // Hide or show numerator options.
    if (this.globalOptions.num === 'all') {
      $(this.el.numeratorIds).parent().fadeOut();
    } else {
      $(this.el.numeratorIds).parent().fadeIn();
    }

    // Hide or show denominator options.
    if (this.globalOptions.denom !== 'chemical') {
      $(this.el.denominatorIds).parent().fadeOut();
    } else {
      $(this.el.denominatorIds).parent().fadeIn();
    }
    this.checkIfButtonShouldBeEnabled(this.globalOptions);
  },

  checkIfChartCanBeRendered: function(options) {
    var hasNumerator;
    var hasOrgIds;
    hasNumerator = ((options.num === 'all') || (options.numIds.length > 0));
    hasOrgIds = (
      (options.org && options.org !== 'practice') ||
      (options.orgIds.length > 0)
    );
    return hasNumerator && hasOrgIds;
  },

  checkIfButtonShouldBeEnabled: function(options) {
    var btnEnabled = this.checkIfChartCanBeRendered(options);
    $(this.el.update).prop('disabled', !btnEnabled);
    return btnEnabled;
  },

  initialiseGlobalOptionsFromHash: function(is_load) {
    // console.log('initialiseGlobalOptionsFromHash');
    var params = hashHelper.getHashParams();
    for (var k in params) {
      // Handle old URL parameters.
      if ((k === 'denom') && (params[k] === 'star_pu_oral_antibac_items')) {
        params[k] = 'star_pu.oral_antibacterials_item';
      }
      this.globalOptions[k] = params[k];
    }
    if (this.globalOptions.denom == 'nothing' &&
        (typeof this.globalOptions.denomIds !== 'undefined' && this.globalOptions.denomIds.length > 0)
       ) {
      // the default for the dropdown is 'nothing', but we should
      // override that if a denominator has been specified in the URL
      this.globalOptions.denom = 'chemical';
    }
  },

  initialiseHelpText: function() {
    var _this = this;
    $(_this.el.numeratorHelp).popover({
      html: true,
      content: function() {
        return $(_this.el.numHelpText).html();
      },
      title: 'Add BNF sections or drugs',
    });
    $(_this.el.denominatorHelp).popover({
      html: true,
      content: function() {
        return $(_this.el.denomHelpText).html();
      },
      title: 'Add BNF sections, drugs or prescribing comparators',
    });
  },

  initialiseFormEvents: function() {
        // console.log('initialiseFormEvents');
    var _this = this;
        // If we change the type of org, numerator or denominator, we want
        // to set the selected IDs in globalOptions to empty.
        // Then update the form accordingly.
    var typeBoxes = [this.el.org, this.el.numerator, this.el.denominator];
    _.each(typeBoxes, function(d) {
      $(d).on('change', function() {
                // console.log('changed typebox', $(this).attr('id'));
        _this.globalOptions[$(this).attr('id')] = $(this).val();
        _this.globalOptions[$(this).attr('id') + 'Ids'] = [];
        _this.updateFormElementsToMatchOptions();
      });
    });
        // If the selected IDs for org/numerator/denominator are changed
        // with select2, then we need to update the globalOptions to match.
    var idBoxes = [this.el.orgIds, this.el.numeratorIds, this.el.denominatorIds];
    _.each(idBoxes, function(d) {
      $(d).on('select2:select select2:unselect', function(e) {
        var selectedData = $(this).select2('data');
                // console.log('changed idbox', $(this).attr('id'), 'selectedData', selectedData);
        var optionId = $(this).attr('id');
        _this.globalOptions[optionId] = [];
        _.each(selectedData, function(d) {
          var item = {
            'id': d.id,
            'ccg': d.ccg,
          };
          item.name = d.name || d.text;
          item.text = item.name;
          if (d.type) {
            item.type = d.type;
          }
          if (d.code) {
            item.code = d.code;
          }
          _this.globalOptions[optionId].push(item);
        });
        _this.checkIfButtonShouldBeEnabled(_this.globalOptions);
      });
    });
        // Handle click on 'get data' button.
    $(_this.el.update).click(function() {
      $(this).data('clicked', true);
      $(_this.el.results).hide();
      $(_this.el.chart).html('');
      if (_this.checkIfChartCanBeRendered(_this.globalOptions)) {
        analyseChart.renderChart(_this.globalOptions);
      }
    });
  },

  initialiseFormValues: function() {
        // console.log('initialiseFormValues');
    var _this = this;
    return _this.prefillOrgs()
                    .then(_this.prefillNumerators)
                    .then(_this.prefillDenominators)
                    .then(function(denomIds, context) {
                      if (context === 'success') {
                        context = this;
                      }
                      context.globalOptions.denomIds = denomIds;
                      return true;
                    });
  },

  prefillOrgs: function() {
    if (this.globalOptions.orgIds.length > 0) {
      var url = config.apiHost + '/api/1.0/org_code/?format=json&exact=true&q=';
      _.each(this.globalOptions.orgIds, function(d) {
        url += d.id + ',';
      });
      url += '&org_type=' + this.globalOptions.org;
      return $.ajax({
        type: 'GET',
        url: url,
        dataType: 'json',
        context: this,
      });
    } else {
      return $.when([], this);
    }
  },

  prefillNumerators: function(orgIds, context) {
        // console.log('this', this);
    if (context === 'success') {
      context = this;
    }
    context.globalOptions.orgIds = orgIds;
    if (context.globalOptions.numIds.length > 0) {
      var url = config.apiHost + '/api/1.0/bnf_code/?format=json&exact=true&q=';
      _.each(context.globalOptions.numIds, function(d) {
        url += d.id + ',';
      });
      return $.ajax({
        type: 'GET',
        url: url,
        dataType: 'json',
        context: context,
      });
    } else {
      return $.when([], context);
    }
  },

  prefillDenominators: function(numIds, context) {
    if (context === 'success') {
      context = this;
    }
    context.globalOptions.numIds = numIds;
    if (context === 'success') {
      context = this;
    }
    if (context.globalOptions.denomIds.length > 0) {
      var url = config.apiHost + '/api/1.0/bnf_code/?format=json&exact=true&q=';
      _.each(context.globalOptions.denomIds, function(d) {
        url += d.id + ',';
      });
      return $.ajax({
        type: 'GET',
        url: url,
        dataType: 'json',
        context: context,
      });
    } else {
      return $.when([], context);
    }
  },

  initialiseSelectElements: function() {
    var _this = this;
    $(this.el.org).val(this.globalOptions.org);
    $(this.el.numerator).val(this.globalOptions.num);
    $(this.el.denominator).val(this.globalOptions.denom);
    $('.form-select.not-searchable').select2({
      minimumResultsForSearch: Infinity,
    });
    var select2Options = {
      placeholder: 'add names or codes',
            // allowClear: true,
      escapeMarkup: function(markup) {
 return markup;
},
      minimumInputLength: 3,
      templateResult: function(result) {
        if (result.loading) return result.text;
        var str, section, name;
        str = '<strong>' + result.type;
        if ('is_generic' in result) {
          str += (result.is_generic) ? ', generic' : ', branded';
        }
        str += '</strong>: ';
        str += (result.text) ? result.text : result.name;
        str += ' (' + result.id;
        if ('section' in result) {
          str += ', in section ' + result.section;
        }
        str += ')';
        return str;
      },
      templateSelection: function(result) {
        var str = '', section, name;
        str += (result.text) ? result.text : result.name;
        str += (result.id) ? ' (' + result.id + ')' : '';
        return str;
      },
      ajax: {
        url: config.apiHost + '/api/1.0/bnf_code/?format=json',
        delay: 50,
        data: function(params) {
          return {
            q: params.term,
            page: params.page,

          };
        },
        processResults: function(data, params) {
          params.page = params.page || 1;
          return {
            results: data,
            pagination: {
              more: (params.page * 30) < data.total_count,
            },
          };
        },
        cache: true,
      },
    };
    var optionsNum = $.extend(true, {}, select2Options);
    optionsNum.placeholder += ', e.g. Cerazette';
    var optionsDenom = $.extend(true, {}, select2Options);
    optionsDenom.placeholder += ', e.g. 7.3.2';
    $(this.el.numeratorIds).select2(optionsNum);
    $(this.el.denominatorIds).select2(optionsDenom);
    var optionsOrg = $.extend(true, {}, select2Options);
    optionsOrg.ajax.url = function() {
      var orgType = _this.globalOptions.org;
      if (orgType === 'practice') {
        orgType = 'CCG,practice';
      }
      return config.apiHost + '/api/1.0/org_code/?org_type=' + orgType + '&format=json';
    };
    $(this.el.orgIds).select2(optionsOrg);
    _this.globalOptions.selectOrgOptions = optionsOrg;
  },

};

domready(function() {
  queryForm.setUp();
});

module.exports = queryForm;
