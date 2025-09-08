// not working currently
$(document).ready(function() {

    // if set these to local variable, will cause modal submit too many times
    var cn;
    var storename;

    const alertPlaceholder = document.getElementById('liveAlertPlaceholder');
    const appendAlert = (message, type) => {
        const wrapper = document.createElement('div');
        wrapper.innerHTML = [
            `<div class="alert alert-${type} alert-dismissible fade show " role="alert">`,
            `   <div>${message}</div>`,
            '   <button type="button" class="close" data-dismiss="alert" aria-label="Close">',
            '<span aria-hidden="true">&times;</span>',
            '</button>',
            '</div>'
        ].join('\n');

        alertPlaceholder.append(wrapper);
    };

    function formatDate(date) {
        var d = new Date(date),
            month = '' + (d.getMonth() + 1),
            day = '' + d.getDate(),
            year = d.getFullYear();
        if (month.length < 2) month = '0' + month;
        if (day.length < 2) day = '0' + day;
        return [year, month, day].join('-');
    };

    function formatTime(date) {
        var d = new Date(date),
            month = '' + (d.getMonth() + 1),
            day = '' + d.getDate(),
            year = d.getFullYear(),
            hour = '' + d.getHours(),
            min = '' + d.getMinutes(),
            sec = '' + d.getSeconds();
        if (month.length < 2) month = '0' + month;
        if (day.length < 2) day = '0' + day;
        if (hour.length < 2) {
            hour = '0' + hour;
        }
        if (min.length < 2) min = '0' + min;
        if (sec.length < 2) sec = '0' + sec;
        return [year, month, day].join('-') + "_" + [hour, min, sec].join(':');
    };

    /*
       nav highlight when a.href == location.pathname
   */

    $(".nav-item").find("li").each(function() {
        var a = $(this).find("a:first")[0];
        // console.log(a);
        if ($(a).attr("href") === location.pathname) {
            $(a).addClass("active");
            console.log("==========================");
        } else {
            $(a).removeClass("active");
            console.log("nnnnnnnnnnnnnnnnnnnnnnnnnnnnn");
        }
    });

    /*
        nav highlight when a.href == location.pathname
    */
    $(".nav-sidebar").find("li").each(function() {
        var a = $(this).find("a:first")[0];
        if ($(a).attr("href") === location.pathname) {
            $(a).addClass("active");
        } else {
            $(a).removeClass("active");
        }
    });

    /* **********************************************
        OpenVPN serivces overview page functions
    ********************************************** */
    // Post to stop an OpenVPN service
    $('tbody').on('click', '.stop_ovpn_service', function() {
        // alert("debug");
        $tr = $(this).closest('tr');
        var data = $tr.children("th").map(function() {
            return $(this).text();
        }).get();

        var current_ob = $(this).closest('tr').find(".server_running_status");

        var s_uuid = data[0];
        // alert(sid);
        $.post("", { 'csrfmiddlewaretoken': window.csrftoken, 'action': "stop_ovpn_service", "s_uuid": s_uuid }, function(result) {
            // alert("debug in jQuery post");
            // window.location.reload();
            // $tr.find(".server_running_status").addClass("text-green").removeClass("text-red");
            if (result['result'] == 'success') {
                current_ob.removeClass("text-green").addClass("text-red");
            }
            appendAlert(result['message'], result['result']);
        });
    });

    // Post to start an OpenVPN service
    $('tbody').on('click', '.start_ovpn_service', function() {
        // alert("debug");
        $tr = $(this).closest('tr');
        var data = $tr.children("th").map(function() {
            return $(this).text();
        }).get();

        var current_ob = $(this).closest('tr').find(".server_running_status");

        var s_uuid = data[0];
        // alert(sid);
        $.post("", { 'csrfmiddlewaretoken': window.csrftoken, 'action': "start_ovpn_service", "s_uuid": s_uuid }, function(result) {
            // alert("debug in jQuery post");
            // window.location.reload();
            // $tr.find(".server_running_status").addClass("text-red").removeClass("text-green");
            if (result['result'] == 'success') {
                current_ob.removeClass("text-red").addClass("text-green");
            }
            appendAlert(result['message'], result['result']);
        });
    });


    /* **********************************************
        OpenVPN serivce detaul page functions
    ********************************************** */
    // a workaround for extra data to post retrieve clinets data
    //https://datatables.net/forums/discussion/74315/passing-data-attributes-via-ajax-using-this
    var tb_openvpn_clients = $("#tb_openvpn_clients").DataTable({
        //"dom": 'Blfrtip',
        "dom": '<"row"<"col"B><"col"f>>rt<"row"<"col"i><"col"p>>',
        "responsive": true,
        "lengthChange": true,
        "autoWidth": false,
        // "responsive": true, "lengthChange": true, "autoWidth": true,
        //"buttons": ["excel", "colvis"],
        "buttons": [{
                extend: 'excel',
                text: 'Excel',
                exportOptions: {
                    modifier: {
                        page: 'all',
                        selected: null,
                        search: 'none',
                    },
                    columns: [0, 1, 2, 3]
                },
            },
            // { extend: 'excel', text: '<i class="fas fa-file-excel" aria-hidden="true"> Excel </i>' },
            "colvis",
            "pageLength"
        ],

        "lengthMenu": [100, 50, 20, "1000"],
        "processing": true,
        "serverSide": true,
        "destroy": true,
        "paging": true,
        //"search": {return: true },
        "ordering": true,
        "order": [5, "desc"],
        "ajax": {
            'url': "clients",
            'type': 'POST',
            'data': function(d) {
                d.action = "action_list_ovpn_clients";
                var current_uuid = $("#tb_openvpn_clients:first").data("openvpn_service_uuid");
                console.log('Current ovpn service UUID: ' + current_uuid);
                d.ovpn_server_uuid = current_uuid;
            },
            'dataType': 'json',
        },
        "columnDefs": [{
                "targets": 0,
                "data": null,
                "render": function(data, type, row) {
                    var temp = data["site_name"] ? data["site_name"] : "Unnamed";
                    var html = "<a href='javascript:void(0);'  class='clientstatus' data-toggle='modal' data-target='#tunclientStatusModal'>" + temp + "</a>"
                    return html;
                }
            },
            {
                "targets": 1,
                "data": null,
                "render": function(data, type, row) {
                    return data["cn"];
                }
            },
            {
                "targets": 2,
                "data": null,
                "render": function(data, type, row) {
                    return data["ip"];
                }
            },
            {
                "targets": 3,
                "data": null,
                "render": function(data, type, row) {
                    var rdate = new Date(data["toggle_time"])
                        // console.log(formatDate(rdate));
                    return formatTime(rdate);
                }
            },
            {
                "targets": 4,
                "data": null,
                "render": function(data, type, row) {
                    var rdate = new Date(data["expire_date"])
                        // console.log(formatDate(rdate));
                    return formatDate(rdate);
                }
            },
            {
                "targets": 5,
                "data": null,
                "render": function(data, type, row) {
                    // console.log(data[5]);
                    var html = data["status"] ? "<i class='fa fa-circle text-green'></i>" : "<i class='fa fa-circle text-red'></i>";
                    return html;
                }
            },
            {
                "targets": 6,
                "orderable": false,
                "data": null,
                "render": function(data, type, row) {
                    // console.log(data[5]);
                    if (data["status"]) {
                        var reg = RegExp(/boss/);
                        if (data["cn"].length == 41 || reg.test(data["cn"])) {
                            var html = "<a href='javascript:void(0);' class='conn4ect443 btn btn-default btn-xs'><i class='far fa-arrow-alt-circle-right'></i> Mgmt</a>"
                            html += "<a href='javascript:void(0);' class='sshConnect btn btn-default btn-xs'><i class='fa fa-terminal'></i> SSH</a>"
                            return html;
                        } else {
                            var html = 'NotApplied';
                            return html;
                        }
                    } else {
                        var html = 'Unreachable';
                        return html;
                    }
                }
            },
            {
                "targets": 7,
                "orderable": false,
                "data": null,
                "render": function(data, type, row) {
                    if (data["status"]) {
                        var reg = RegExp(/boss/);
                        if (data["cn"].length == 41 || reg.test(data["cn"])) {
                            var html = "<a href='javascript:void(0);' class='checkProxyConfig btn btn-default btn-xs'><i class='fa fa-file'></i> proxy</a>"
                            return html;
                        } else {
                            var html = 'NotApplied';
                            return html;
                        }
                    } else {
                        var html = 'Unreachable';
                        return html;
                    }
                }
            },
        ],
        // hide the ProxyConfig check if it is not "super" or "admin"
        "initComplete": function(settings, json) {
            if (settings.jqXHR.responseJSON.privs_group != 'SUPER' && settings.jqXHR.responseJSON.privs_group != 'ADMIN') {
                // alert(settings.jqXHR.responseJSON.privs  );
                tb_openvpn_clients.columns([7]).visible(false);
            }
        }
    });

    $('#tunclientStatusModal').on('shown.bs.modal',
        function(e) {
            storename = $(e.relatedTarget).parent().parent().children(".dtr-control").text();
            cn = $(e.relatedTarget).parent().parent().children(".dtr-control").next().text();
            var thismodal = $('#tunclientStatusModal');
            // thismodal.find('.modal-body').html("<p>storename: " + storename + "</p><p>cn: " + cn + "</p>");
            thismodal.find('.modal-body .display_store_info').html("<p>storename: " + storename + "</p><p>cn: " + cn + "</p>");
            $(this).on('click', '.btn-primary', { 'filename': cn }, function(e) {
                var newstorename = thismodal.find('input').val();
                console.log("newstorename:" + newstorename);
                if (newstorename) {
                    $.post("tunClientsStatus/update/storename", { 'cn': cn, 'newstorename': newstorename }, function(result) {
                        console.log("服务器返回结果：" + result.result);
                        $('#tb_openvpn_clients').DataTable().ajax.reload(); // reload table data
                        $('#tunclientStatusModal').modal('hide'); // hide modal
                    });
                } else {
                    thismodal.find('.modal-body .error_info').html("<p class='text-danger'>Error: failed to update storename!</p>");
                }
            });
        });

    $("#tunclientStatusModal").on("hidden.bs.modal", function(e) {
        // remove the actual elements from the DOM when fully hidden
        $('#tunclientStatusModal').find("input[type=text], textarea").val("");
        $(this).find('form').trigger('reset');
    });

    // Port 443 connection
    $('#tb_openvpn_clients tbody').on('click', '.conn4ect443', function(e) {
        var clientIp = $(this).parent().parent().children().eq(2).text();
        var cn = $(this).parent().parent().children().eq(1).text();
        // console.log(clientIp, cn);
        $.post("checkTunProxyConfig", { 'cn': cn }, function(result) {
            console.log(result);
            if (result['result'] == 'success') {
                var url = "/" + result['url'] + '/';
                var openNewLink = window.open(url);
                openNewLink.focus();
            } else {
                appendAlert(result['message'], result['result']);
            }
        });

    });


    // SSH connection
    // https://service.carel-remote.com/wssh/?hostname=xx&username=yy&password=str_base64_encoded&title=boss-a98bd3ba-cfc3-11ed-94a8-c400ad64f34a
    // https://service.carel-remote.com/wssh/?hostname=192.168.120.62&username=root&title=boss-a98bd3ba-cfc3-11ed-94a8-c400ad64f34a
    $('#tb_openvpn_clients tbody').on('click', '.sshConnect', function(e) {
        var clientIp = $(this).parent().parent().children().eq(2).text();
        var cn = $(this).parent().parent().children().eq(1).text();
        var storename = $(this).parent().parent().children().eq(0).text();
        var url = "/wssh/" + "?hostname=" + clientIp;
        url = url + '&' + "username=root";
        url = url + "&title=" + storename;
        console.log("ssh url: " + url);
        var openNewLink = window.open(url);
        openNewLink.focus();
    });

    // checkProxyConfig button func
    $('#tb_openvpn_clients tbody').on('click', '.checkProxyConfig', function(e) {
        var reqFileName = $(this).parent().parent().children().eq(1).text();
        var clientIp = $(this).parent().parent().children().eq(2).text();
        //alert(reqFileName);
        $.post("checkTunProxyConfig", { 'cn': reqFileName }, function(result) {
            console.log(result);
            if (result['result'] == 'success') {
                var openNewLink = window.open("showTunProxyConfig/" + reqFileName);
                openNewLink.focus();
                // $('#tuntbreqfiles').DataTable().ajax.reload(); // reload table data
            } else {
                appendAlert(result['message'], result['result']);
            }
        });
    });

    /* **********************************************
        tun upload req file page functions
    ********************************************** */

    // update the filename in the input 
    $(".custom-file > input").on("change", function() {
        var filePath = $(this).val();
        if (filePath.length > 0) {
            var arr = filePath.split('\\');
            var fileName = arr[arr.length - 1];
            $('.custom-file-label').text(fileName);
        } else {
            $('.custom-file-label').text("Please select Req file to upload");
        }
    })

    /* **********************************************
        tun mode req file list page functions
    ********************************************** */

    $("#tuntbreqfiles").DataTable({
        //"dom": 'Blfrtip',
        "dom": '<"row"<"col"B><"col"f>>rt<"row"<"col"i><"col"p>>',
        "responsive": true,
        "lengthChange": false,
        "autoWidth": false,
        // "responsive": true, "lengthChange": true, "autoWidth": true,
        "buttons": ["excel", "colvis"],
        "lengthMenu": [5, 50, 100, 1000],
        "processing": true,
        "serverSide": true,
        // "searching": true,
        "destroy": true,
        "paging": false,
        // "pagingType": 'input',
        "ordering": false,
        // "iDisplayLength": 10,
        // "bLengthChange": true,
        // "lengthMenu": [20, 50, 100, 1000],
        "ajax": {
            'url': "tunReqFiles/list",
            'type': 'POST',
            'data': {},
            'dataType': 'json',
        },
        "columnDefs": [{
            "targets": 3,
            "data": null,
            "render": function(data, type, row) {
                var id = '"' + row.id + '"';
                var html = "<a href='javascript:void(0);'  class='reqDelete btn btn-danger btn-xs' data-toggle='modal' data-target='#tunreqDelModal'  ><i class='fa fa-times'></i> Delete</a>"
                    // html += "<a href='javascript:void(0);'   onclick='deleteThisRowPapser(" + id + ")'  class='down btn btn-default btn-xs'><i class='fa fa-arrow-down'></i> Download</a>"
                html += "<a href='javascript:void(0);' class='reqDownload btn btn-default btn-xs'><i class='fa fa-arrow-down'></i> Download</a>"
                return html;
            }
        }],
    });


    // tun mode delete req file
    $('#tunreqDelModal').on('show.bs.modal',
        function(e) {
            var reqFileName = $(e.relatedTarget).parent().parent().children(".dtr-control").text();
            $(this).on('click', '.btn-danger', { 'filename': reqFileName }, function(e) {
                // alert("Deleted!!");
                $.post("tunReqFileList/delete", { 'filename': reqFileName }, function(result) {
                    console.log(result);
                    $('#tuntbreqfiles').DataTable().ajax.reload(); // reload table data
                });
                $('#tunreqDelModal').modal('hide'); // hide modal
            });
        });

    // tun req files download
    $('#tuntbreqfiles tbody').on('click', '.reqDownload', function() {
        var reqFileName = $(this).parent().parent().children(".dtr-control").text();
        //Set the File URL.
        var url = "tunReqFileList/download/" + reqFileName;
        console.log(url);
        $.ajax({
            url: url,
            cache: false,
            xhr: function() {
                var xhr = new XMLHttpRequest();
                xhr.onreadystatechange = function() {
                    if (xhr.readyState == 2) {
                        if (xhr.status == 200) {
                            xhr.responseType = "blob";
                        } else {
                            xhr.responseType = "text";
                        }
                    }
                };
                return xhr;
            },
            success: function(data) {
                //Convert the Byte Data to BLOB object.
                var blob = new Blob([data], { type: "application/octetstream" });

                //Check the Browser type and download the File.
                var isIE = false || !!document.documentMode;
                if (isIE) {
                    window.navigator.msSaveBlob(blob, reqFileName);
                } else {
                    var url = window.URL || window.webkitURL;
                    link = url.createObjectURL(blob);
                    var a = $("<a />");
                    a.attr("download", reqFileName);
                    a.attr("href", link);
                    $("body").append(a);
                    a[0].click();
                    $("body").remove(a);
                }
            }
        });
    });

    /* **********************************************
        OpenVPN plain cert files list page functions
    ********************************************** */
    $("#tb_openvpn_plain_certs").DataTable({
        // "dom": 'Blfrtip',
        "dom": '<"row"<"col"B><"col"f>>rt<"row"<"col"i><"col"p>>',
        "responsive": true,
        "lengthChange": true,
        "autoWidth": false,
        // "responsive": true, "lengthChange": true, "autoWidth": true,
        // "buttons": ["copy", "csv", "excel", "pdf", "print", "colvis"],
        //"buttons": ["excel", "colvis"],
        "buttons": [{
                extend: 'excel',
                text: 'Excel',
                exportOptions: {
                    modifier: {
                        page: 'all',
                        selected: null,
                        search: 'none',
                    },
                    columns: [0, 1, 2, 3]
                },
            },
            // { extend: 'excel', text: '<i class="fas fa-file-excel" aria-hidden="true"> Excel </i>' },
            "colvis",
            "pageLength"
        ],
        "lengthMenu": [100, 50, 20, 1000],
        //
        "processing": true,
        "serverSide": true,
        // "searching": true,
        "destroy": true,
        "paging": true,
        // "pagingType": 'input',
        "ordering": true,
        // "iDisplayLength": 10,
        // "bLengthChange": true,
        // "lengthMenu": [20, 50, 100, 1000],
        "ajax": {
            'url': "plain_certs",
            'type': 'POST',
            'data': { "action": "action_list_ovpn_plain_certs" },
            'dataType': 'json',
        },
        // datatable inline-button
        // https://datatables.net/reference/option/columnDefs
        "columnDefs": [{
                "targets": 0,
                "data": null,
                "render": function(data, type, row) {
                    return data["cert_name"];
                }
            },
            {
                "targets": 1,
                "data": null,
                "orderable": false,
                "render": function(data, type, row) {
                    return data["create_time"];
                }
            },
            {
                "targets": 2,
                "data": null,
                "orderable": false,
                "render": function(data, type, row) {
                    return data["cert_size"];
                }
            },
            {
                "targets": 3,
                "data": null,
                "orderable": false,
                "render": function(data, type, row) {
                    var id = '"' + row.id + '"';
                    var html = "<a href='javascript:void(0);'  class='certDelete btn btn-danger btn-xs' data-toggle='modal' data-target='#tuncertDelModal'  ><i class='fa fa-times'></i> Delete</a>"
                        // html += "<a href='javascript:void(0);'   onclick='deleteCertByFilename(" + 99 + ")'  class='down btn btn-default btn-xs'><i class='fa fa-arrow-down'></i>Download</a>"
                    html += "<a href='javascript:void(0);' class='certDownload btn btn-default btn-xs'><i class='fa fa-arrow-down'></i>Download</a>"
                    return html;
                }
            }
        ],
    });
    /* **********************************************
        OpenVPN encrypy cert files list page functions
    ********************************************** */
    $("#tb_openvpn_encrypt_certs").DataTable({
        // "dom": 'Blfrtip',
        "dom": '<"row"<"col"B><"col"f>>rt<"row"<"col"i><"col"p>>',
        "responsive": true,
        "lengthChange": true,
        "autoWidth": false,
        // "responsive": true, "lengthChange": true, "autoWidth": true,
        // "buttons": ["copy", "csv", "excel", "pdf", "print", "colvis"],
        //"buttons": ["excel", "colvis"],
        "buttons": [{
                extend: 'excel',
                text: 'Excel',
                exportOptions: {
                    modifier: {
                        page: 'all',
                        selected: null,
                        search: 'none',
                    },
                    columns: [0, 1, 2, 3]
                },
            },
            // { extend: 'excel', text: '<i class="fas fa-file-excel" aria-hidden="true"> Excel </i>' },
            "colvis",
            "pageLength"
        ],
        "lengthMenu": [100, 50, 20, 1000],
        //
        "processing": true,
        "serverSide": true,
        // "searching": true,
        "destroy": true,
        "paging": true,
        // "pagingType": 'input',
        "ordering": true,
        // "iDisplayLength": 10,
        // "bLengthChange": true,
        // "lengthMenu": [20, 50, 100, 1000],
        "ajax": {
            'url': "encrypt_certs",
            'type': 'POST',
            'data': { "action": "action_list_ovpn_encrypt_certs" },
            'dataType': 'json',
        },
        // datatable inline-button
        // https://datatables.net/reference/option/columnDefs
        "columnDefs": [{
                "targets": 0,
                "data": null,
                "render": function(data, type, row) {
                    return data["cert_name"];
                }
            },
            {
                "targets": 1,
                "data": null,
                "orderable": false,
                "render": function(data, type, row) {
                    return data["create_time"];
                }
            },
            {
                "targets": 2,
                "data": null,
                "orderable": false,
                "render": function(data, type, row) {
                    return data["cert_size"];
                }
            },
            {
                "targets": 3,
                "data": null,
                "orderable": false,
                "render": function(data, type, row) {
                    var id = '"' + row.id + '"';
                    var html = "<a href='javascript:void(0);'  class='certDelete btn btn-danger btn-xs' data-toggle='modal' data-target='#tuncertDelModal'  ><i class='fa fa-times'></i> Delete</a>"
                        // html += "<a href='javascript:void(0);'   onclick='deleteCertByFilename(" + 99 + ")'  class='down btn btn-default btn-xs'><i class='fa fa-arrow-down'></i>Download</a>"
                    html += "<a href='javascript:void(0);' class='certDownload btn btn-default btn-xs'><i class='fa fa-arrow-down'></i>Download</a>"
                    return html;
                }
            }
        ],
    });

    /* **********************************************
        OpenVPN reqs files list page functions
    ********************************************** */
    $("#tb_openvpn_reqs").DataTable({
        // "dom": 'Blfrtip',
        "dom": '<"row"<"col"B><"col"f>>rt<"row"<"col"i><"col"p>>',
        "responsive": true,
        "lengthChange": true,
        "autoWidth": false,
        // "responsive": true, "lengthChange": true, "autoWidth": true,
        // "buttons": ["copy", "csv", "excel", "pdf", "print", "colvis"],
        //"buttons": ["excel", "colvis"],
        "buttons": [{
                extend: 'excel',
                text: 'Excel',
                exportOptions: {
                    modifier: {
                        page: 'all',
                        selected: null,
                        search: 'none',
                    },
                    columns: [0, 1, 2, 3]
                },
            },
            // { extend: 'excel', text: '<i class="fas fa-file-excel" aria-hidden="true"> Excel </i>' },
            "colvis",
            "pageLength"
        ],
        "lengthMenu": [100, 50, 20, 1000],
        //
        "processing": true,
        "serverSide": true,
        // "searching": true,
        "destroy": true,
        "paging": true,
        // "pagingType": 'input',
        "ordering": true,
        // "iDisplayLength": 10,
        // "bLengthChange": true,
        // "lengthMenu": [20, 50, 100, 1000],
        "ajax": {
            'url': "reqs",
            'type': 'POST',
            'data': { "action": "action_list_ovpn_reqs" },
            'dataType': 'json',
        },
        // datatable inline-button
        // https://datatables.net/reference/option/columnDefs
        "columnDefs": [{
                "targets": 0,
                "data": null,
                "render": function(data, type, row) {
                    return data["cert_name"];
                }
            },
            {
                "targets": 1,
                "data": null,
                "orderable": false,
                "render": function(data, type, row) {
                    return data["create_time"];
                }
            },
            {
                "targets": 2,
                "data": null,
                "orderable": false,
                "render": function(data, type, row) {
                    return data["cert_size"];
                }
            },
            {
                "targets": 3,
                "data": null,
                "orderable": false,
                "render": function(data, type, row) {
                    var id = '"' + row.id + '"';
                    var html = "<a href='javascript:void(0);'  class='certDelete btn btn-danger btn-xs' data-toggle='modal' data-target='#tuncertDelModal'  ><i class='fa fa-times'></i> Delete</a>"
                        // html += "<a href='javascript:void(0);'   onclick='deleteCertByFilename(" + 99 + ")'  class='down btn btn-default btn-xs'><i class='fa fa-arrow-down'></i>Download</a>"
                    html += "<a href='javascript:void(0);' class='certDownload btn btn-default btn-xs'><i class='fa fa-arrow-down'></i>Download</a>"
                    return html;
                }
            }
        ],
    });

    /* **********************************************
        OpenVPN zip certs files list page functions
    ********************************************** */
        $("#tb_openvpn_zip_certs").DataTable({
            // "dom": 'Blfrtip',
            "dom": '<"row"<"col"B><"col"f>>rt<"row"<"col"i><"col"p>>',
            "responsive": true,
            "lengthChange": true,
            "autoWidth": false,
            // "responsive": true, "lengthChange": true, "autoWidth": true,
            // "buttons": ["copy", "csv", "excel", "pdf", "print", "colvis"],
            //"buttons": ["excel", "colvis"],
            "buttons": [{
                    extend: 'excel',
                    text: 'Excel',
                    exportOptions: {
                        modifier: {
                            page: 'all',
                            selected: null,
                            search: 'none',
                        },
                        columns: [0, 1, 2, 3]
                    },
                },
                // { extend: 'excel', text: '<i class="fas fa-file-excel" aria-hidden="true"> Excel </i>' },
                "colvis",
                "pageLength"
            ],
            "lengthMenu": [100, 50, 20, 1000],
            //
            "processing": true,
            "serverSide": true,
            // "searching": true,
            "destroy": true,
            "paging": true,
            // "pagingType": 'input',
            "ordering": true,
            // "iDisplayLength": 10,
            // "bLengthChange": true,
            // "lengthMenu": [20, 50, 100, 1000],
            "ajax": {
                'url': "zip_certs",
                'type': 'POST',
                'data': { "action": "action_list_ovpn_zip_certs" },
                'dataType': 'json',
            },
            // datatable inline-button
            // https://datatables.net/reference/option/columnDefs
            "columnDefs": [{
                    "targets": 0,
                    "data": null,
                    "render": function(data, type, row) {
                        return data["cert_name"];
                    }
                },
                {
                    "targets": 1,
                    "data": null,
                    "orderable": false,
                    "render": function(data, type, row) {
                        return data["create_time"];
                    }
                },
                {
                    "targets": 2,
                    "data": null,
                    "orderable": false,
                    "render": function(data, type, row) {
                        return data["cert_size"];
                    }
                },
                {
                    "targets": 3,
                    "data": null,
                    "orderable": false,
                    "render": function(data, type, row) {
                        var id = '"' + row.id + '"';
                        var html = "<a href='javascript:void(0);'  class='certDelete btn btn-danger btn-xs' data-toggle='modal' data-target='#tuncertDelModal'  ><i class='fa fa-times'></i> Delete</a>"
                            // html += "<a href='javascript:void(0);'   onclick='deleteCertByFilename(" + 99 + ")'  class='down btn btn-default btn-xs'><i class='fa fa-arrow-down'></i>Download</a>"
                        html += "<a href='javascript:void(0);' class='certDownload btn btn-default btn-xs'><i class='fa fa-arrow-down'></i>Download</a>"
                        return html;
                    }
                }
            ],
        });

    // tun mode delete cert file
    $('#tuncertDelModal').on('show.bs.modal',
        function(e) {
            var certFileName = $(e.relatedTarget).parent().parent().children(".dtr-control").text();
            $(this).on('click', '.btn-danger', { 'filename': certFileName }, function(e) {
                // alert("Deleted!!");
                $.post("tunCertFileList/delete", { 'filename': certFileName }, function(result) {
                    // console.log(result)
                    $('#tuntbcertfiles').DataTable().ajax.reload();
                });
                $('#tuncertDelModal').modal('hide'); // hide modal
            });
        })

    // tun cert files download
    $('#tuntbcertfiles tbody').on('click', '.certDownload', function() {
        var certFileName = $(this).parent().parent().children(".dtr-control").text();
        //Set the File URL.
        var url = "tunCertFileList/download/" + certFileName;
        console.log(url);
        $.ajax({
            url: url,
            cache: false,
            xhr: function() {
                var xhr = new XMLHttpRequest();
                xhr.onreadystatechange = function() {
                    if (xhr.readyState == 2) {
                        if (xhr.status == 200) {
                            xhr.responseType = "blob";
                        } else {
                            xhr.responseType = "text";
                        }
                    }
                };
                return xhr;
            },
            success: function(data) {
                //Convert the Byte Data to BLOB object.
                var blob = new Blob([data], { type: "application/octetstream" });

                //Check the Browser type and download the File.
                var isIE = false || !!document.documentMode;
                if (isIE) {
                    window.navigator.msSaveBlob(blob, certFileName);
                } else {
                    var url = window.URL || window.webkitURL;
                    link = url.createObjectURL(blob);
                    var a = $("<a />");
                    a.attr("download", certFileName);
                    a.attr("href", link);
                    $("body").append(a);
                    a[0].click();
                    $("body").remove(a);
                }
            }
        });
    });

    /* **********************************************
        tun mode generic cert file list page functions
    ********************************************** */
    $("#tuntbgenericcertfiles").DataTable({
        "dom": 'Blfrtip',
        "responsive": true,
        "lengthChange": false,
        "autoWidth": false,
        // "responsive": true, "lengthChange": true, "autoWidth": true,
        // "buttons": ["copy", "csv", "excel", "pdf", "print", "colvis"],
        "buttons": ["excel", "colvis"],
        "lengthMenu": [5, 50, 100, 1000],
        //
        "processing": true,
        "serverSide": true,
        // "searching": true,
        "destroy": true,
        "paging": false,
        // "pagingType": 'input',
        "ordering": false,
        // "iDisplayLength": 10,
        // "bLengthChange": true,
        // "lengthMenu": [20, 50, 100, 1000],
        "ajax": {
            'url': "tunGenericCertFiles/list",
            'type': 'POST',
            'data': {},
            'dataType': 'json',
        },
        // datatable inline-button
        // https://datatables.net/reference/option/columnDefs
        "columnDefs": [{
            "targets": 3,
            "data": null,
            "render": function(data, type, row) {
                var id = '"' + row.id + '"';
                var html = "<a href='javascript:void(0);'  class='certDelete btn btn-danger btn-xs' data-toggle='modal' data-target='#tungenericcertDelModal'  ><i class='fa fa-times'></i> Delete</a>"
                    // html += "<a href='javascript:void(0);'   onclick='deleteCertByFilename(" + 99 + ")'  class='down btn btn-default btn-xs'><i class='fa fa-arrow-down'></i>Download</a>"
                html += "<a href='javascript:void(0);' class='certDownload btn btn-default btn-xs'><i class='fa fa-arrow-down'></i>Download</a>"
                return html;
            }
        }],
    });


    $('#tungenericcertDelModal').on('show.bs.modal',
        function(e) {
            var certFileName = $(e.relatedTarget).parent().parent().children(".dtr-control").text();
            $(this).on('click', '.btn-danger', { 'filename': certFileName }, function(e) {
                // alert("Deleted!!");
                $.post("tunGenericCertFileList/delete", { 'filename': certFileName }, function(result) {
                    // console.log(result)
                    $('#tuntbgenericcertfiles').DataTable().ajax.reload();
                });
                $('#tungenericcertDelModal').modal('hide'); // hide modal
            });
        });

    $('#tuntbgenericcertfiles tbody').on('click', '.certDownload', function(e) {
        var certFileName = $(this).parent().parent().children(".dtr-control").text();
        e.preventDefault();
        var url = 'tunGenericCertFileList/download/' + certFileName;
        console.log(url);
        window.location.href = url;
    });

    /* **********************************************
        admin user page functions
    ********************************************** */
    /*
    // table user list tb_users_list
    $("#tb_users_list").DataTable({
        "dom": '<"row"<"col"B><"col"f>>rt<"row"<"col"i><"col"p>>',
        "responsive": true,
        "lengthChange": true,
        "autoWidth": false,
        // "responsive": true, "lengthChange": true, "autoWidth": true,
        "buttons": [{
                extend: 'excel',
                text: 'Excel',
                exportOptions: {
                    modifier: {
                        page: 'all',
                        selected: null,
                        search: 'none',
                    },
                    columns: [0, 1, 2, 3]
                },
            },
            // { extend: 'excel', text: '<i class="fas fa-file-excel" aria-hidden="true"> Excel </i>' },
            "colvis",
            "pageLength"
        ],
        "lengthMenu": [10, 50, 100, "1000"],
        "processing": true,
        "serverSide": true,
        "destroy": true,
        "paging": true,
        "ordering": true,
        "order": [1, "asc"],
        "ajax": {
            'url': "list/users",
            'type': 'post',
            'data': {},
            'dataType': 'json',
        },
        "columnDefs": [{
                "targets": 0,
                "data": null,
                "orderable": false,
                render: function(data, type, row, meta) {
                    // return meta.row + 1;
                    return data["user_id"];
                }
            },
            {
                "targets": 1,
                "data": null,
                "render": function(data, type, row) {
                    return data["username"];
                }
            },
            {
                "targets": 2,
                "data": null,
                "render": function(data, type, row) {
                    if (data["user_type"] == '1') {
                        return "admin";
                    } else {
                        return "user";
                    }
                }
            },
            {
                "targets": 3,
                "data": null,
                "render": function(data, type, row) {
                    return data["display_name"];
                }
            },
            {
                "targets": 4,
                "data": null,
                "render": function(data, type, row) {
                    if (data["status"] == '0') {
                        return "Disabled";
                    } else {
                        return "Enabled";
                    }
                }
            },

            {
                "targets": 5,
                "orderable": false,
                "data": null,
                "render": function(data, type, row) {
                    // console.log(data[5]);
                    //if (data["status"] == '0' || data["status"] == '1') {
                    //     <th>
                    //     <button class="btn btn-default" data-user-id="${user.userId }"
                    //         data-toggle="modal" data-target="#changeStatus">禁用</button>
                    //     <button class="btn btn-danger" data-user-id="${user.userId }"
                    //         data-toggle="modal" data-target="#deleteUser">删除</button>
                    // </th>
                    var status = null;
                    var op = null;
                    if (data["username"] != 'super') {
                        if (data["status"] == '0') {
                            status = "success";
                            op = "Enabled";
                        } else {
                            status = "danger";
                            op = "Disabled";
                        }
                        var html = "<button class='btn btn-" + status + "' data-username=";
                        html += data["username"];
                        html += " data-user-status=" + data["status"]
                        html += " id='changeStatus'>" + op + "</button>"

                        html += "<button class='btn btn-primary' data-user_id=";
                        html += data["user_id"];
                        html += " data-toggle='modal' data-target='#updateUser'>Edit</button>"

                        html += "<button class='btn btn-danger' data-username=";
                        html += data["username"];
                        html += " data-toggle='modal' data-target='#deleteUser'>Delete</button>"
                        return html;
                    } else {
                        return "HIDED!";
                    }
                }
            },
        ],
    });
    */

    /*
    $('#updateUser').on('shown.bs.modal', function(event) {
        var button = $(event.relatedTarget);
        var user_id = button.data('user_id');
        var modal = $(this);
        var params = {
            "user_id": user_id
        };
        $.ajax({
            url: 'admin/getUser',
            type: "post",
            data: params,
            success: function(result) {
                user = result;
                console.log(user);
                modal.find('#update-user_id').val(user.user_id);
                modal.find('#update-user_type').val(user.user_type);
                modal.find('#update-username').val(user.username);
                modal.find('#update-password').val('');
                modal.find('#update-display_name').val(user.display_name);
            }
        })
    });

    $('#deleteUser').on('shown.bs.modal', function(event) {
        var button = $(event.relatedTarget);
        var username = button.data('username');
        var modal = $(this);
        console.log(username);
        modal.find('#delete-username').val(username);

        // submit in html
        // $(this).on('click', '#delete_student', { 'username': username }, function(e) {
        //     console.log(username);
        //     if (username) {
        //         $.post("admin/delete/user", { 'username': username, 'op': "delete" }, function(result) {
        //             // $('#tb_users_list').DataTable().ajax.reload(); // reload table data
        //             $('#deleteUser').modal('hide'); // hide modal
        //         });
        //     }
        // });
    });
    */

    /**
    $('#addUser').on('shown.bs.modal', function(event) {
        var modal = $(this);
        $.ajax({
            url: 'admin/getStudents',
            type: "post",
            data: { "unregistered": 1 },
            success: function(result) {
                // var students = result[0];
                // console.log(result);
                var i = 0;
                for (i = 0; i < Object.keys(result).length; i++) {
                    student_no = result[i]["student_no"];
                    student_name = result[i]["student_name"];
                    modal.find("select[name='student_no']").append("<option value=" + student_no + ">" + student_name + "</option>");
                };
                // $('#mySelect').append($('<option>').val('head').text('Head'));
                // <option value="${student.studentNo }">${student.studentName }</option>
            }
        })
    });
    **/

    // $('#clientStatusModal').on('shown.bs.modal',
    //     function(e) {
    //         storename = $(e.relatedTarget).parent().parent().children(".dtr-control").text();
    //         cn = $(e.relatedTarget).parent().parent().children(".dtr-control").next().text();
    //         var thismodal = $('#clientStatusModal');
    //         thismodal.find('.modal-body').html("<p>storename: " + storename + "</p><p>cn: " + cn + "</p>");
    //         $(this).on('click', '.btn-primary', { 'filename': cn }, function(e) {
    //             var newstorename = thismodal.find('input').val();
    //             console.log("newstorename:" + newstorename);
    //             if (newstorename) {
    //                 $.post("service/clientstatus/update", { 'cn': cn, 'newstorename': newstorename }, function(result) {
    //                     $('#tbclientstatus').DataTable().ajax.reload(); // reload table data
    //                     $('#clientStatusModal').modal('hide'); // hide modal
    //                 });
    //             }
    //         });

    //     });

    $(document).on('click', '#changeStatus', function(e) {
        // storename = $(e.relatedTarget).parent().parent().children(".dtr-control").text();
        // var test = $(e.target).text(); // button word
        var target_user = $(e.target).parent().parent().children().eq(1).text();
        var user_status = $(e.target).data('user-status');
        console.log(target_user + ", " + user_status);

        $.post("admin/user/toggle", { 'target_user': target_user, "user_status": user_status }, function(result) {
            // console.log(result)
            $('#tb_users_list').DataTable().ajax.reload();
        });
    });
    // $(document).on('click', '#changeStatus', function() {
    //     alert("button is clicked");
    // });

    /* **********************************************
        management page functions
    ********************************************** */

    var tbSystemConfigTable = $("#tbSystemConfig").DataTable({
        "dom": 'lfrt',
        "responsive": false,
        "lengthChange": false,
        "autoWidth": false,
        "processing": true,
        "serverSide": true,
        "searching": false,
        "destroy": true,
        "paging": false,
        "ordering": false,
        "ajax": {
            'url': "system/config",
            'type': 'POST',
            'data': {},
            'dataType': 'json',
        },
        "columnDefs": [{
                "targets": 0,
                "data": null,
                "render": function(data, type, row) {
                    //console.log(data);
                    return data['item'];
                }
            },
            {
                "targets": 1,
                "data": null,
                "render": function(data, type, row) {
                    console.log(data);
                    var html = '<input type="text" class="form-control" value=' + data['ivalue'] + ' name=' + data['item'] + ' required>';
                    return html;
                }
            },
        ],
    });

    // System config table update function
    // $('#updateSystemConfig').click(function() {
    //     var data = tbSystemConfigTable.$('input, select').serialize();
    //     //alert(
    //     //    "The following data would have been submitted to the server: \n\n"+
    //     //    data.substr( 0, 120 )+'...'
    //     // );
    //     $.post("system/updateConfig", data, function(result) {
    //         console.log(result);
    //         appendAlert(result['message'], result['result']);
    //         $('#tbSystemConfig').DataTable().ajax.reload();
    //     });
    // });

});
