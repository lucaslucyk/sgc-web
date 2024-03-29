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

async function get_from_api(model, filter, put_in){
  /*
    model: string of relative url for api request
    filter: string for send in api request
    put_in: string of select id where put the results
  */
  var _url = window.location.origin + '/api/get/' + model + '/' + filter + '/';

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

//function for detect style change
(function() {
    orig = $.fn.css;
    $.fn.css = function() {
        var result = orig.apply(this, arguments);
        $(this).trigger('stylechanged');
        return result;
    }
})();

// Add listener to body
$('body').on('stylechanged', function () {
    var _style = $('body').attr("class");

    //change img logo depending nav
    if (_style.indexOf("sidebar-collapse") >= 0) {
      //console.log("collapse");
      $('#logo-big').hide("fast");
      $('#logo-small').show("fast");
    }
    else {
      //console.log("complete");
      $('#logo-small').hide("fast");
      $('#logo-big').show("fast");
    }
});



