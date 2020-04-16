// this is the id of the form
$("#formFiltros").submit(function(e) {
  e.preventDefault(); // avoid to execute the actual submit of the form.
  //reset page number and filter
  get_classes(1, 'fecha'); //get classes and update tables
});

$('[view-model-order=true]').click(function(e){
  e.preventDefault();
  append_order($(this).attr("data-order"));
});

$( '#paginatorNav ul' ).on( "click", "li a", function(e) {
  e.preventDefault();
  var page = parseInt($(this).text());
  var actual_page = parseInt($('#paginatorNav ul li.active a').text());

  if (isNaN(page)) {
    var offset = parseInt($(this).attr("tabindex"));
    page = actual_page + offset;
  }

  localStorage.setItem('page', page);

  //console.log(page);
  get_classes(page, localStorage.getItem("order_by"));
});


async function append_order(_order){

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



function get_classes(_page, _order){

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

      //console.log(response.page);
   }
  });
}

function update_paginator(_pages, _page){
  $('#paginatorNav ul li').remove();

  $('#paginatorNav ul').append('\
    <li class="page-item '+ (_page <= 1 ? 'disabled' : '') +'">\
      <a class="page-link" href="#" tabindex="-1">Anterior</a>\
    </li>\
  ');

  for (var i=1; i<=_pages; i++) {
    $('#paginatorNav ul').append('\
      <li class="page-item '+ (i == _page ? 'active' : '') +'"><a class="page-link" href="#">'+ i +'</a></li>\
    ');
  }

  $('#paginatorNav ul').append('\
    <li class="page-item '+ (_page == _pages ? 'disabled' : '') +'">\
      <a class="page-link" href="#" tabindex="1">Siguiente</a>\
    </li>\
  ');

  //console.log(_page + " of " + _pages);
}

function update_table(dataList){
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
      <td class="align-middle">'+ item.ausencia +'</td>\
      <td class="align-middle"><i class="fas fa-'+ (item.confirmada ? 'check': 'times') +'-circle"></i></td>\
    ');

  });
}

function clean_localStorage(){
  localStorage.removeItem("order_by");
  localStorage.removeItem("page");
}

$(document).ready(function() {
  //reset storage management
  clean_localStorage();
});