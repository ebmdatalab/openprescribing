import domready from "domready";
import _ from "underscore";
import analyseChart from "./analyse-chart";
import hashHelper from "./analyse-hash";
import utils from "./chart_utils";
import config from "./config";

const queryForm = {
  el: {
    org: "#org",
    orgIds: "#orgIds",
    orgHelp: "#org-help",
    numerator: "#num",
    numeratorIds: "#numIds",
    denominator: "#denom",
    denominatorIds: "#denomIds",
    numeratorHelp: "#numerator-help",
    denominatorHelp: "#denominator-help",
    numHelpText: "#numerator-help-text",
    denomHelpText: "#denominator-help-text",
    loading: "#loading-form",
    analyseOptions: "#analyse-options",
    update: "#update",
    chart: "#chart",
    results: "#results",
    oldBrowserWarning: "#old-browser",
  },
  // These are default values for the analyse form:
  globalOptions: {
    data: {},
    org: "CCG",
    orgIds: [],
    num: "chemical",
    numIds: [],
    denom: "nothing",
    denomIds: [],
    highlightedPoints: [],
    reUpdate: false,
    selectedTab: "summary", // One of 'summary', 'chart', 'map'
  },

  setUp() {
    this.initialiseGlobalOptionsFromHash(true);
    this.initialiseHelpText();
    const _this = this;
    if (utils.getIEVersion()) {
      $(_this.el.oldBrowserWarning).show();
    }
    this.initialiseFormValues().then(() => {
      _this.initialiseSelectElements();
      _this.updateFormElementsToMatchOptions(true);
      _this.initialiseFormEvents();
      $(_this.el.loading).hide();
      $(_this.el.analyseOptions).removeClass("invisible").hide().fadeIn();
      if (_this.checkIfButtonShouldBeEnabled(_this.globalOptions)) {
        analyseChart.renderChart(_this.globalOptions);
      }
    });
  },

  updateFormElementsToMatchOptions(isInitial = false) {
    const _this = this;
    if (isInitial) {
      // On first load, manually append all the values.
      // This is how select2 wants us to do it.
      _.each(_this.globalOptions.orgIds, ({ name, id }) => {
        const option = $("<option selected></option>").text(name).val(id);
        $(_this.el.orgIds).append(option);
      });
      $(_this.el.orgIds).trigger("change");
      _.each(_this.globalOptions.numIds, ({ name, id }) => {
        const option = $("<option selected></option>").text(name).val(id);
        $(_this.el.numeratorIds).append(option);
      });
      $(_this.el.numeratorIds).trigger("change");
      _.each(_this.globalOptions.denomIds, ({ name, id }) => {
        const option = $("<option selected></option>").text(name).val(id);
        $(_this.el.denominatorIds).append(option);
      });
      $(_this.el.denominatorIds).trigger("change");
    } else {
      // We do this because a type change needs us to set the related
      // IDs to empty - e.g. if we change org type from CCGs to practices,
      // we want to empty the list of orgs.
      if (_this.globalOptions.orgIds.length === 0) {
        $(_this.el.orgIds).val("").trigger("change");
      }
      if (_this.globalOptions.numIds.length === 0) {
        $(_this.el.numeratorIds).val("").trigger("change");
      }
      if (_this.globalOptions.denomIds.length === 0) {
        $(_this.el.denominatorIds).val("").trigger("change");
      }
    }

    // Hide or show CCG matches.
    if (this.globalOptions.org !== "all") {
      $(this.el.orgIds).parent().fadeIn();
      if (this.globalOptions.org === "practice") {
        $(this.el.orgHelp).text("Hint: add a CCG to see all its practices");
        $(this.el.orgHelp).fadeIn();
      } else if (this.globalOptions.org === "CCG") {
        $(this.el.orgHelp).text("Hint: leave blank to see national totals");
        $(this.el.orgHelp).fadeIn();
      }
    } else {
      $(this.el.orgHelp).fadeOut();
      $(this.el.orgIds).parent().fadeOut();
    }

    // Hide or show numerator options.
    if (this.globalOptions.num === "all") {
      $(this.el.numeratorIds).parent().fadeOut();
    } else {
      $(this.el.numeratorIds).parent().fadeIn();
    }

    // Hide or show denominator options.
    if (this.globalOptions.denom !== "chemical") {
      $(this.el.denominatorIds).parent().fadeOut();
    } else {
      $(this.el.denominatorIds).parent().fadeIn();
    }
    this.checkIfButtonShouldBeEnabled(this.globalOptions);
  },

  checkIfChartCanBeRendered({ num, numIds, org, orgIds }) {
    let hasNumerator;
    let hasOrgIds;
    hasNumerator = num === "all" || numIds.length > 0;
    hasOrgIds = (org && org !== "practice") || orgIds.length > 0;
    return hasNumerator && hasOrgIds;
  },

  checkIfButtonShouldBeEnabled(options) {
    const btnEnabled = this.checkIfChartCanBeRendered(options);
    $(this.el.update).prop("disabled", !btnEnabled);
    return btnEnabled;
  },

  initialiseGlobalOptionsFromHash(is_load) {
    // console.log('initialiseGlobalOptionsFromHash');
    const params = hashHelper.getHashParams();
    for (const k in params) {
      // Handle old URL parameters.
      if (k === "denom" && params[k] === "star_pu_oral_antibac_items") {
        params[k] = "star_pu.oral_antibacterials_item";
      }
      this.globalOptions[k] = params[k];
    }
    if (
      this.globalOptions.denom == "nothing" &&
      typeof this.globalOptions.denomIds !== "undefined" &&
      this.globalOptions.denomIds.length > 0
    ) {
      // the default for the dropdown is 'nothing', but we should
      // override that if a denominator has been specified in the URL
      this.globalOptions.denom = "chemical";
    }
  },

  initialiseHelpText() {
    const _this = this;
    $(_this.el.numeratorHelp).popover({
      html: true,
      content() {
        return $(_this.el.numHelpText).html();
      },
      title: "Add BNF sections or drugs",
    });
    $(_this.el.denominatorHelp).popover({
      html: true,
      content() {
        return $(_this.el.denomHelpText).html();
      },
      title: "Add BNF sections, drugs or prescribing comparators",
    });
  },

  initialiseFormEvents() {
    // console.log('initialiseFormEvents');
    const _this = this;
    // If we change the type of org, numerator or denominator, we want
    // to set the selected IDs in globalOptions to empty.
    // Then update the form accordingly.
    const typeBoxes = [this.el.org, this.el.numerator, this.el.denominator];
    _.each(typeBoxes, (d) => {
      $(d).on("change", function () {
        // console.log('changed typebox', $(this).attr('id'));
        _this.globalOptions[$(this).attr("id")] = $(this).val();
        _this.globalOptions[`${$(this).attr("id")}Ids`] = [];
        _this.updateFormElementsToMatchOptions();
      });
    });
    // If the selected IDs for org/numerator/denominator are changed
    // with select2, then we need to update the globalOptions to match.
    const idBoxes = [
      this.el.orgIds,
      this.el.numeratorIds,
      this.el.denominatorIds,
    ];
    _.each(idBoxes, (d) => {
      $(d).on("select2:select select2:unselect", function (e) {
        const selectedData = $(this).select2("data");
        // console.log('changed idbox', $(this).attr('id'), 'selectedData', selectedData);
        const optionId = $(this).attr("id");
        _this.globalOptions[optionId] = [];
        _.each(selectedData, (d) => {
          const item = {
            id: d.id,
            ccg: d.ccg,
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
    $(_this.el.update).click(function () {
      $(this).data("clicked", true);
      $(_this.el.results).hide();
      $(_this.el.chart).html("");
      if (_this.checkIfChartCanBeRendered(_this.globalOptions)) {
        analyseChart.renderChart(_this.globalOptions);
      }
    });
  },

  initialiseFormValues() {
    // console.log('initialiseFormValues');
    const _this = this;
    return _this
      .prefillOrgs()
      .then(_this.prefillNumerators)
      .then(_this.prefillDenominators)
      .then(function (denomIds, context) {
        if (context === "success") {
          context = this;
        }
        context.globalOptions.denomIds = denomIds;
        return true;
      });
  },

  prefillOrgs() {
    if (this.globalOptions.orgIds.length > 0) {
      let url = `${config.apiHost}/api/1.0/org_code/?format=json&exact=true&q=`;
      _.each(this.globalOptions.orgIds, ({ id }) => {
        url += `${id},`;
      });
      url += `&org_type=${this.getOrgTypeForQuery()}`;
      return $.ajax({
        type: "GET",
        url,
        dataType: "json",
        context: this,
      });
    } else {
      return $.when([], this);
    }
  },

  prefillNumerators(orgIds, context) {
    // console.log('this', this);
    if (context === "success") {
      context = this;
    }
    context.globalOptions.orgIds = orgIds;
    if (context.globalOptions.numIds.length > 0) {
      let url = `${config.apiHost}/api/1.0/bnf_code/?format=json&exact=true&q=`;
      _.each(context.globalOptions.numIds, ({ id }) => {
        url += `${id},`;
      });
      return $.ajax({
        type: "GET",
        url,
        dataType: "json",
        context,
      });
    } else {
      return $.when([], context);
    }
  },

  prefillDenominators(numIds, context) {
    if (context === "success") {
      context = this;
    }
    context.globalOptions.numIds = numIds;
    if (context === "success") {
      context = this;
    }
    if (context.globalOptions.denomIds.length > 0) {
      let url = `${config.apiHost}/api/1.0/bnf_code/?format=json&exact=true&q=`;
      _.each(context.globalOptions.denomIds, ({ id }) => {
        url += `${id},`;
      });
      return $.ajax({
        type: "GET",
        url,
        dataType: "json",
        context,
      });
    } else {
      return $.when([], context);
    }
  },

  initialiseSelectElements() {
    const _this = this;
    $(this.el.org).val(this.globalOptions.org);
    $(this.el.numerator).val(this.globalOptions.num);
    $(this.el.denominator).val(this.globalOptions.denom);
    $(".form-select.not-searchable").select2({
      minimumResultsForSearch: Infinity,
    });
    const select2Options = {
      placeholder: "add names or codes",
      // allowClear: true,
      escapeMarkup(markup) {
        return markup;
      },
      minimumInputLength: 3,
      templateResult(result) {
        if (result.loading) return result.text;
        let str;
        let section;
        let name;
        str = `<strong>${result.type}`;
        if ("is_generic" in result) {
          str += result.is_generic ? ", generic" : ", branded";
        }
        str += "</strong>: ";
        str += result.text ? result.text : result.name;
        str += ` (${result.id}`;
        if ("section" in result) {
          str += `, in section ${result.section}`;
        }
        str += ")";
        return str;
      },
      templateSelection(result) {
        let str = "";
        let section;
        let name;
        str += result.text ? result.text : result.name;
        str += result.id ? ` (${result.id})` : "";
        return str;
      },
      ajax: {
        url: `${config.apiHost}/api/1.0/bnf_code/?format=json`,
        delay: 50,
        data({ term, page }) {
          return {
            q: term,
            page: page,
          };
        },
        processResults(data, params) {
          params.page = params.page || 1;
          return {
            results: data,
            pagination: {
              more: params.page * 30 < data.total_count,
            },
          };
        },
        cache: true,
      },
    };
    const optionsNum = $.extend(true, {}, select2Options);
    optionsNum.placeholder += ", e.g. Cerazette";
    const optionsDenom = $.extend(true, {}, select2Options);
    optionsDenom.placeholder += ", e.g. 7.3.2";
    $(this.el.numeratorIds).select2(optionsNum);
    $(this.el.denominatorIds).select2(optionsDenom);
    const optionsOrg = $.extend(true, {}, select2Options);
    optionsOrg.ajax.url = () => {
      const orgType = _this.getOrgTypeForQuery();
      return `${config.apiHost}/api/1.0/org_code/?org_type=${orgType}&format=json`;
    };
    $(this.el.orgIds).select2(optionsOrg);
    _this.globalOptions.selectOrgOptions = optionsOrg;
  },

  getOrgTypeForQuery() {
    let orgType = this.globalOptions.org;
    // Support selecting all practices in a CCG by supplying the CCG code
    if (orgType === "practice") {
      orgType = "CCG,practice";
    }
    return orgType;
  },
};

domready(() => {
  queryForm.setUp();
});

export default queryForm;
