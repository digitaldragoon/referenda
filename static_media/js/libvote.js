function Session() {
    this.setup_complete = false;
}
Session.prototype.get_credentials = function() {
    this.user_id = $('#login_user_id').val();
    this.password = $('#login_password').val();
}
Session.prototype.keygen = function() {
    alert('not implemented yet');
}

function VoteControl() {
    this.session = new Session();
}
VoteControl.prototype.login = function() {
    var control = this;
    this.session.get_credentials();
    
    var req_data = {user_id: this.session.user_id, password: this.session.password};
    $.post('.', req_data,
            function (data) {
                if (data.success) {
                    control.session.races = data.races;
                    control.load_content();
                }
                else {
                    alert(data.message);
                }
            }, 'json');
}
VoteControl.prototype.disable_links = function() {
    $('#header a').add('#footer a').each( function() { $(this).click(function() { alert('Link disabled while voting!'); return false; }); });
}
VoteControl.prototype.load_content = function() {
    this.disable_links();
    var control = this;
    $.get('../content/', function(data) {
                $('#inner-frame').html(data);
                control.set_panel_slide();
                control.configure();
            });
}
VoteControl.prototype.configure = function () {
    var cont = document.createElement('a');
    $(cont).addClass('button').addClass('votenow');

    var notice = document.createElement('p');
    $(notice).attr('id', 'crypto-notice').addClass('wait').text('Please wait while we generate your cryptography keys...').oneTime('3s', 'keygen', function() { $(this).replaceWith(cont); control.activate_controls();});
    $('#panel_setup').append(notice);
}
VoteControl.prototype.activate_controls = function() {
    /* nav links */
    $('#progress-frame').data('current', 'setup');
    $('#progress-frame li a').click(function() {
                var id = $(this).closest('li').attr('id').split('_')[1];
                var current = $('#progress-frame').data('current');
                $('#panel_' + current).toggle();
                $('#panel_' + id).toggle();
                $('#progress-frame').data('current', id);
            });
    $('#progress_setup').removeClass('in-progress').addClass('completed');

    /* candidate selection */
    $('li.candidate').fitted();
    $('li.candidate').click(function() {
                var inp = $(this).find('.checkbox input');
                if ($(inp).attr('checked') == true) {
                    $(this).removeClass('selected');
                    $(inp).attr('checked', false);
                }
                else {
                    $(this).addClass('selected');
                    $(inp).attr('checked', true);
                }
            });
}
VoteControl.prototype.set_panel_slide = function() {
        var panel = $('#advanced-panel');
        panel.data('state', 'closed');

        /* fix IE */
        if (jQuery.browser.msie) {
            $('#advanced-panel').css('right', '-800px');
        }

        panel.find('.button').click(function() {
            var panel = $(this).closest('#advanced-panel');
            if (panel.data('state') == 'closed')
            {
                if (jQuery.browser.msie) { var rightVal = '760px'; }
                else { var rightVal = '0px';}

                panel.animate({
                    right: rightVal
                }, 'normal');
                panel.data('state', 'open');
            }
            else
            {
                if (jQuery.browser.msie) { var rightVal = '0px'; }
                else { var rightVal = '-760px';}

                panel.animate({
                    right: rightVal
                }, 'normal');
                panel.data('state', 'closed');
            }
        });
};

