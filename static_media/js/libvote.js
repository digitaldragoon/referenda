/* Slide advanced panel in and out */
function set_panel_slide() {
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

function ContentLoader() {

}
ContentLoader.prototype.frame = function(races) {
    $.get('../components/frame/', function (data) {
                $('#inner-frame').html(data); 

                var lst = document.createElement('ul');

                $(lst).append('<li id="progress_item_setup" class="progress-item in-progress">Setup</li>');

                for (race in races) {
                    $(lst).append('<li id="progress_item_' + race  + '" class="progress-item"><a>' + races[race] + '</a></li>');
                }

                $('#progress-frame').append(lst);
                set_panel_slide();
            });

    $.get('../components/setup/', function (data) {
                $('#race-frame').html(data);
            });
}
ContentLoader.prototype.race = function(race) {
    $.get('../components/race/' + race + '/', function (data) {
                $('#race-frame').html(data); 
            });
}
ContentLoader.prototype.race_list = function(races) {
}

function Session() {
    this.setup_complete = false;
}
/* Login function */
Session.prototype.get_credentials = function() {
    this.user_id = $('#login_user_id').val();
    this.password = $('#login_password').val();
}

function VoteControl() {
    this.session = new Session();
    this.load = new ContentLoader();
}
VoteControl.prototype.login = function() {
    var control = this;
    this.session.get_credentials();
    
    var req_data = {user_id: this.session.user_id, password: this.session.password};
    $.post('.', req_data,
            function (data) {
                if (data.success) {
                    control.session.races = data.races;
                    control.load.frame(data.races);
                    control.disable_links();
                }
                else {
                    alert(data.message);
                }
            }, 'json');
}
VoteControl.prototype.disable_links = function() {
    $('#header a').each( function() { $(this).click(function() { alert('Link disabled while voting!'); return false; }); });
    $('#footer a').each( function() { $(this).click(function() { alert('Link disabled while voting!'); return false; }); });
}
