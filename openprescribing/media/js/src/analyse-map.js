import chroma from "chroma-js";
import $ from "jquery";
import "mapbox.js";
import _ from "underscore";
import formatters from "./chart_formatters";
import utils from "./chart_utils";
import config from "./config";

const analyseMap = {
  setup(options) {
    this.options = options;
    // TODO: Deal with no data
    //         $('#map-wrapper').show();
    //     } else {
    //         $('.chart-title').html("No known locations");
    //         $('.chart-sub-title').html('');
    //         $('#map-wrapper').hide();
    //     }
    // });

    const _this = this;
    _this.activeNames = _.pluck(options.orgIds, "name");
    L.mapbox.accessToken = window.MAPBOX_PUBLIC_TOKEN;
    if (typeof _this.map === "undefined") {
      _this.map = L.mapbox.map("map", null);
      _this.map.addLayer(
        L.mapbox.styleLayer("mapbox://styles/mapbox/streets-v11")
      );
      _this.map.scrollWheelZoom.disable();
    } else {
      _this.map.removeLayer(_this.orgLayer);
      if (typeof _this.legendHtml !== "undefined") {
        _this.map.legendControl.removeLegend(_this.legendHtml);
      }
    }
    const completed = $.Deferred();

    _this.popup = new L.Popup({ autoPan: false });
    const boundsUrl = this.getBoundsUrl(options);

    _this.orgLayer = L.mapbox
      .featureLayer(null, {
        pointToLayer(feature, latlng) {
          return L.circleMarker(latlng, {
            radius: 8,
            color: "#000",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.97,
          });
        },
      })
      .loadURL(boundsUrl)
      .addTo(_this.map)
      .on("ready", joinDataAndSetupMap);

    function joinDataAndSetupMap() {
      const dataByName = utils.indexDataByRowNameAndMonth(
        options.data.combinedData
      );
      _this.minMaxByDate = utils.calculateMinMaxByDate(
        options.data.combinedData
      );
      const f = joinFeaturesWithData(_this.orgLayer.getGeoJSON(), dataByName);
      _this.orgLayer.setGeoJSON(f);
      if ("_northEast" in _this.orgLayer.getBounds()) {
        _this.map.fitBounds(_this.orgLayer.getBounds(), {
          minZoom: 7,
          paddingBottomRight: [$(_this.legendContainer).width(), 0],
        });
      }
      _this.addLayerEvents();
      _this.updateMap("items", options);
      $("#play-slider").show();
      completed.resolve();
    }

    function joinFeaturesWithData({ features }, data) {
      const joinedFeatures = [];
      const byName = {};
      _.each(features, (d, i) => {
        if ("setting" in d.properties) {
          if (d.properties.setting === 4) {
            byName[d.properties.name] = d;
          }
        } else {
          byName[d.properties.name] = d;
        }
      });
      for (const name in byName) {
        byName[name].properties.data = data[name];
        joinedFeatures.push(byName[name]);
      }
      return joinedFeatures;
    }

    return completed;
  },

  addLayerEvents(ratio, month) {
    const _this = this;
    let closeTooltip;
    _this.orgLayer.eachLayer((layer) => {
      layer.on(
        "mousemove",
        function ({ target, latlng }) {
          const layerData = target.feature.properties.data;
          // console.log('chartValues', _this.options.chartValues);
          const y = _this.options.chartValues.y;
          const x = _this.options.chartValues.x_val;
          const month = _this.options.activeMonth;
          const ratio = _this.options.chartValues.ratio;
          let monthData;
          const k = month.replace(/\//g, "-");
          if (typeof layerData !== "undefined" && k in layerData) {
            monthData = layerData[k];
          } else {
            monthData = {};
            monthData[y] = null;
            monthData[x] = null;
            monthData[ratio] = null;
          }
          const layer = target;
          const html = formatters.constructTooltip(
            _this.options,
            layer.feature.properties.name,
            month,
            monthData[y],
            monthData[x],
            monthData[ratio]
          );
          this.popup.setLatLng(latlng);
          this.popup.setContent(html);
          if (!this.popup._isOpen) {
            this.popup.openOn(this.map);
          }
          window.clearTimeout(closeTooltip);
          if (!L.Browser.ie && !L.Browser.opera) {
            layer.bringToFront();
          }
        },
        _this
      );
      layer.on(
        "mouseout",
        function (e) {
          const _this = this;
          closeTooltip = window.setTimeout(() => {
            _this.map.closePopup();
          }, 100);
        },
        _this
      );
      layer.on(
        "click",
        function (e) {
          this.map.fitBounds(e.target.getBounds());
          e.target.fireEvent("mousemove", e);
        },
        _this
      );
    });
  },

  updateMap(ratio, options) {
    const _this = this;
    let minMax;
    ratio = `ratio_${ratio}`;
    const month = options.activeMonth.replace(/\//g, "-");
    if (options.playing) {
      // For animation-over-time, keep the min/max values constant
      const allMinMax = _.pluck(_.values(_this.minMaxByDate), ratio);
      minMax = [
        _.min(_.map(allMinMax, (x) => x[0])),
        _.max(_.map(allMinMax, (x) => x[1])),
      ];
    } else {
      minMax =
        month in _this.minMaxByDate ? _this.minMaxByDate[month][ratio] : null;
    }
    _this.map.legendControl.removeLegend(_this.legendHtml);
    _this.legendHtml = _this.getLegend(minMax, options);
    _this.map.legendControl.addLegend(_this.legendHtml);
    _this.orgLayer.eachLayer((layer) => {
      const layerData = layer.feature.properties.data;
      const val =
        typeof layerData !== "undefined" && month in layerData
          ? layerData[month][ratio]
          : null;
      const style = _this.getStyle(
        val,
        minMax[1],
        layer.feature.properties.name,
        _this.activeNames
      );
      layer.setStyle(style);
    });
  },

  getStyle(val, maxVal, name, activeNames) {
    const style = {
      color: "black",
      fillOpacity: 0.7,
      radius: 8,
      weight: 2,
      opacity: 0.3,
      fillColor: this.getColour(maxVal, val),
    };
    if (_.contains(activeNames, name)) {
      style.weight = 3;
      style.opacity = 0.9;
    }
    return style;
  },

  resize() {
    const _this = this;
    if (
      _this.orgLayer.getGeoJSON() &&
      _this.orgLayer.getGeoJSON().length &&
      _this.orgLayer.getBounds().isValid()
    ) {
      _this.map.invalidateSize();
      _this.map.fitBounds(_this.orgLayer.getBounds(), {
        minZoom: 7,
        paddingBottomRight: [$(_this.legendContainer).width(), 0],
      });
    } else {
      _this.map.invalidateSize();
      _this.map.setView([52, 0], 6);
    }
  },

  getBoundsUrl({ org, orgIds }) {
    let boundsUrl = `${config.apiHost}/api/1.0/org_location/?format=json&`;
    if (org === "practice") {
      boundsUrl += "org_type=practice&q=";
      _.each(orgIds, (d) => {
        if ("ccg" in d && d.ccg) {
          boundsUrl += `${d.ccg},`;
        } else {
          boundsUrl += `${d.id},`;
        }
      });
    } else {
      boundsUrl += `org_type=${org.toLowerCase()}`;
    }
    return boundsUrl;
  },

  getColour(topVal, d) {
    const scale = chroma.scale("RdBu");
    return scale(1 - d / topVal).hex();
  },

  getLegend(minMax, { friendly }) {
    // console.log('getLegend', quintiles);
    let legend = `<span class="legend-header">${friendly.yAxisTitle.replace(
      "<br/>",
      ""
    )}`;
    legend += ` ${friendly.chartSubTitle}</span>`;
    legend += '<div class="gradient">';
    for (let i = 1; i <= 100; i++) {
      const j = minMax[0] + (i * (minMax[1] - minMax[0])) / 100;
      legend += `<span class="grad-step" style="background-color:${this.getColour(
        minMax[1],
        j
      )}"></span>`;
    }
    legend += `<span class="domain-min">${Highcharts.numberFormat(
      minMax[0]
    )}</span>`;
    legend += `<span class="domain-max">${Highcharts.numberFormat(
      minMax[1]
    )}</span>`;
    legend += "</div>";
    legend += `by ${friendly.friendlyOrgs}`;
    return legend;
  },

  // hasKnownLocations: function(boundaries) {
  //     var has_locations = false;
  //     $.each(boundaries.features, function(i, d) {
  //         if (d.geometry !== null) {
  //             has_locations = true;
  //             return false;
  //         }
  //     });
  //     return has_locations;
  // }
};
export default analyseMap;
