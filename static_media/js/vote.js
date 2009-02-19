/* an object with some methods for handling modal dialogs */
var dialog = {
    close: function(dialog) {
                dialog.container.fadeOut(300, function() {
                            dialog.overlay.slideUp(300, function() {
                            $.modal.close();
                            });
                        });
           },
    open: function(dialog) {
                dialog.overlay.slideDown(300, function() {
                        dialog.container.fadeIn(300, function() {
                                dialog.data.show();
                            });
                        });
          },
    show: function(dialog) {
                $(document).oneTime(800, 'foc',  function() {
                            dialog.data.find('a.button')[0].focus();
                        });
          },
    showHigh: function(dialog) {
                dialog.container.css('top', '100px');
          }
};
$.modal.defaults.close = false;
$.modal.defaults.onClose = dialog.close;
$.modal.defaults.onOpen = dialog.open;
$.modal.defaults.onShow = dialog.show;

function Ballot() {
}
Ballot.prototype.json = function() {
    return $('#enc_plaintext_ballot').val();
}

function Session() {
    this.ballot = new Ballot();
}
Session.prototype.get_credentials = function() {
    this.user_id = $('#login_user_id').val();
    this.password = $('#login_password').val();
}
Session.prototype.keygen = function() {
    $('#enc_public_key').val('none');
}

function Controller() {
    this.session = new Session();
}
/* Display a notification to the user */
Controller.prototype.display_message = function (message, node) {
    var btn_cont = '<a href="" class="button continue simplemodal-close">Continue</a>';
    $.modal('<p>' + message + '</p>' + btn_cont); 
}

/* The grand login function - authenticate and load in the election pane */
Controller.prototype.login = function() {
    var control = this;
    this.session.get_credentials();
    
    var req_data = {user_id: this.session.user_id, password: this.session.password};
    $('#login_frame').append($(document.createElement('p')).addClass('wait').text('Logging in...'));
    $.ajax({
            type: 'POST',
            url: '.',
            dataType: 'json',
            data: req_data,
            success: function (data) {
                if (data.status == 'success') {
                    control.session.races = data.races;
                    control.session.friendly_name = data.friendly_name
                    control.session.user_id = data.user_id

                    /* build map of race slugs to race objects */
                    control.session.racemap = {};
                    for (race in data.races) {
                        control.session.racemap[data.races[race].fields.slug] = data.races[race];
                    }

                    control.load_content();
                    document.title = 'Referenda - Vote';
                }
                else if (data.status == 'invalid') {
                    $('#login_frame p.wait').remove();
                    control.display_message(data.message);
                }
                else if (data.status == 'forbidden') {
                    $('#login_frame p.wait').remove();
                    control.display_message(data.message);
                    $('.simplemodal-data .button.continue').click(function() {
                                window.location = '..';
                            });
                }
                else if (data.status == 'duplicate') {
                    $('#login_frame p.wait').remove();
                    control.display_message(data.message);
                    $('.simplemodal-data .button.continue').click(function() {
                                window.location = '..';
                            });
                }
            },
            error: function (data) {
                control.display_message('The server encountered an error while aattempting to log you in. Please try again in a few moments. If the problem persists, <a href="..">contact the administrator</a>.');
                $('#login_frame .wait').remove();

            }
        });
}

/* Disable links in the header and footer to prevent accidental loss of ballot*/
Controller.prototype.disable_links = function() {
    $('#header a').add('#footer a').each( function() { $(this).click(function(e) { e.preventDefault(); control.display_message('Link disabled while voting!', this); }); });
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
    this.session.keygen();
    $('#panel_setup').append(notice);
}

/* Navigate to a particular panel */
Controller.prototype.navigate_to_panel = function(panel_id) {
    var current = $('#progress-frame').data('current');
    if (panel_id != current) {
        $.scrollTo({top:'0px'}, 200);
        $(document).oneTime(300, 'scroll', function() {
            $('#progress_' + current).removeClass('current');
            $('#panel_' + current).hide();
            $('#panel_' + panel_id).show();
            $('#progress-frame').data('current', panel_id);
            $('#progress_' + panel_id).addClass('current');
            });
    }
}

