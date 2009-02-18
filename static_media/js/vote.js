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

function Controller() {
    this.session = new Session();
}
/* Display a notification to the user */
Controller.prototype.display_message = function (message, node) {
    var btn_cancel = '<a class="button cancel simplemodal-close">Cancel</a>';
    $.modal('<p>' + message + '</p>' + btn_cancel, {close: false});
}

/* The grand login function - authenticate and load in the election pane */
Controller.prototype.login = function() {
    var control = this;
    this.session.get_credentials();
    
    var req_data = {user_id: this.session.user_id, password: this.session.password};
    $('#login_frame').append($(document.createElement('p')).addClass('wait').text('Logging in...'));
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
                    $('#login_frame .wait').remove();
                }
            }, 'json');
}

/* Disable links in the header and footer to prevent accidental loss of ballot*/
Controller.prototype.disable_links = function() {
    $('#header a').add('#footer a').each( function() { $(this).click(function() { control.display_message('Link disabled while voting!', this); return false; }); });
}

/* Load in the basic content for the election */
Controller.prototype.load_content = function() {
    this.disable_links();
    var control = this;
    $.get('../content/', function(data) {
                var data = $(data);
                control.prune_races(data);

                /* prepend a nice greeting */
                $(data).find('#panel_setup h2').after($(document.createElement('p')).text('Welcome, ' + control.session.friendly_name + '!'));

                $('#inner-frame').html(data);
                control.activate_panel();
                control.configure();

                /* Initial update of finalize page */
                control.update_ballot();

            });


}

/* Prunes list of races to those received in the login */
Controller.prototype.prune_races = function(root) {
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
Controller.prototype.configure = function () {
    var cont = document.createElement('a');
    $(cont).addClass('button').addClass('continue').click(function() {
                control.activate_controls();
                control.navigate_to_panel(control.session.races[0].fields.slug);
            });

    var notice = document.createElement('p');
    $(notice).attr('id', 'crypto-notice').addClass('wait').text('Please wait while we generate your cryptography keys...').oneTime('3s', 'keygen', function() { $(this).removeClass('wait').append('done!').after(cont);});
    $('#panel_setup').append(notice);
}

/* Navigate to a particular panel */
Controller.prototype.navigate_to_panel = function(panel_id) {
    var current = $('#progress-frame').data('current');
    if (panel_id != current) {
        $('#panel_' + current).toggle();
        $('#panel_' + panel_id).toggle();
        $('#progress-frame').data('current', panel_id);
    }
}

/* Activate all of the JS interface */
Controller.prototype.activate_controls = function() {
    var control = this;
 
    /* nav links */
    $('#progress-frame').data('current', 'setup');
    $('#progress-frame li a').click(function() {
                var id = $(this).closest('li').attr('id').split('_')[1];
                control.navigate_to_panel(id);
            });
    $('#progress_setup').removeClass('in-progress').addClass('completed');

    /* candidate selection */
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
                    control.update_ballot();
                }
            });

    $('li.candidate').add('#progress-frame li').fitted();

    /* submit link */
    $('#submit_ballot').click(function() {
                control.submit_ballot();
            });
}

/* Select a candidate */
Controller.prototype.select_candidate = function(candidate) {
    var id = control.get_race_id($(candidate).closest('div.race'));
    if (this.race_choices_left($(candidate).closest('div.race')) > 0) {
        if ($(candidate).find('input').val() == '') {
            control.display_message('please write in a name', candidate);
        }
        else {
            $(candidate).addClass('selected');
            this.update_ballot();
        }
    }
    else {
        control.display_message('You may only select ' + this.session.racemap[id].fields.num_choices + ' candidates.', candidate);
    }
}

/* Deselect a candidate */
Controller.prototype.deselect_candidate = function(candidate) {
    $(candidate).removeClass('selected');
    this.update_ballot();
}

/* Returns the number of total choices for a race */
Controller.prototype.race_num_choices = function(race) {
    var id = control.get_race_id(race);
    return this.session.racemap[id].fields.num_choices;
}

/* Check to see if the maximum number of candidates for a race have been selected. Returns the difference between the number of currently selected candidates and the number of possible candidates (positive means there are still choices to make) */
Controller.prototype.race_choices_left = function(race) {
    return this.race_num_choices(race) - $(race).find('li.candidate.selected').length;
}

