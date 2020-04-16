
// //for detect after of de-select field
// $(inputSearch).change(function(){
//  //console.log("was changed");
//  console.log(inputSearch.val());
// });

//for second search
// $(document).ready(function () {
//  $('select').selectize({
//    sortField: 'text'
//  });

//    });

//for select2 initialize
// $(document).ready(function() {
//     $('.js-example-basic-multiple').select2();
// });

//for select all in results table
$('.results_selectAll').click(function(e){
    var table = $(e.target).closest('table');
    $('td input:checkbox',table).prop('checked',this.checked);
});

//format HH:MM for time inputs
$(".hour-input").keypress(function(e){
  e.preventDefault();
  var number = parseInt(e.key);
    
  if(!isNaN(parseInt(e.key))){
    var inputVal = $(this).val();
    if (inputVal.length < 5) {
      //(logical expression) ? True : False ;
      var sep = (inputVal.length == 1) ? ":": "";
      //update input text
      $(this).val(inputVal + number + sep);
    }
  }
});

//const inputSearch = $('#empleados-search');

// detect enter press on input
$('[api-model-search=true]').keypress(function(e){
  var code = (e.code ? e.keyCode : e.which);
  if (code == 13){
    //for don't sent form
    e.preventDefault();

    //get input value
    var cv = $(this).val();

    //get all coincident employees
    if (cv.length >= 4) {
      const results = get_from_api($(this).attr("model-search"), cv, $(this).attr("put-in"));
  }
  }
});

// //for authomatic change detect
// $(inputSearch).on('input', function(e){
//  var cv = inputSearch.val()
//  if (cv.length >= 4) {
//    const results = get_empleados(cv);
//  }
// });

async function get_from_api(model, filter, put_in){
  /*
    model: string of relative url for api request
    filter: string for send in api request
    put_in: string of select id where put the results
  */
  var _url = window.location.origin + '/api/get/' + model + '/' + filter + '/';

  //get model filter from internal api
  //const res = await fetch(url);
  //const json = await res.json();

  //remove all current options
  $("#"+ put_in +" option").remove();

  $.getJSON(_url, function(json){
    //add options with results
    $.each(json.results, function(i, item){
      $("#" + put_in).append("<option value='" + item.id + "'>" + item.text + "</option>");
    });
  });

  $("#"+ put_in).focus();
}

async function get_day_classes(put_in){

  var randomColorGenerator = function () {
    return '#' + (Math.random().toString(16) + '0000000').slice(2, 8);
  };

  var url = window.location.origin + '/api/get/day_classes/';
  const res = await fetch(url);
  const json = await res.json();

  var labelNames = [];
  var values = [];
  var colors = []

  $.each(json.results, function(i, item){
    labelNames.push(item.label);
    values.push(item.cantidad);
    colors.push(randomColorGenerator());
  });

  var ctx = document.getElementById(put_in).getContext('2d');
  var myChart = new Chart(ctx, {
  type: 'bar',
  data: {
      labels: labelNames,
      datasets: [
        {
          label: "",
          data: values,
          backgroundColor: colors,
        }
      ]
  },
  options: {
      scales: {
          yAxes: [{
              ticks: {
                  beginAtZero: true
              }
          }]
      },
      responsive: true,
      maintainAspectRatio: true,
      legend: {
          position: 'none'
      },
      title: {
          display: true
      },
      animation: {
          animateScale: true,
          animateRotate: true
      }
  }
  });

}

function get_storageData(){
  console.log(localStorage.getItem("testing"));
}
/* storage management */

$(document).ready(function() {
  if ($('#myChart').length) {
    const graph = get_day_classes("myChart");
  }
  if ($('#graph-sedes').length) {
    const graph = get_day_classes("graph-sedes");
  }

});