/* Navigate to next panel */
Controller.prototype.navigate_to_next_panel = function() {
    var frame = $('#progress-frame');
    var next_id = frame.find('#progress_' + frame.data('current')).next().attr('id').split('_')[1];
    this.navigate_to_panel(next_id);
}

/* Activate all of the JS interface */
Controller.prototype.activate_controls = function() {
    var control = this;
 
    /* nav links */
    $('#progress-frame').data('current', 'setup');
    $('#progress-frame li a').each(function() {
                $(this).closest('li').click(function() {
                    var id = $(this).closest('li').attr('id').split('_')[1];
                    control.navigate_to_panel(id);
                });
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

    $('li.candidate').add('#progress-frame li a').each(function() {
                $(this).closest('li').fitted();
            });

    /* cast vote button */
    $('.race .button.castvote').click(function() {
                if (control.race_choices_left($(this).closest('div.race')) > 0){
                    var btn_cont = $('<a class="button continue simplemodal-close">Continue</a>');
                    btn_cont.click(function() {
                            control.navigate_to_next_panel();
                        });

                    var content = $('<div><p>You have not used all of your votes in this race (<strong>choose&nbsp;up&nbsp;to&nbsp;' + control.race_num_choices($(this).closest('div.race')) + '</strong>). Are you sure you want to continue? You may change your vote later by clicking on one of the links to the right.</p></div>')
                   content.append(btn_cont).append('<a class="button cancel simplemodal-close">Cancel</a>');
                   $.modal(content);
                }
                else {
                    control.navigate_to_next_panel();
                }
            });

    /* submit link */
    $('#submit_ballot').click(function() {
                var message_pane = $('#submission-pane .message-pane');
                if (control.ballot_is_complete())
                {
                    message_pane.html('');
                }
                else
                {
                    message_pane.html('<p class="warning">Warning! Your ballot is not 100% complete. By submitting now, you are choosing not to use one or more of your votes. Are you sure?</p>');
                }
                $('#submission-pane').modal({
                            onShow: function(d) {
                                dialog.show(d);
                                dialog.showHigh(d);
                                }
                        });

            });
    $('#submission-pane .button.submitballot').click(function() {
                control.submit_ballot();
                $(this).unbind('click');
            });

    /* protect advanced panel from tab focus */
    $('#advanced-panel textarea').focus(function(e) {
                control.open_panel(true);
            });
}

/* Select a candidate */
Controller.prototype.select_candidate = function(candidate) {
    var id = control.get_race_id($(candidate).closest('div.race'));
    if (this.race_choices_left($(candidate).closest('div.race')) > 0) {
        if ($(candidate).find('input').val() == '') {
            control.display_message('Please write in a name to select a write-in candidate.', candidate);
        }
        else {
            $(candidate).addClass('selected');
            this.update_ballot();
        }
    }
    else {
        var numc = this.session.racemap[id].fields.num_choices;
        if (numc <= 1) { var plural = 'candidate'; }
        else { var plural = 'candidates'; }
        control.display_message('You may only select ' + this.session.racemap[id].fields.num_choices + ' ' + plural + '.', candidate);
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
                control.open_panel(false);
            }
            else
            {
                control.close_panel(false);
            }
        });

        /* Trigger an update of the finalize page */
        $('#enc_plaintext_ballot').blur(function() {
                    control.update_finalize()
                }); 

        /* Reveal advanced controls */
        $('#advanced-panel-gate').click(function() {
                    if ($(this).hasClass('checked')) {
                        $(this).removeClass('checked');
                        $('#advanced-panel-controls').css('visibility', 'hidden');
                    }
                    else {
                        $(this).addClass('checked');
                        $('#advanced-panel-controls').css('visibility', 'visible');

                    }
                });
};

/* open the advanced panel */
Controller.prototype.open_panel = function(instant) {
    var panel = $('#advanced-panel');
    if (panel.data('state') == 'closed')
    {
        if (jQuery.browser.msie) { var rightVal = '760px'; }
        else { var rightVal = '0px';}

        if (instant) {
            panel.css('right', rightVal);
        }
        else
        {
            panel.animate({
                    right: rightVal
                }, 'normal');
        }
        panel.data('state', 'open');
    }
}

