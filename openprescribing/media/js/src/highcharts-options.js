var Highcharts = require('Highcharts');
global.jQuery = require('jquery');
global.$ = global.jQuery;

var backgroundGradient = {
    linearGradient: [0, 0, 500, 500],
    stops: [
        [0, 'rgb(255, 255, 255)'],
        [1, 'rgb(240, 240, 255)']
    ]
};
Highcharts.theme = {
    colors: ['#058DC7', '#50B432', '#ED561B', '#DDDF00', '#24CBE5', '#64E572',
             '#FF9655', '#FFF263', '#6AF9C4'],
    chart: {
        marginTop: 10,
        marginRight: 30,
        background: backgroundGradient,
        shadow: {
            'color': '#ccc',
            'offsetX': 1,
            'offsetY': 3,
            'opacity': 0.6
        },
        borderRadius: 6,
        renderTo: 'chart'
    },
    title: {
        style: {
            color: '#000',
            font: "bold 16px 'sofia-pro', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif"
        }
    },
    subtitle: {
        style: {
            color: '#666666',
            font: "bold 12px 'sofia-pro', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif"
        }
    },
    legend: {
        itemStyle: {
            font: "9px 'sofia-pro', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
            color: 'black'
        },
        itemHoverStyle:{
            color: 'gray'
        }
    }
};
Highcharts.setOptions(Highcharts.theme);
Highcharts.setOptions({
    lang: {
        thousandsSep: ',',
        numericSymbols: [ "k" , "m" , "G" , "T" , "P" , "E"]
    }
});

var baseOptions = {
    global: {
      useUTC: false
    },
    chart: {
        type: 'scatter',
        zoomType: 'xy',
        style: {
            fontFamily: "'sofia-pro', 'Helvetica Neue', 'Arial', sans-serif"
        }
    },
    credits: {
        enabled: true,
        position: {
            align: 'center',
            verticalAlign: 'top',
            y: 96
        },
        style: {
            color: '#ccc',
            fontSize: '24px',
            opacity: 0.2
        },
        text: "openprescribing.net"
    },
    title: {
        text: null
    },
    xAxis: {
        title: {
            enabled: true,
            text: 'Month'
        },
        type: 'datetime',
        dateTimeLabelFormats: {
            month: '%b \'%y'
        },
        gridLineWidth: 0,
        minorGridLineWidth: 0
    },
    yAxis: {
        min: 0,
        gridLineWidth: 0,
        tickWidth: 1,
        lineWidth: 1
    },
    legend: {
        layout: 'vertical',
        align: 'left',
        verticalAlign: 'top',
        x: 100,
        y: 70,
        floating: true,
        backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF',
        borderWidth: 1
    },
    plotOptions: {
        column: {
            borderRadius: 2
        },
        scatter: {
            allowPointSelect: true,
            marker: {
                states: {
                    hover: {
                        enabled: true,
                        lineColor: 'rgba(240, 173, 78, 0.3)',
                        lineWidth: 3,
                        radius: 5,
                        fillColor: 'rgba(240, 173, 78, 0.7)'
                    },
                    select: {
                        enabled: true,
                        lineColor: 'rgba(217, 83, 79, 0.3)',
                        lineWidth: 3,
                        radius: 7,
                        fillColor: 'rgba(217, 83, 79, 0.7)'
                    }
                }
            }
        }
    }
};

var barOptions = $.extend(true, {}, baseOptions);
barOptions.chart.type = 'column';
barOptions.chart.marginTop = 60;
barOptions.chart.renderTo = 'summarychart';
barOptions.xAxis.type = 'category';
barOptions.legend.enabled = false;
barOptions.xAxis.labels = {
    formatter: function() {
        var str = this.value.substring(0, 17);
        str += (this.value.length > 17) ? '...' : '';
        return str;
    },
    rotation: -90,
    style: {
        fontSize: '8px'
    }
};

var lineOptions = $.extend(true, {}, baseOptions);
lineOptions.chart.type = 'line';
lineOptions.legend.enabled = false;
lineOptions.chart.marginTop = 60;
lineOptions.plotOptions = {
    series: {
        marker: {
            states: {
                hover: {
                    radiusPlus: 1,
                    lineWidthPlus: 1
                }
            }
        },
        states: {
            hover: {
                lineWidthPlus: 2
            }
        }
    }
};

var scatterOptions = $.extend(true, {}, baseOptions);
var chartOptions = {
    baseOptions: $.extend(true, {}, baseOptions),
    barOptions: barOptions,
    lineOptions: lineOptions,
    scatterOptions: scatterOptions
};



var dashOptions = $.extend(true, {}, baseOptions);
dashOptions.chart.type = 'line';
dashOptions.credits.enabled = false;
dashOptions.chart.marginTop = 10;
dashOptions.chart.spacingLeft = 0;
dashOptions.chart.marginRight = 10;

dashOptions.legend.enabled = true;
dashOptions.legend.align = 'left';
dashOptions.legend.verticalAlign = 'bottom';
dashOptions.legend.y = -40;
dashOptions.legend.x = 90;
dashOptions.legend.borderRadius = 3;
dashOptions.yAxis.title = {
    offset: 50,
    style: {
        fontSize: 9
    }
};
dashOptions.yAxis.tickLength = 5;
dashOptions.yAxis.labels = {
    x: -10,
    y: 3,
    style: {
        fontSize: 9
    }
};
dashOptions.xAxis.title.style = {
        fontSize: 9
};
dashOptions.xAxis.tickLength = 5;
dashOptions.xAxis.labels = {
    y: 15,
    align: 'center',
    style: {
        fontSize: 9
    }
};

var scatterOptions = $.extend(true, {}, baseOptions);
var chartOptions = {
    baseOptions: $.extend(true, {}, baseOptions),
    barOptions: barOptions,
    lineOptions: lineOptions,
    dashOptions: dashOptions,
    scatterOptions: scatterOptions
};
module.exports = chartOptions;
