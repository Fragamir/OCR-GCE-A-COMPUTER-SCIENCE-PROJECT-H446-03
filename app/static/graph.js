function CreateGraph (machine_id, machine_nickname) {
    let dataSeries1 = [];
    let dataSeries2 = [];
    let dataSeries3 = [];

    let text = "Usage statistics for Machine #" + machine_id;
    if (machine_nickname !== null) {
        text = "Usage statistics for Machine (#"+machine_id+"): "+machine_nickname
    }

    let options = {
        exportEnabled: true,
        animationEnabled: true,
        title: {
            text: text
        },
        axisX: {
            title: "Time"
        },
        axisY: [{
            title: "Memory usage",
            titleFontColor: "#4F81BC",
            lineColor: "#4F81BC",
            labelFontColor: "#4F81BC",
            tickColor: "#4F81BC",
            includeZero: true,
            viewportMaximum: 100,
            suffix: "%"
        },{
            title: "CPU usage",
            titleFontColor: "#C0504E",
            lineColor: "#C0504E",
            labelFontColor: "#C0504E",
            tickColor: "#C0504E",
            includeZero: true,
            viewportMaximum: 100,
            suffix: "%"
        }],
        axisY2: {
            title: "Disk usage",
            titleFontColor: "#32C030",
            lineColor: "#32C030",
            labelFontColor: "#32C030",
            tickColor: "#32C030",
            includeZero: true,
            viewportMaximum: 100,
            suffix: "%"
        },
        toolTip: {
            shared: true
        },
        legend: {
            cursor: "pointer",
            itemclick: toggleDataSeries
        },
        data: [{
            type: "spline",
            name: "CPU usage",
            axisYIndex: 1,
            xValueType: "dateTime",
            showInLegend: true,
            dataPoints: dataSeries1
        },
        {
            type: "spline",
            name: "Disk usage",
            axisYIndex: 0,
            xValueType: "dateTime",
            showInLegend: true,
            dataPoints: dataSeries2
        },
        {
            type: "spline",
            name: "Memory usage",
            axisYType: "secondary",
            xValueType: "dateTime",
            showInLegend: true,
            dataPoints: dataSeries3
        }]
    };
    const chartContainer = $("#chartContainer"+machine_id);
    chartContainer.CanvasJSChart(options);
    const chart = chartContainer.CanvasJSChart();

    function toggleDataSeries(e) {
        e.dataSeries.visible = !(typeof (e.dataSeries.visible)==="undefined" || e.dataSeries.visible);
        e.chart.render();
    }

    let firstRequest = true;
    let previousRequest = "";

    function addData(data) {
        if (firstRequest === true) {
            $.each(data, function (key, value) {
                dataSeries1.push({x: value[0], y: value[1]});
                dataSeries2.push({x: value[0], y: value[2]});
                dataSeries3.push({x: value[0], y: value[3]});
                firstRequest = false;
            });
        } else if (typeof (data[9]) === "undefined" && previousRequest !== data.toString()) {
            let val = data[data.length - 1];
            dataSeries1.push({x: val[0], y: val[1]});
            dataSeries2.push({x: val[0], y: val[2]});
            dataSeries3.push({x: val[0], y: val[3]});
        } else {
            if (previousRequest.toString() !== data.toString()) {
                dataSeries1.push({x: data[9][0], y: data[9][1]});
                dataSeries2.push({x: data[9][0], y: data[9][2]});
                dataSeries3.push({x: data[9][0], y: data[9][3]});
                dataSeries1.shift();
                dataSeries2.shift();
                dataSeries3.shift();
            }
        }
        previousRequest = data;
        chart.render();
        setTimeout(updateData, 15000)
    }

    function updateData() {
        $.getJSON("../m/"+machine_id).done(addData)
    }

    updateData();

}
