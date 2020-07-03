/** passing to file */
const update_content = [
  '<textarea name="comentario" rows="2" class="form-control">',
  '</textarea>\
  <span class="input-group-append">\
    <button name="update_comment" type="submit" class="btn btn-info btn-flat">Guardar</button>\
    <button class="btn btn-secondary btn-flat" type="button" onclick="update_cancel(',
  ')">Cancelar</button>\
  </span>\
  '
];
function urls_to_tags(text) {
  return text.replace(
    /\bhttp[s]?:\/\/([\w\.-]+\.)+[a-z]{2,}([\/\w\.\-\_\?\=\!\#,\&amp;]+)/gi,
    '<a style="display:contents;" target="_blank" href="$&">$&</a>'
  );
}
function tags_to_urls(text) {
  return text.replace(/<a\ .+>(.+)<\/a>/gi, '$1');
}
function nl_to_br(text) {
  return text.replace('\n', '<br>');
}
function br_to_nl(text) {
  return text.replace('<br>', '\r\n');
}

function update_cancel(comment_id) {
  var form_group = $('[form_group_id=' + comment_id + ']');
  form_group.html(function (i, text) {
    return urls_to_tags(nl_to_br(form_group.find('textarea').html()));
  });
  var edit_btn = $('[edit_id=' + comment_id + ']').removeClass('disabled');
}

$('[btn_action=comment_update]').click(function (e) {
  e.preventDefault();
  $(this).blur().addClass('disabled');
  var comment_id = $(this).attr("edit_id");
  var form_group = $('[form_group_id=' + comment_id + ']');
  form_group.html(function (i, text) {
    return update_content[0] + tags_to_urls(
      br_to_nl(form_group.html().trim())
    ) + update_content[1] + comment_id + update_content[2];
  });
});

$(function () {
  $('[searh_urls=true]').html(function (i, text) {
    return urls_to_tags(text);
  });
});