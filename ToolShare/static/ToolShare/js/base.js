/////
// Screen resize component sizing
/////
$(window).on("resize", function() {
    sidebar = $("#sidebar-fixed");
    sidebar.css("width", sidebar.parent().width());
});
$(window).resize();

/////
// Tool List component
/////
$("body").on("click", ".toggle-btn", function() {
    $(this).text(function(i, old) {
        return old == "Show" ? "Hide" : "Show";
    });
}).on("click", ".tool-list .text-right a", function(e) {
    e.preventDefault();
    href = $(this).attr("href");
    action = href.substring(1, 5);
    id = href.substring(5);
    $(".toolDetail" + id).collapse(action);
    $("#tool-list-" + id + " .toggle-btn").text(function(i, old) {
        return action == "show" ? "Hide" : "Show";
    });
});

/////
// Datepicker component
/////
$(".datepicker").datepicker({
    minDate: 0,
    numberOfMonths: [1, 2],
    beforeShowDay: function(date) {
        for (var i in window.blacklistedDays[this.id]) {
            start = $.datepicker.parseDate($.datepicker._defaults.dateFormat, blacklistedDays[this.id][i][0]);
            end   = $.datepicker.parseDate($.datepicker._defaults.dateFormat, blacklistedDays[this.id][i][1]);
            if (start <= date && date <= end) return [false];
        }
        var date1 = $.datepicker.parseDate($.datepicker._defaults.dateFormat, $("#" + this.id + "StartDay").val());
        var date2 = $.datepicker.parseDate($.datepicker._defaults.dateFormat, $("#" + this.id + "EndDay").val());
        return [true, date1 && ((date.getTime() == date1.getTime()) || (date2 && date >= date1 && date <= date2)) ? "dp-highlight" : ""];
    },
    onSelect: function(dateText, inst) {
        var date1 = $.datepicker.parseDate($.datepicker._defaults.dateFormat, $("#" + this.id + "StartDay").val());
        var date2 = $.datepicker.parseDate($.datepicker._defaults.dateFormat, $("#" + this.id + "EndDay").val());
        var selDate = $.datepicker.parseDate($.datepicker._defaults.dateFormat, dateText);
        if ((!date1 || date2) || selDate < date1) {
            $("#" + this.id + "StartDay").val(dateText);
            $("#" + this.id + "EndDay").val("");
            $(this).datepicker();
        } else {
            var endDate;
            for (var i in window.blacklistedDays[this.id]) {
                endDate = $.datepicker.parseDate($.datepicker._defaults.dateFormat, blacklistedDays[this.id][i][1]);
                if (date1 < endDate && endDate < selDate) return;
            }
            $("#" + this.id + "EndDay").val(dateText);
            $(this).datepicker();
        }
    }
});

/////
// Form confirmation
/////

var confirmModal = $('<div class="modal fade" tabindex="-1" role="dialog">' +
'  <div class="modal-dialog">' +
'    <div class="modal-content">' +
'      <div class="modal-header">' +
'        <button type="button" class="close" data-dismiss="modal">&times;</button>' +
'        <h4 class="modal-title">Are you sure?</h4>' +
'      </div>' +
'      <div class="modal-body" id="confModalBody"></div>' +
'      <div class="modal-footer">' +
'        <button type="button" class="btn btn-default" data-dismiss="modal">No</button>' +
'        <button type="button" class="btn btn-primary">Yes</button>' +
'      </div>' +
'    </div>' +
'  </div>' +
'</div>').modal({
    show: false
});
confirmModal.find(".btn-primary").on("click", function() {
    confirmModal.modal("hide");
    if (confirmModal.data("type") == "form") {
        confirmModal.data("form").data("confirmed", "yes").submit();
    } else if (confirmModal.data("type") == "link") {
        confirmModal.data("link").data("confirmed", "yes").click();
    }
});

$("form.confirm").on("submit", function(e) {
    form = $(this);
    if (form.data("confirmed") != "yes") {
        e.preventDefault();
        confirmModal.find("#confModalBody").html(form.data("message").replace(/%([^%]*?)%/g, function(match, p1) {
            var val = form.find("input[name='" + p1 + "']").val();
            return val;
        }));
        confirmModal.data("form", form).data("type", "form");
        confirmModal.modal("show");
    }
});
$("a.confirm").on("click", function(e) {
    link = $(this);
    if (link.data("confirmed") != "yes") {
        e.preventDefault();
        confirmModal.find("#confModalBody").html(link.data("message"));
        confirmModal.data("link", link).data("type", "link");
        confirmModal.modal("show");
    } else {
        window.location = link.prop("href");
    }
});