/* close the advanced panel */
Controller.prototype.close_panel = function(instant) {
    var panel = $('#advanced-panel');
    if (panel.data('state') == 'open')
    {
        if (jQuery.browser.msie) { var rightVal = '0px'; }
        else { var rightVal = '-760px';}

        if (instant) {
            panel.css('right', rightVal);
        }
        else
        {
            panel.animate({
                    right: rightVal
                }, 'normal');
        }
        panel.data('state', 'closed');
    }
}

/* Get the id of the enclosing rance */
Controller.prototype.get_race_id = function (node) {
    return $(node).closest('div.race').attr('id').split('_')[1];
}

/* Submit the ballot! */
Controller.prototype.submit_ballot = function() {
    var control = this;
    $('#submission-pane').append('<p class="wait">Submitting your ballot...</p>');

    var data = {
        user_id: this.session.user_id,
        password: this.session.password,
        ballot:  this.session.ballot.json(),
        public_key: $('#enc_public_key').val(),
        signature: 'none'
    };

    $.ajax({
                type: 'POST',
                url: '../submit/',
                dataType: 'json',
                data: data,
                success: function(data) {
                    $('#submission-pane').fadeOut(200, function() {
                        control.handle_submit_response(data);
                        });
                },
                error: function(data) {
                    $('#submission-pane').fadeOut(200, function() {
                        control.handle_submit_error(data);
                        });
                }
            });
}

/* Handle response to ballot submission */
Controller.prototype.handle_submit_response = function(data) {
    var control = this;
    var pane = $('#submission-pane');
    pane.empty();
    if (data.status == 'success') {
        pane.append('<h1>Success!</h1>');
        pane.append('<p>' + data.message + '</p>');
        pane.append('<p><strong>Your receipt:</strong> ' + data.receipt + '</p>');
        pane.append($('<a class="button continue">Continue</a>').click(function() { $.modal.close(); window.location = '../../../'; }));
    }
    else if (data.status == 'duplicate') {
        pane.append('<h1>Duplicate Vote</h1>');
        pane.append('<p>' + data.message + '</p');
        pane.append('<p>If you believe that you have received this message in error, please <a href="..">contact the administrator</a>.</p>');
        pane.append($('<a class="button cancel">Cancel</a>').click(function() { $.modal.close(); }));
    }
    else if (data.status == 'forbidden') {
        pane.append('<h1>Authorization Failed</h1>');
        pane.append('<p>' + data.message + '</p');
        pane.append('<p>You may try again by entering your username and password below. If the problem persists, please <a href="..">contact the administrator</a>.</p>');
        pane.append('<ul class="form"><li><input type="text" id="login_user_id" value="' + control.session.user_id + '" /></li><li><input type="password" id="login_password" value="' + control.session.password + '" /></li></ul>');
        pane.append($('<a class="button submitballot">Submit ballot</a>').click(function() { control.session.get_credentials(); control.submit_ballot(); }));
        pane.append($('<a class="button cancel">Cancel</a>').click(function() { $.modal.close(); }));
    }
    else if (data.status == 'invalid') {
        pane.append('<h1>Corrupted Vote</h1>');
        pane.append('<p>' + data.message + '</p');
        pane.append('<p>Please re-check your ballot selections. If the problem persists, please <a href="..">contact the administrator</a>.</p>');
        pane.append($('<a class="button cancel">Cancel</a>').click(function() { $.modal.close(); }));
    }

    pane.fadeIn(200);
}

/* Handle server error on ballot submission */
Controller.prototype.handle_submit_error = function(data) {
    var pane = $('#submission-pane');
    pane.empty();
    pane.append('<h1>Server Error</h1><p>The server has encountered an error while trying to process your data. Please try again in a few moments. If the problem persists, <a href="..">contact the administrator</a>.');
    pane.append($('<a class="button continue">Continue</a>').click(function() { $.modal.close() }));
    pane.fadeIn(200);
}

/* Initialize */
var control = new Controller();

$(document).ready(function () {
        $('#login_submit').click(function () {
                control.login();
            });
});
