$('[action_btn=true]').click(function (e) {
  e.preventDefault();

  var task_name = $(this).attr("task_name");

  //loading spinner
  $('div[role=status][task_name='+task_name+']').show('fast');

  var currentUrl = window.location.href;
  var form = $('#actions-form').serializeArray();
  form.push({ name: 'command', value: $(this).attr("command")});
  form.push({ name: 'task_name', value: task_name });

  $.post(
    {
      url: currentUrl,
      data: form,
      datatype: 'json',
    },
    function (response) {
      if (response.success) {
        location.reload();
      }
      else {
        $('div[role=status][task_name=' + task_name + ']').hide('fast');
        alert(response.error);
      }
    }
  );

});