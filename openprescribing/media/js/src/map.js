require('mapbox.js');
var utils = require('./chart_utils');
var formatters = require('./chart_formatters');
var _ = require('underscore');

var analyseMap = {

    update: function(ratio, month, title, subtitle) {
        this.updateMap('ratio_' + ratio, month, title, subtitle);
    },

    setup: function(options) {

        this.options = options;
        // TODO: Deal with no data
        //         $('#map-wrapper').show();
        //     } else {
        //         $('.chart-title').html("No known locations");
        //         $('.chart-sub-title').html('');
        //         $('#map-wrapper').hide();
        //     }
        // });

        var _this = this;
        _this.activeNames = _.pluck(options.orgIds, 'name');
        L.mapbox.accessToken = 'pk.eyJ1IjoiYW5uYXBvd2VsbHNtaXRoIiwiYSI6ImNzY1VpYkkifQ.LC_IcHpHfOvWOQCuo5t7Hw';
        if (typeof _this.map === 'undefined') {
            _this.map = L.mapbox.map('map', 'mapbox.streets');
            _this.map.scrollWheelZoom.disable();
        } else {
            _this.map.removeLayer(_this.orgLayer);
            if (typeof _this.legendHtml !== 'undefined') {
                _this.map.legendControl.removeLegend(_this.legendHtml);
            }
        }

        _this.popup = new L.Popup({ autoPan: false });
        var boundsUrl = this.getBoundsUrl(options);

        _this.orgLayer = L.mapbox.featureLayer(null, {
                pointToLayer: function (feature, latlng) {
                    return L.circleMarker(latlng, {
                        radius: 8,
                        color: "#000",
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.97
                    });
                }
            })
            .loadURL(boundsUrl)
            .addTo(_this.map)
            .on('ready', joinDataAndSetupMap);

        function joinDataAndSetupMap() {
            var dataByName = utils.indexDataByRowNameAndMonth(options.data.combinedData);
            _this.quintiles = utils.calculateQuintiles(options.data.combinedData);
            var f = joinFeaturesWithData(_this.orgLayer.getGeoJSON(),
                                         dataByName);
            _this.orgLayer.setGeoJSON(f);
            if ('_northEast' in _this.orgLayer.getBounds()) {
                _this.map.fitBounds(_this.orgLayer.getBounds(), {
                    minZoom: 7,
                    paddingBottomRight: [$(_this.legendContainer).width(), 0]
                });
            }
            _this.addLayerEvents();
            _this.updateMap('ratio_items',
                            options.activeMonth,
                            options.friendly.chartTitle,
                            options.friendly.chartSubTitle);
        }

        function joinFeaturesWithData(currentJson, data) {
            var joinedFeatures = [],
                byName = {};
            _.each(currentJson.features, function(d, i) {
                byName[d.properties.name] = d;
            });
            for (var name in byName) {
                byName[name].properties.data = data[name];
                joinedFeatures.push(byName[name]);
            }
            return joinedFeatures;
        }
    },

    addLayerEvents: function(ratio, month) {
        var _this = this;
        var closeTooltip;
        _this.orgLayer.eachLayer(function(layer) {
            layer.on('mousemove', function(e) {
                var layerData = e.target.feature.properties.data;
                // console.log('chartValues', _this.options.chartValues);
                var y = _this.options.chartValues.y;
                var x = _this.options.chartValues.x_val;
                var month = _this.options.activeMonth;
                var ratio = _this.options.chartValues.ratio;
                var monthData;
                var k = month.replace(/\//g, '-');
                if ((typeof layerData !== 'undefined') && (k in layerData)) {
                    monthData = layerData[k];
                } else {
                    monthData = {};
                    monthData[y] = null;
                    monthData[x] = null;
                    monthData[ratio] = null;
                }
                var layer = e.target;
                var html = formatters.constructTooltip(_this.options,
                    layer.feature.properties.name,
                    month,
                    monthData[y],
                    monthData[x],
                    monthData[ratio]);
                this.popup.setLatLng(e.latlng);
                this.popup.setContent(html);
                if (!this.popup._isOpen) {
                    this.popup.openOn(this.map);
                }
                window.clearTimeout(closeTooltip);
                if (!L.Browser.ie && !L.Browser.opera) {
                    layer.bringToFront();
                }
            }, _this);
            layer.on('mouseout', function(e) {
                var _this = this;
                closeTooltip = window.setTimeout(function() {
                   _this.map.closePopup();
                }, 100);
            }, _this);
            layer.on('click', function(e) {
                this.map.fitBounds(e.target.getBounds());
            }, _this);
        });
    },

    updateMap: function(ratio, month, title, subtitle) {
        var _this = this;
        month = month.replace(/\//g, '-');
        var quintiles = (month in _this.quintiles) ? _this.quintiles[month][ratio] : [];
        _this.map.legendControl.removeLegend(_this.legendHtml);
        _this.legendHtml = _this.getLegend(quintiles, ratio, title, subtitle);
        _this.map.legendControl.addLegend(_this.legendHtml);
        _this.orgLayer.eachLayer(function(layer) {
            var layerData = layer.feature.properties.data;
            var val = ((typeof layerData !== 'undefined') && (month in layerData)) ? layerData[month][ratio] : null;
            var style = _this.getStyle(val,
                                       quintiles,
                                       layer.feature.properties.name,
                                       _this.activeNames);
            layer.setStyle(style);
        });
    },

    getStyle: function(val, quintiles, name, activeNames) {
        var style = {
            color: 'black',
            fillOpacity: 0.7,
            radius: 8,
            weight: 2,
            opacity: 0.3,
            fillColor: this.getColour(quintiles, val)
        };
        if (_.contains(activeNames, name)) {
            style.weight = 3;
            style.opacity = 0.9;
        }
        return style;
    },

    resize: function() {
        var _this = this;
        if ((_this.orgLayer.getGeoJSON()) && (_this.orgLayer.getGeoJSON().length) && (_this.orgLayer.getBounds().isValid())) {
            _this.map.invalidateSize();
            _this.map.fitBounds(_this.orgLayer.getBounds(), {
                minZoom: 7,
                paddingBottomRight: [$(_this.legendContainer).width(), 0]
            });
        } else {
            _this.map.invalidateSize();
            _this.map.setView([52, 0], 6);
        }
    },

    getBoundsUrl: function(options) {
        var boundsUrl = '/api/1.0/org_location/?';
        if (options.org === 'CCG') {
            boundsUrl += 'org_type=ccg';
        } else {
            boundsUrl += 'org_type=practice&q=';
            _.each(options.orgIds, function(d) {
                if (('ccg' in d) && (d.ccg)) {
                    boundsUrl += d.ccg + ',';
                } else {
                    boundsUrl += d.id + ',';
                }
            });
        }
        return boundsUrl;
    },

    getColour: function(quintiles, d) {
        var color;
        if (quintiles.length === 6) {
            color = d > quintiles[4] ? '#54278f' :
              d > quintiles[3] ? '#756bb1' :
              d > quintiles[2] ? '#9e9ac8' :
              d > quintiles[1] ? '#cbc9e2' :
              '#f2f0f7';
        } else if (quintiles.length === 5) {
            color = d > quintiles[3] ? '#54278f' :
              d > quintiles[2] ? '#756bb1' :
              d > quintiles[1] ? '#9e9ac8' :
              '#f2f0f7';
        } else if (quintiles.length === 4) {
            color = d > quintiles[2] ? '#54278f' :
              d > quintiles[1] ? '#9e9ac8' :
              '#f2f0f7';
        } else {
            color = d > quintiles[1] ? '#9e9ac8' : '#f2f0f7';
        }
        return color;
    },

    getLegend: function(quintiles, ratio, title, subtitle) {
        // console.log('getLegend', quintiles);
        var labels = [], from, to, label;
        for (var i = 0; i < quintiles.length-1; i++) {
          from = quintiles[i];
          to = quintiles[i + 1];
          label = '<li><span class="swatch" style="background:';
          label += this.getColour(quintiles, to) + '"></span> ';
          label += (ratio === 'ratio_items') ? '' : '£';
          label += Highcharts.numberFormat(from);
          if (to) {
            label += '&ndash;';
            label += (ratio === 'ratio_items') ? '' : '£';
            label += Highcharts.numberFormat(to);
          }
          label += '</li>';
          labels.push(label);
        }
        var legend = '<span class="legend-header">' + title.replace('<br/>', '');
        legend += ' ' + subtitle + '</span>';
        legend += '<ul>' + labels.join('') + '</ul>';
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
module.exports = analyseMap;
