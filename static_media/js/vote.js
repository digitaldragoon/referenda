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

/* Display a notification to the user */
VoteControl.prototype.display_message = function (message, node) {
    alert(message + ' (from ' + node + ')');
}

/* The grand login function - authenticate and load in the election pane */
VoteControl.prototype.login = function() {
    var control = this;
    this.session.get_credentials();
    
    var req_data = {user_id: this.session.user_id, password: this.session.password};
    $.post('.', req_data,
            function (data) {
                if (data.success) {
                    control.session.races = data.races;
                    control.session.friendly_name = data.friendly_name
                    control.session.user_id = data.user_id

                    /* build map of race slugs to race objects */
                    control.session.racemap = {};
                    for (race in data.races) {
                        control.session.racemap[data.races[race].fields.slug] = data.races[race];
                    }

                    control.load_content();
                }
                else {
                    control.display_message(data.message);
                }
            }, 'json');
}

/* Disable links in the header and footer to prevent accidental loss of ballot*/
VoteControl.prototype.disable_links = function() {
    $('#header a').add('#footer a').each( function() { $(this).click(function() { control.display_message('Link disabled while voting!', this); return false; }); });
}

/* Load in the basic content for the election */
VoteControl.prototype.load_content = function() {
    this.disable_links();
    var control = this;
    $.get('../content/', function(data) {
                var data = $(data);
                control.prune_races(data);

                /* prepend a nice greeting */
                $(data).find('#panel_setup h2').after($(document.createElement('p')).text('Welcome, ' + control.session.friendly_name + '!'));

                $('#inner-frame').html(data);
                control.set_panel_slide();
                control.configure();

            });
}

/* Prunes list of races to those received in the login */
VoteControl.prototype.prune_races = function(root) {
    var control = this;
    var root = root;
    var races = this.session.races;
    $(root).find('#panel-frame').children('.race').each(function () {
                var id = control.get_race_id(this);

                if (control.session.racemap[id] == null) {
                    $(root).find('#progress_' + id).remove();
                    $(this).remove();
                }

            });
}

/* Set up crypto keys */
VoteControl.prototype.configure = function () {
    var cont = document.createElement('a');
    $(cont).addClass('button').addClass('continue').click(function() {
                control.activate_controls();
                control.navigate_to_panel(control.session.races[0].fields.slug);
            });

    var notice = document.createElement('p');
    $(notice).attr('id', 'crypto-notice').addClass('wait').text('Please wait while we generate your cryptography keys...').oneTime('3s', 'keygen', function() { $(this).replaceWith(cont);});
    $('#panel_setup').append(notice);
}

/* Navigate to a particular panel */
VoteControl.prototype.navigate_to_panel = function(panel_id) {
    var current = $('#progress-frame').data('current');
    if (panel_id != current) {
        $('#panel_' + current).toggle();
        $('#panel_' + panel_id).toggle();
        $('#progress-frame').data('current', panel_id);
    }
}

/* Activate all of the JS interface */
VoteControl.prototype.activate_controls = function() {
    var control = this;
 
    /* nav links */
    $('#progress-frame').data('current', 'setup');
    $('#progress-frame li a').click(function() {
                var id = $(this).closest('li').attr('id').split('_')[1];
                control.navigate_to_panel(id);
            });
    $('#progress_setup').removeClass('in-progress').addClass('completed');

    /* candidate selection */
    $('li.candidate').fitted();
    $('li.candidate').click(function(e) {
                if (e.target.tagName != 'INPUT') {
                    if ($(this).hasClass('selected') == true) {
                        control.deselect_candidate(this);
                    }
                    else {
                        control.select_candidate(this);
                    }
                }
            });

    $('li.candidate .info input').keyup(function() {
                if ($(this).closest('li').hasClass('selected')) {
                    control.compute_ballot();
                }
            });
}

/* Select a candidate */
VoteControl.prototype.select_candidate = function(candidate) {
    if (this.check_race_is_full($(candidate).closest('div.race')) > 0) {
        if ($(candidate).find('input').val() == '') {
            control.display_message('please write in a name', candidate);
        }
        else {
            $(candidate).addClass('selected');
            this.compute_ballot();
        }
    }
    else {
        control.display_message('too many choices!', candidate);
    }
}

/* Deselect a candidate */
VoteControl.prototype.deselect_candidate = function(candidate) {
    $(candidate).removeClass('selected');
    this.compute_ballot();
}

/* Check to see if the maximum number of candidates for a race have been selected. Returns the difference between the number of currently selected candidates and the number of possible candidates (positive means there are still choices to make) */
VoteControl.prototype.check_race_is_full = function(race) {
    var id = control.get_race_id(race);
    return this.session.racemap[id].fields.num_choices - $(race).find('li.candidate.selected').length;
}

/* Compute and update the state of the ballot */
VoteControl.prototype.compute_ballot = function() {
    var control = this;
    $('#panel-frame').children('.race').each(function () {
                var result = control.compute_single_ballot(this);
            });
}

/* Compute the results of a single ballot race */
VoteControl.prototype.compute_single_ballot = function (race) {
    var id = control.get_race_id(race);
    $(race).find('li.candidate.selected').each(function() {
                alert($(this).find('.info input').val());
            });
}

/* Set the advanced control panel to slide */
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

/* Get the id of the enclosing rance */
VoteControl.prototype.get_race_id = function (node) {
    return $(node).closest('div.race').attr('id').split('_')[1];
}

/* Initialize */
control = new VoteControl();

$(document).ready(function () {
        $('#login_submit').click(function () {
                control.login();
            });
});
