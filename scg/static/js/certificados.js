$('[view-clases-filter=true]').click(function(e){
  e.preventDefault();
  
  update_card('#card-impacto');
  
  var certif_id = $(this).attr("data-id");
  var url = "/api/get/clases_from_certificado/" + certif_id + "/";
  var put_in = $(this).attr("put-results-in");

  get_from_certif(put_in, url);
  
  //remove focus
  $(this).blur();

});

function update_card(card_id){
	//show table
  $(card_id).removeClass('collapsed-card');
  $(card_id + ' div.card-body').removeAttr('style');

  $('html, body').animate({
      scrollTop: $(card_id).offset().top
  }, 500);

  $(card_id + " div div button i").removeClass('fa-plus').addClass('fa-minus');
}

async function get_from_certif(_put_in, _url){
	$.ajax({
   type: "GET",
   dataType: "json",
   url: _url,
   success: function(response){
      update_table(_put_in, response.results);
      //console.log(response.results);
   }
  });
}

async function update_table(put_in, datalist){
	$(put_in + " tr").remove();

	$.each(datalist, function(i, item){
    
    $(put_in).append('<tr></tr>');
    $(put_in + ' tr:last')
    .append('\
      <td>'+ item.empleado +'</td>\
      <td>'+ item.actividad +'</td>\
      <td>'+ item.dia_semana +'</td>\
      <td>'+ $.format.date(new Date(item.fecha.split("-")), "d MMMM yyyy") +'</td>\
      <td>'+ item.horario_desde +'</td>\
      <td>'+ item.horario_hasta +'</td>\
      <td>'+ item.ausencia +'</td>\
    ');
  });

}