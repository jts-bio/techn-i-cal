// dataSouce: get from url "kdeplot/"
var dataSource;

$.ajax({
  url: "kdeplot/",
  type: "GET",
  dataType: "json",
  async: false,
  success: function(data) {
    dataSource = data;
  }
});

console.log(dataSource);

let xiData = [];
let animationDuration = 1500;
let range = 7,
  startPoint = -3;
for (i = 0; i < range; i++) {
  xiData[i] = startPoint + i;
}
let data = [];

function GaussKDE(xi, x) {
  return (1 / Math.sqrt(2 * Math.PI)) * Math.exp(Math.pow(xi - x, 2) / -2);
}

let N = dataSource.length;

for (i = 0; i < xiData.length; i++) {
  let temp = 0;
  for (j = 0; j < dataSource.length; j++) {
    temp = temp + GaussKDE(xiData[i], dataSource[j]);
  }
  data.push([xiData[i], (1 / N) * temp]);
}

console.log(data);
Highcharts.chart("container", {
  chart: {
    type: "spline",
    animation: true
  },
  title: {
    text: "KDE"
  },

  yAxis: {
    title: { text: null }
  },
  tooltip: {
    valueDecimals: 3
  },
  plotOptions: {
    series: {
      marker: {
        enabled: false
      },
      legend: false,
      dashStyle: "shortdot",
      color: "#ff8d1e",
      pointStart: xiData[0],
      animation: {
        duration: animationDuration
      }
    }
  },
  series: [
    {
      name: "KDE",
      dashStyle: "solid",
      lineWidth: 2,
      color: "#1E90FF",
      data: data
    }
  ]
});