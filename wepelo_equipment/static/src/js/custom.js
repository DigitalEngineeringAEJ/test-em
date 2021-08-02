$( document ).ready(function() {

    $('#date_deadline').val(moment().format('YYYY-MM-DD'));
    $('#priority').combostars({starUrl: '/wepelo_equipment/static/src/libs/img/stars.png',
                                starWidth: 16,
                                starHeight: 15,
                                clickMiddle: true});

    $('#form-schedule-activity').unbind('click').bind('click',function(e){
        $('#ok-modal-alert').modal();
        $("#ok-modal-alert").removeClass('hide');
    });

     $('#form-maintenance-request').unbind('click').bind('click',function(e){
        $('#ok-modal-maintenance-request').modal();
        $("#ok-modal-maintenance-request").removeClass('hide');
    });

    $('#schedule_new_activity').submit(function(event) {
         event.preventDefault();
         event.stopImmediatePropagation();
         var form = $(this);
         var data = new FormData(this)
         jQuery.ajax({
                type: "POST",
                url: '/my/schedule_new_activity',
                async: true,
                processData: false,
                contentType: false,
                dataType: 'json',
                data: data,
                success: function ( data ) {
                    if("error" in eval(eval(data)[0])){
                        $('#ok-modal-alert').modal('hide');
                        $('.alert-danger p').text(eval(eval(data)[0])['error']);
                        $('.alert-danger').css({'display': ''});
                        setTimeout(function() { $(".alert-danger").css('display', 'none'); }, 10000);
                    }
                    if("success" in eval(eval(data)[0])){
                        $('#ok-modal-alert').modal('hide');
                        $('.alert-success').text(eval(eval(data)[0])['success']);
                        $('.alert-success').css('display', '');
                        setTimeout(function() { $(".alert-success").css('display', 'none'); }, 10000);

                 }
                },
                failure: function( data ){
                   console.log( item );
                }

        });


    });

    jQuery.ajax({
            type: "GET",
            url: '/my/schedule_dates',
            async: true,
            processData: false,
            contentType: false,
            dataType: 'json',
            success: async function ( data ) {
                if("success" in eval(eval(data)[0])){
                    var result = eval(eval(data)[0])['success'];
                    var months = eval(eval(data)[0])['months'];
                    if (months){
                     var months  = months;
                    }
                    if (result){
                        var schedule_dates = []
                        for (var i = 0; i < result.length; i++) {
                            var parts =result[i]['date_deadline'].split('-');
                            schedule_dates.push({'startDate': new Date(result[i]['date_deadline']),
                                                'endDate': new Date(result[i]['date_deadline']),
                                                'summary': result[i]['summary']})
                        };
                        await $("#calendar").simpleCalendar({
                          fixedStartDay: 0, // begin weeks by sunday
                          disableEmptyDetails: true,
                          events: schedule_dates,
                          months: months
                        });
                    }
                }
            },
            failure: function( data ){
               console.log( item );
            }

    });

     $('#create_maintenance_request').submit(function(event) {
         event.preventDefault();
         event.stopImmediatePropagation();
         var form = $(this);
         var data = new FormData(this)
         jQuery.ajax({
                type: "POST",
                url: '/my/create_maintenance_request',
                async: true,
                processData: false,
                contentType: false,
                dataType: 'json',
                data: data,
                success: function ( data ) {
                    if("error" in eval(eval(data)[0])){
                        $('#ok-modal-maintenance-request').modal('hide');
                        $('.alert-danger p').text(eval(eval(data)[0])['error']);
                        $('.alert-danger').css({'display': ''});
                        setTimeout(function() { $(".alert-danger").css('display', 'none'); }, 10000);
                    }
                    if("success" in eval(eval(data)[0])){
                        $('#ok-modal-maintenance-request').modal('hide');
                        $('.alert-success').text(eval(eval(data)[0])['success']);
                        $('.alert-success').css('display', '');
                        setTimeout(function() { $(".alert-success").css('display', 'none'); }, 10000);

                 }
                },
                failure: function( data ){
                   console.log( item );
                }

        });


    });

     // onchange request_date
     $('#request_date').on('change', function(event){
        $("#request_date")
            request_date = $("#request_date").val();
            request_date = moment(request_date).format('DD/MM/YYYY');
            serial_number = $("#serial_no").val();
            $('#name').val(serial_number+ '_'+request_date)
        });


             $("#error_message").addClass("hide");

         var transaction_table = $('#protocol_box table').DataTable( {
          'paging'      : false,
          'lengthChange': false,
          'searching'   : false,
          'ordering'    : false,
          'info'        : false,
          'autoWidth'   : false,
          'retrieve'    : true,
            columnDefs: [ {
                orderable: false,
                className: 'select-checkbox',
                targets: 0
            } ],
            select: {
                style:    'multi',
                selector: 'td:first-child'
            },
            order: [[ 1, 'asc' ]]
        } );
        transaction_table.on("click", "th.select-checkbox", function() {
            if ($("th.select-checkbox").hasClass("selected")) {
                transaction_table.rows().deselect();
                $("th.select-checkbox").removeClass("selected");
            } else {
                transaction_table.rows().select();
                $("th.select-checkbox").addClass("selected");
            }
        }).on("select deselect", function() {
            ("Some selection or deselection going on")
            if (transaction_table.rows({
                    selected: true
                }).count() !== transaction_table.rows().count()) {
                $("th.select-checkbox").removeClass("selected");
            } else {
                $("th.select-checkbox").addClass("selected");
            }
        });

     transaction_table.on("click", "tr.groupbyequipment", function() {
         if (! $(this).hasClass("selected")) {
             var rowData =  transaction_table.rows( this ).data();
             for (var i=0; i < rowData.length ;i++){

                 if (! $(rowData[i][0]).data('record') && $(rowData[i][0]).data('equipment_id')){
                    var allData = transaction_table.rows().data();
                    for (var j=0; j < allData.length ;j++){
                     if ($(allData[j][0]).data('record') && $(allData[j][0]).data('equipment_id')  &&  $(allData[j][0]).data('equipment_id') == $(rowData[i][0]).data('equipment_id')){transaction_table.rows(j).select();}}}}}
                 else{
                     var rowData =  transaction_table.rows( this ).data();
                     for (var i=0; i < rowData.length ;i++){
                         if (! $(rowData[i][0]).data('record') && $(rowData[i][0]).data('equipment_id')){
                            var allData = transaction_table.rows().data();
                            for (var j=0; j < allData.length ;j++){
                             if ($(allData[j][0]).data('record') && $(allData[j][0]).data('equipment_id')  &&  $(allData[j][0]).data('equipment_id') == $(rowData[i][0]).data('equipment_id')){transaction_table.rows(j).deselect();}}}}}

        });


    $('#print-protocol-report').click(function(e){
         var datas = transaction_table.rows({selected:  true}).data();
          var data = {};
           var newarray=[];
                for (var i=0; i < datas.length ;i++){
                   if  ($(datas[i][0]).data('record')  && $(datas[i][0]).data('report')){
                   newarray.push($(datas[i][0]).data('record'));

                      }
                }
        var newlink = '/my/protocols/report?protocols=' + newarray;
        $(this).attr("href", newlink);

    });


});