/* Determines whether or not this ballot is complete. */
Controller.prototype.ballot_is_complete = function() {
    var control = this;
    var complete = true;
    $('#panel-frame').find('.race').each(function() {
                complete = complete && control.race_choices_left(this) == 0;
            });

    return complete;
}

/* Update ballot */
Controller.prototype.update_ballot = function() {
    this.compute_ballot();
    this.update_nav_links();
    this.update_finalize();

}

/* Update candidate choices from ballot */
Controller.prototype.update_candidates_from_ballot = function() {
    /*FIXME - implement*/
}

/* update finalize page */
Controller.prototype.update_finalize = function() {
    var control = this;

    var ballot_text = $('#enc_plaintext_ballot').val();
    var ballot = $.parseJSON(ballot_text, true);

    var ol = document.createElement('ul');
    for (key in ballot) {
        var race = control.session.racemap[key];
        var li = document.createElement('li');

        var candidates = '';
        for (candidate in ballot[key]) {
            if (candidates != '') {
                candidates += ', ';
            }
            candidates += ballot[key][candidate];
        }

        if (candidates == '')
        {
            candidates = 'None';
        }

        $(li).html('<strong>' + race.fields.name + '</strong>: ' + candidates);
        $(ol).append(li);
    }

    $('#final_ballot').html(ol);
}

/* Compute and update the state of the ballot */
Controller.prototype.compute_ballot = function() {
    var control = this;
    var result = {};

    /* compile individual race ballots */
    $('#panel-frame').children('.race').each(function () {
                var temp = control.compute_single_ballot(this);
                for (key in temp) {
                    result[key] = temp[key];
                }
            });
    

    $('#enc_plaintext_ballot').val($.toJSON(result, true));
}

/* Compute the results of a single ballot race */
Controller.prototype.compute_single_ballot = function (race) {
    var id = control.get_race_id(race);
    var result = {};
    result[id] = new Array();
    $(race).find('li.candidate.selected').each(function() {
                result[id].push($(this).find('.info input').val());
            });
    return result;
}

/* Update nav links with completed/noncompleted status*/
Controller.prototype.update_nav_links = function () {
    $('#panel-frame').children('.race').each( function() {
                var diff = control.race_choices_left(this);
                var id = control.get_race_id(this);
                var race_control = $('#progress_' + id);
                if (diff > 0) {
                    if (diff == control.race_num_choices($('#panel_' + id))) {
                        $(race_control).removeClass('in-progress').removeClass('completed');
                    }
                    else {
                        $(race_control).addClass('in-progress').removeClass('completed');
                    }
                }
                else {
                    $(race_control).removeClass('in-progress').addClass('completed');
                }
        });
}

/* Set up the advanced control panel */
Controller.prototype.activate_panel = function() {
        var control = this;
        var panel = $('#advanced-panel');
        panel.data('state', 'closed');

        /* fix IE */
        if (jQuery.browser.msie) {
            $('#advanced-panel').css('right', '-800px');
        }

        /* Set slider */
        panel.find('.button').click(function() {
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

        /* Trigger an update of the finalize page */
        $('#enc_plaintext_ballot').blur(function() {
                    control.update_finalize()
                }); 
};

/* Get the id of the enclosing rance */
Controller.prototype.get_race_id = function (node) {
    return $(node).closest('div.race').attr('id').split('_')[1];
}

/* Submit the ballot! */
Controller.prototype.submit_ballot = function() {
    var btn_submit = '<a class="button submitballot">Submit Ballot</a>';
    var btn_cancel = '<a class="button cancel simplemodal-close">Cancel</a>';
    var message = '<h2>Submit your ballot.</h2><p>Are you sure you want to submit your ballot? This will complete your vote.</p>';

    if (control.ballot_is_complete() == false)
    {
        message += '<p class="warning">Warning! Your ballot is not 100% complete. By submitting now, you are choosing not to use one or more of your votes. Are you sure?</p>';
    }

    $.modal(message + btn_submit + btn_cancel, {close: false});

}

/* Initialize */
var control = new Controller();

$(document).ready(function () {
        $('#login_submit').click(function () {
                control.login();
            });
});
