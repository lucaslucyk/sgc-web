$(function () {

  //show results
  $('body').addClass('sidebar-collapse');
  //change to small logo
  $('#logo-big').hide("fast");
  $('#logo-small').show("fast");

  /* initialize the calendar
      -----------------------------------------------------------------*/
  //Date for the calendar events (dummy data)
  // var date = new Date()
  // var d = date.getDate(),
  //   m = date.getMonth(),
  //   y = date.getFullYear()

  var Calendar = FullCalendar.Calendar;
  var calendarEl = document.getElementById('calendar');

  var calendar = new Calendar(calendarEl, {
    plugins: ['bootstrap', 'dayGrid', 'timeGrid'],
    header: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay'
    },
    'themeSystem': 'bootstrap',
    editable: false, //change to false for dont edit
    droppable: false, // this allows things to be dropped onto the calendar !!!
    defaultView: 'timeGridWeek',
    contentHeight: 450,
    //height: 600,
    allDaySlot: false,
  });

  calendar.render();


  //for proccess rest of data
  $('[sede-filter=true]').click(function (e) {
    e.preventDefault();
    
    //put overlay to inform user
    $('.overlay').css('display', 'flex');

    //remove focus
    $(this).blur();

    get_classes($(this).attr("sede-name"));

  });

  async function get_classes(_sede) {
    /*  
      get classes with POST method of endpoint view 
      after remove results table and put obtained json data with "update_table" function
      after update paginator with function "update_paginator" and obtained json data 
    */

    var form = $('#filtro-sedes').serializeArray();
    form.push({ name: 'sede', value: _sede });

    var currentUrl = window.location.href;

    $.ajax({
      type: "POST",
      dataType: "json",
      url: currentUrl,
      data: form, // serializes the form's elements.
      success: function (response) {
        const table = update_calendar(response.results);
      }
    });
  }

  function newInstance(clazz, arguments, scope) {
    return new (Function.prototype.bind.apply(clazz, [scope].concat(arguments)));
  }

  async function update_calendar(dataList) {
    /* recive a list of classes and remove and refresh the container clasesResults */

    //deleting events
    $.each(calendar.getEvents(), function (i, item) {
      item.remove();
    })

    var randomColorGenerator = function () {
      return '#' + (Math.random().toString(16) + '0000000').slice(2, 8);
    };

    $.each(dataList, function (i, item) {
      //adding events
      calendar.addEvent({
        title: item.ejecutor,
        start: newInstance(Date, item.start),
        end: newInstance(Date, item.end),
        allDay: false,
        backgroundColor: randomColorGenerator(), //Success (green)
        borderColor: '#d3d3d3' //Success (green)
      });
    });

    //hide overlay
    $('.overlay').hide("fast");
  }
});

