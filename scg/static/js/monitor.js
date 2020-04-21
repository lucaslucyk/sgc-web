$("#formFiltros").submit(function(e) {
  /* at send form, get classes and reset orders and page */
  e.preventDefault();

  //show results
  $('body').addClass('sidebar-collapse');
  //change to small logo
  $('#logo-big').hide("fast");
  $('#logo-small').show("fast");
  
  //show results
  $('#actions_results').show("slow");
  $('html, body').animate({
      scrollTop: $("#actions_results").offset().top
  }, 1000);

  //remove all order icons
  $('[view-model-order=true] i').hide();
  //reset storage management
  clean_localStorage();

  //reset flipp and fliiper class
  $('[view-model-order=true] i').removeClass('flipp').addClass('flipper');

  //get classes, reset current page and orders
  //update tables and paginator
  get_classes(1, 'fecha'); 
});

$('[view-model-order=true]').click(function(e){
  e.preventDefault();
  $(this).children('i').show().toggleClass('flipper flipp');
  append_order($(this).attr("data-order"));
});

$( '#paginatorNav ul' ).on( "click", "li a", function(e) {
  /* call the get_classes ajax with page clicked number */

  e.preventDefault();
  var page = parseInt($(this).text());
  var actual_page = parseInt($('#paginatorNav ul li.active a').text());

  if (isNaN(page)) {
    var offset = parseInt($(this).attr("tabindex"));
    page = actual_page + offset;
  }
  localStorage.setItem('page', page);
  get_classes(page, localStorage.getItem("order_by"));
  $('html, body').animate({
      scrollTop: $("#actions_results").offset().top
  }, 500);
});

async function append_order(_order){
  /* append the order key received to the context of orders */

  //trying get item
  var order_by = localStorage.getItem('order_by');
  
  if (order_by == null) {
    order_by = _order;
    localStorage.setItem('order_by', _order);
  }
  else{
    //console.log(order_by.indexOf(_order));
    if (order_by.indexOf(_order) >= 0) {
      if (order_by.indexOf("-"+_order) >= 0) {
        order_by = order_by.replace("-"+_order, _order);
      }
      else{
        order_by = order_by.replace(_order, "-"+_order);
      }
    }
    else{
      order_by += "," + _order;
    }
    localStorage.order_by = order_by;
  }
  //console.log(localStorage.order_by);
  get_classes(localStorage.getItem('page'), order_by);
}

async function get_classes(_page, _order){
  /*  
    get classes with POST method of endpoint view 
    after remove results table and put obtained json data with "update_table" function
    after update paginator with function "update_paginator" and obtained json data 
  */

  var form = $('#formFiltros').serializeArray();
  form.push({name: 'order_by', value: _order});
  form.push({name: 'page', value: _page});

  var currentUrl = window.location.href;

  $.ajax({
   type: "POST",
   dataType: "json",
   url: currentUrl,
   data: form, // serializes the form's elements.
   success: function(response){
      const table = update_table(response.results);
      const paginator = update_paginator(response.pages, response.page);
   }
  });
}

async function update_paginator(_pages, _page){
  /* remove actual and create new paginator with current _page and number of _pages */
  //console.log(_page + " of " + _pages);

  $('#paginatorNav ul li').remove();


  $('#paginatorNav ul').append('\
    <li class="page-item '+ (_page <= 1 ? 'disabled' : '') +'">\
      <a class="page-link" href="#" tabindex="'+ (parseInt(_page) * (-1) + 1 ) +'"><i class="fas fa-step-backward"></i></a>\
    </li>\
  ');

  $('#paginatorNav ul').append('\
    <li class="page-item '+ (_page <= 1 ? 'disabled' : '') +'">\
      <a class="page-link" href="#" tabindex="-1">Anterior</a>\
    </li>\
  ');

  for (var i=1; i<=_pages; i++) {
    $('#paginatorNav ul').append('\
      <li class="page-item '+ (i == _page? 'active' : '') +'"><a class="page-link" href="#">'+ i +'</a></li>\
    ');
  }

  $('#paginatorNav ul').append('\
    <li class="page-item '+ (_page == _pages || _pages == 0 ? 'disabled' : '') +'">\
      <a class="page-link" href="#" tabindex="1">Siguiente</a>\
    </li>\
  ');
  $('#paginatorNav ul').append('\
    <li class="page-item '+ (_page == _pages || _pages == 0 ? 'disabled' : '') +'">\
      <a class="page-link" href="#" tabindex="'+ (parseInt(_pages) - parseInt(_page)) +'"><i class="fas fa-step-forward"></i></a>\
    </li>\
  ');
}

async function update_table(dataList){
  /* recive a list of classes and remove and refresh the container clasesResults */

  $("#clasesResults tr").remove();

  $.each(dataList, function(i, item){
    
    $('#clasesResults').append('<tr></tr>');
    $('#clasesResults tr:last')
    .append('\
      <td class="align-middle">\
        <div class="form-check-inline">\
          <input type="checkbox" id="toProcess_'+ item.id +'" name="toProcess_'+ item.id +'" class="form-check-input check_clases">\
        </div>\
      </td>\
      <td class="align-middle">'+ item.estado +'</td>\
      <td class="align-middle"><i class="fas fa-'+ (item.was_made ? 'check': 'times') +'-circle"></i></td>\
      <td class="align-middle">'+ item.empleado +'</td>\
      <td class="align-middle">'+ (item.reemplazo ? '<strong>'+item.reemplazo+'</strong>': item.empleado) +'</td>\
      <td class="align-middle">'+ item.sede +'</td>\
      <td class="align-middle">'+ item.actividad +'</td>\
      <td class="align-middle">'+ item.dia_semana +'</td>\
      <td class="align-middle">'+ $.format.date(new Date(item.fecha.split("-")), "d MMMM yyyy") +'</td>\
      <td class="align-middle">'+ item.horario_desde +'</td>\
      <td class="align-middle">'+ item.horario_hasta +'</td>\
      <td class="align-middle">'+ (item.modificada ? '<i class="fas fa-exclamation-circle"></i>': '&nbsp;') +'</td>\
      <td class="align-middle">'+ item.ausencia +'</td>\
      <td class="align-middle"><i class="fas fa-'+ (item.confirmada ? 'check': 'times') +'-circle"></i></td>\
    ');
  });
}

function clean_localStorage(){
  /* clean localStorage what can be saved by another functions */
  localStorage.removeItem("order_by");
  localStorage.removeItem("page");
}

$(document).ready(function() {
  //reset storage management
  clean_localStorage();
});