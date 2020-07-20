
function get_labels(datalist) {
  var labels = [];
  $.each(datalist, function (i, month_data) {
    labels.push(month_data.date);
  });
  return labels;
}

function prepare_values(labels, items) {
  var pre_values = {}
  $.each(labels, function (i, label) {
    pre_values[label] = 0;
  });

  $.each(items, function (i, data) {
    pre_values[data.date] = data.quantity;
  });

  var prepared_values = [];
  $.each(pre_values, function (month, quantity) {
    prepared_values.push(quantity);
  });
  return prepared_values;
}

function dates_to_names(date_labels) {
  var dates_format = [];
  $.each(date_labels, function (i, date_label) {
    dates_format.push($.format.date(new Date(date_label.split("-")), "MMMM yyyy"));
  });
  return dates_format;
}

async function update_chart(div_id, results) {

  var chart_div = document.getElementById(div_id).getContext('2d');
  var api_labels = get_labels(results[0].results);
  var chart_data = {
    labels: dates_to_names(api_labels),
    datasets: [],
  }
  var chart_options = {
    pointSize: 10,
    pointHoverRadius: 5,
    pointHitRadius: 2,
    pointHoverBorderColor: '#999999',
    maintainAspectRatio: false,
    responsive: true,
    legend: {
      display: true
    },
    scales: {
      xAxes: [{
        gridLines: {
          display: false,
        }
      }],
      yAxes: [{
        gridLines: {
          display: false,
        }
      }]
    }
  }

  $.each(results, function (i, item) {
    var values = {};
    var newDataset = {
      label: item.label,
      backgroundColor: item.bgcolor,
      borderColor: item.color,
      pointBackgroundColor: item.color,
      data: prepare_values(api_labels, item.results)
    }
    chart_data.datasets.push(newDataset);
  });

  var salesChart = new Chart(chart_div, {
    type: 'line',
    data: chart_data,
    options: chart_options
  }
  );
}

async function get_months_chart(div_id) {
  var url = '/api/get/months-chart/';
  $.ajax({
    type: "GET",
    dataType: "json",
    url: url,
    success: function (response) {
      update_chart(div_id, response.results);
    }
  });
}

$(function () {
  //print graph
  get_months_chart("months-chart");
});