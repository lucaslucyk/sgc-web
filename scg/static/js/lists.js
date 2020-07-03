$('[btn-get-url=true]').click(function (e) {
  e.preventDefault();
  $(this).addClass('disabled');

  var url = $(this).attr("get-url");
  var periodo = $(this).attr("btn-id");
  var type = $(this).attr("btn-type");

  const loading = $('[loading-id=' + periodo + '][loading-type=' + type + ']');
  const download = $('[download-id=' + periodo + '][download-type=' + type + ']');
  const btn = $(this);
  loading.show();

  $.ajax({
    type: "GET",
    dataType: "json",
    url: url,
    success: function (response) {
      //update download btn
      download.attr("href", response.fileUrl);
      download.attr("role", "link");
      download.attr("aria-disabled", "false");
      download.removeClass('disabled');
      $('<section id="mensajes">\
          <div class="alert alert-success alert-dismissible">\
            <a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>\
              Liquidación actualizada.\
          </div>\
        </section>\
      ').insertBefore('#results');
    },
    error: function (error) {
      $('<section id="mensajes">\
          <div class="alert alert-danger alert-dismissible">\
            <a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>\
              ' + error.responseJSON.message + '\
          </div>\
        </section>\
      ').insertBefore('#results');
    },
    complete: function () {
      loading.hide();
      //remove focus
      btn.blur();
      btn.removeClass('disabled');
    }
  });
});