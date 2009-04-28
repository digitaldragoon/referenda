/* an object with some methods for handling modal dialogs */
var dialogAnimations = {
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
                dialog.container.css('position', 'absolute');
          }
};
$.modal.defaults.close = false;
$.modal.defaults.onClose = dialogAnimations.close;
$.modal.defaults.onOpen = dialogAnimations.open;
$.modal.defaults.onShow = dialogAnimations.show;


REFERENDA.BOOTH = {};

/* Object which holds ballot information. */
REFERENDA.BOOTH.Ballot = Class.extend({
    /* Creates an empty ballot */
    init: function() {
        this.answers = {};
        for (var race in REFERENDA.BOOTH.SESSION.election.eligibleRaces) {
            race = REFERENDA.BOOTH.SESSION.election.eligibleRaces[race];
            this.answers[race] = [];
        }
        this.receipt = Random.getRandomInteger(new BigInt("340282366920938463463374607431768211456", 10)); // 2^128
    },

    /* Encrypts this ballot */
    encrypt: function() {
        var ciphertext = {};

        for (var key in this.answers) {
            // do encryption
            var pk = REFERENDA.BOOTH.SESSION.election.pk;

            ciphertext[key] = {};

            ciphertext[key]['receipt'] = ElGamal.encryptString($.toJSON(this.receipt), pk).toJSONObject();
            ciphertext[key]['answers'] = new Array();
                
            // "real" answers
            for (var i = 0; i < this.answers[key].length; i++) {
                ciphertext[key]['answers'][i] = ElGamal.encryptString($.toJSON(this.answers[key][i]), pk).toJSONObject();
            }

            // "padding" answers to fill out incomplete ballots
            while (i < REFERENDA.BOOTH.SESSION.getRace(key).numChoices) {
                ciphertext[key]['answers'][i] = ElGamal.encryptString($.toJSON('None'), pk).toJSONObject();
                i++;
            }
        }

        this.ciphertext = $.toJSON(ciphertext);
    },

    isComplete: function() {
        var complete = true;
        for (var key in this.answers) {
            complete = complete && this.answers[key].length == REFERENDA.BOOTH.SESSION.getRace(key).numChoices;
        }

        return complete;
    },

    toJSON: function() {
        var finalBallot = {};

        for (var key in this.answers) {
            if (this.answers[key].length > 0) {
                finalBallot[key] = {
                    receipt: this.receipt,
                    answers: this.answers[key]
                };
            }
        }

        return $.toJSON(finalBallot);
    },

    /* Seals this ballot by dumping plaintext data from memory */
    seal: function() {
        //FIXME
    },

    verifyJSON: function(jsonString) {
        //FIXME
    }
});

/*
 * Holds the session state.
 */
REFERENDA.BOOTH.Session = Class.extend({
    init: function(user_id, password, data) {
        this.user_id = user_id;
        this.password = password;
        this.friendly_name = data['friendlyName'];
        this.election = new REFERENDA.Election(data['election']);
    },

    getRace: function(raceSlug) {
        return this.election.raceMap[raceSlug];
    }
});

/* The object which controls the voting booth (navigation, data gathering, etc.) */
REFERENDA.BOOTH.Controller = Class.extend({
    init: function(element) {
        this.isLoggedIn = false;
        this.container = element;
        this.currentPanel = 'setup';
        this.TEMPLATES = {};

        // setup templates
        this.TEMPLATES.LOGIN_FRAME = new REFERENDA.Template('login_frame');
        this.TEMPLATES.MESSAGE_ALERT = new REFERENDA.Template('message_alert');
        this.TEMPLATES.MESSAGE_CONFIRM = new REFERENDA.Template('message_confirm');
        this.TEMPLATES.BALLOT_PANE = new REFERENDA.Template('ballot_pane');
        this.TEMPLATES.SUBMISSION_PANE = new REFERENDA.Template('submission_pane');
    },

    /* Activates the nav links on the progress panel. */
    activateNavLinks: function() {
        /* Add navigation hook to each link */
        $(this.container).find('#progress-frame li a').each(function() {
                    $(this).closest('li').click(function() {
                        var slug = $(this).closest('li').attr('id').split('_')[1];
                        REFERENDA.BOOTH.CONTROL.navigateToPanel(slug);
                    });
                });

        /* "complete" setup tab */
        $(this.container).find('#progress_setup').removeClass('in-progress').addClass('completed');
    },
   
    /* Activate the selection and deselection of candidates. */
    activateCandidateSelection: function() {

        // update the ballot when new candidates are selected
        $(this.container).find('li.candidate').click(function(e) {
                    if (e.target.tagName != 'INPUT') {
                        var raceSlug = $(this).closest('.race').attr('id').split('_')[1];
                        if ($(this).hasClass('selected')) {
                            $(this).removeClass('selected');
                        }
                        else {
                            var choices = REFERENDA.BOOTH.SESSION.getRace(raceSlug).numChoices;
                            if (REFERENDA.BOOTH.BALLOT.answers[raceSlug].length < choices) {
                                if ($(this).find('.info input').val() == '') {
                                    REFERENDA.BOOTH.CONTROL.displayMessage('Please write in a name to select a wrtie-in candidate.');
                                }
                                else {
                                    $(this).addClass('selected');
                                }
                            }
                            else {
                                if (choices <= 1) { var plural = 'candidate'; }
                                else { var plural = 'candidates'; }
                                REFERENDA.BOOTH.CONTROL.displayMessage('You may only select ' + choices + ' ' + plural + '.');
                            }
                        }

                        REFERENDA.BOOTH.CONTROL.updateBallot(raceSlug);
                    }
                });
    
        // update the ballot as write-in candidates are entered
        $(this.container).find('li.candidate .info input').keyup(function() {
                    var raceSlug = $(this).closest('.race').attr('id').split('_')[1];
                    if ($(this).val() == '') {
                        $(this).closest('li').removeClass('selected');
                    }

                    REFERENDA.BOOTH.CONTROL.updateBallot(raceSlug);
                });
    
        $(this.container).find('li.candidate').add('#progress-frame li a').each(function() {
                    $(this).closest('li').fitted();
                });

    },

    /* Activate the "Cast Vote" buttons, which runs a check to see if the user has used up all of their votes, and then navigates to the next panel. */
    activateCastVoteButtons: function() {
        $(this.container).find('.race .button.castvote').click(function() {
            var raceSlug = $(this).closest('.race').attr('id').split('_')[1];
            /* check to ensure all votes are accounted for */
            if (REFERENDA.BOOTH.SESSION.getRace(raceSlug).numChoices > REFERENDA.BOOTH.BALLOT.answers[raceSlug].length) {
                REFERENDA.BOOTH.CONTROL.displayConfirmation('You have not used all of your votes in this race (<strong>choose&nbsp;up&nbsp;to&nbsp;' + REFERENDA.BOOTH.SESSION.getRace(raceSlug).numChoices + '</strong>). Are you sure you want to continue? You may change your vote later by clicking on one of the links to the right.', function() { REFERENDA.BOOTH.CONTROL.navigateToNextPanel(); });

            }
            else {
                REFERENDA.BOOTH.CONTROL.navigateToNextPanel();
            }
        });
    },

    activateSubmissionButton: function() {
        $(this.container).find('#submit_ballot').click(function() {
                    if (REFERENDA.BOOTH.BALLOT.isComplete()) {
                        var message = '';
                    }
                    else {
                        var message = '<p class="warning">Warning! Your ballot is not 100% complete. By submitting now, you are choosing not to use one or more of your votes. Are you sure?<?p>';
                    }

                    var template = REFERENDA.BOOTH.CONTROL.TEMPLATES.SUBMISSION_PANE;
                    template.processTemplate({message: message});
                    var messagePane = template.getContents();

                    $(messagePane).modal({
                            onShow: function(d) {
                                dialogAnimations.show(d);
                                dialogAnimations.showHigh(d);
                            },
                            position: ['20px',]
                        });

                    var waitMessage = REFERENDA.createWaitMessage('Please wait while we encrypt your ballot...');
                    $(messagePane).find('.submitballot').before(waitMessage);

                    REFERENDA.BOOTH.BALLOT.encrypt();
                    
                    waitMessage.done('done!');

                    // activate submit link
                    $(messagePane).find('.button.submitballot').click(function() {
                        var data = {
                            user_id: REFERENDA.BOOTH.SESSION.user_id,
                            password: REFERENDA.BOOTH.SESSION.password,
                            ballot: REFERENDA.BOOTH.BALLOT.ciphertext
                        };

                        var waitMessage = REFERENDA.createWaitMessage('Submitting your ballot...');
                        $(messagePane).append(waitMessage);

                        $.ajax({
                                type: 'POST',
                                url: './submit/',
                                dataType: 'json',
                                data: data,
                                success: function(data) {
                                    $(messagePane).fadeOut(200, function() {
                                            $(messagePane).empty();
                                            if (data.status == 'success') {
                                                $(messagePane).append('<h1>Success!</h1>');
                                                $(messagePane).append('<p>' + data.message + '</p>');
                                                $(messagePane).append('<p>In order to verify that your ballot was counted correctly, <strong>please save this receipt number</strong>. When you go to verify your ballot, you will be prompted to enter it.</p>');
                                                $(messagePane).append('<p><strong>Your receipt:</strong><br/>' + REFERENDA.BOOTH.BALLOT.receipt.toJSONObject() + '</p>');
                                                $(messagePane).append($('<a class="button continue">Continue</a>').click(function() { $.modal.close(); window.location = '../../../'; }));
                                            }
                                            else if (data.status == 'duplicate') {
                                                $(messagePane).append('<h1>Duplicate Vote</h1>');
                                                $(messagePane).append('<p>' + data.message + '</p>');
                                                $(messagePane).append('<p>If you believe that you have received this message in error, please <a href="..">contact the administartor</a>.</p>');
                                                $(messagePane).append($('<a class="button cancel">Cancel</a>').click(function() { $.modal.close(); }));
                                            }
                                            else if (data.status == 'forbidden') {
                                                $(messagePane).append('<h1>Authorization Failed</h1>');
                                                $(messagePane).append('<p>' + data.message + '</p>');
                                                $(messagePane).append('<p>Please log in and try again. If the problem persists, please <a href="..">contact the administrator</a></p>');
                                                $(messagePane).append($('<a class="button continue">Continue</a>').click(function() { $.modal.close(); window.location = './'; }));
                                            }
                                            else if (data.status == 'invalid') {
                                                $(messagePane).append('<h1>Corrupted Vote</h1>');
                                                $(messagePane).append('<p>' + data.message + '</p>');
                                                $(messagePane).append('<p>Please re-check your ballot selections. If the problem persists, please <a href="..">contact the administrator</a>.</p>');
                                                $(messagePane).append($('<a class="button cancel">Cancel</a>').click(function() { $.modal.close(); }));
                                            }
                                            $(messagePane).fadeIn(200);
                                        });

                                },
                                error:  function(data) {
                                    $(messagePane).fadeOut(200, function() {
                                        $(messagePane).empty();
                                        $(messagePane).append('<h1>Server Error</h1>');
                                        $(messagePane).append('<p>The server has encountered an error while trying to process your data. Please try again in a few moments. If the problem persists, <a href="..">contact the administrator</a>.</p>');
                                        $(messagePane).append($('<a class="button continue">Continue</a>').click(function() { $.modal.close(); }));
                                        $(messagePane).fadeIn(200);
                                    });

                                }

                             });
                    });
        });
    },

    activateControls: function() {
        this.activateNavLinks();
        this.activateCandidateSelection();
        this.activateCastVoteButtons();
        this.activateSubmissionButton();
    },

    /* Bring up the login screen */
    displayLogin: function() {
        // display templates
        this.TEMPLATES.LOGIN_FRAME.processTemplate();
        var contents = this.TEMPLATES.LOGIN_FRAME.getContents();

        // make the login fields submit on enter keypresses
        contents.find('#login_user_id').add(contents.find('#login_password')).keypress(function(e) {
                    if (e.which == 13) {
                        contents.find('#login_submit').click();
                    }
                });
        
        // set login event
        contents.find('#login_submit').click(function() {
                    var user_id = contents.find('#login_user_id').val();
                    var password = contents.find('#login_password').val();
                    REFERENDA.BOOTH.CONTROL.login(user_id, password);
                });

        // watermark fields
        contents.find('#login_user_id').watermark('username');
        contents.find('#login_password').watermark('password');

        $(this.container).html(contents);

        contents.find('#login_user_id').focus();
    },

    disableLinks: function() {
        $('#header a').add('#footer a').each( function() { $(this).click(function(e) { e.preventDefault(); REFERENDA.BOOTH.CONTROL.displayMessage('Link disabled while voting!'); }); });
    },

    /* Bring up a modal confirmation dialog */
    displayConfirmation: function(message, continueCallback, cancelCallback) {
        var template = REFERENDA.BOOTH.CONTROL.TEMPLATES.MESSAGE_CONFIRM;
        template.processTemplate({message: message});
        var messagePane = template.getContents();

        if (continueCallback != undefined)
            $(messagePane).find('.button.continue').click(continueCallback);

        if (cancelCallback != undefined)
            $(messagePane).find('.button.cancel').click(cancelCallback);

        $(messagePane).modal({close: false});
        messagePane.find('a.button.continue').focus();
    },

    /* Bring up a modal alert message */
    displayMessage: function(message, callback) {
        var template = REFERENDA.BOOTH.CONTROL.TEMPLATES.MESSAGE_ALERT;
        template.processTemplate({message: message});
        var messagePane = template.getContents();

        if (callback != undefined) {
            $(messagePane).find('.simplemodal-close').click(callback);
        }

        $(messagePane).modal({close: false});
        messagePane.find('a.button.continue').focus();
    },

    /* Load in the ballot pane */
    loadBallotPane: function() {
        var pane = REFERENDA.BOOTH.CONTROL.TEMPLATES.BALLOT_PANE;
        pane.processTemplate();
        pane = pane.getContents();

        // prune the list of races to only those we are eligible to vote for
        for (var race in REFERENDA.BOOTH.SESSION.election.races) {
            race = REFERENDA.BOOTH.SESSION.election.races[race];
            if (jQuery.inArray(race.slug, REFERENDA.BOOTH.SESSION.election.eligibleRaces) < 0) {
                $(pane).find('#panel_' + race.slug).remove();
                $(pane).find('#progress_' + race.slug).html(race.name + ' (ineligible)').addClass('grey');
            }
        }

        $(this.container).html(pane);

        var continueButton = $('<a class="button continue">Continue</a>');
        $(continueButton).click(function() { REFERENDA.BOOTH.CONTROL.activateControls(); REFERENDA.BOOTH.CONTROL.navigateToPanel(REFERENDA.BOOTH.SESSION.election.eligibleRaces[0]); });
        $(this.container).find('#panel_setup').append(continueButton);

        REFERENDA.BOOTH.CONTROL.updateBallot();
        this.disableLinks();
    },

    /* The grand login function - authenticate and load in ballot pane */
    login: function(user_id, password) {
        if (!this.isLoggedIn) {
        var request_data = {user_id: user_id, password: password};

        $(this.container).find('#login_frame').find('p.wait').remove();
        var waitMessage = REFERENDA.createWaitMessage('Logging in...');
        $(this.container).find('#login_frame').append(waitMessage);

        BigInt.setup();
        $.ajax({
                type: 'POST',
                url: '.',
                dataType: 'json',
                data: request_data,
                success: function (data) {
                    if (data.status == 'success') {
                        REFERENDA.BOOTH.SESSION = new REFERENDA.BOOTH.Session(user_id, password, data);
                        REFERENDA.BOOTH.BALLOT = new REFERENDA.BOOTH.Ballot();
                        REFERENDA.BOOTH.CONTROL.isLoggedIn = true;
                        REFERENDA.BOOTH.CONTROL.loadBallotPane();
                    }
                    else if (data.status == 'invalid') {
                        waitMessage.remove();
                        REFERENDA.BOOTH.CONTROL.displayMessage(data.message);
                    }
                    else if (data.status == 'unavailable') {
                        waitMessage.remove();
                        REFERENDA.BOOTH.CONTROL.displayMessage(data.message);
                    }
                    else if (data.status == 'forbidden') {
                        waitMessage.remove();
                        REFERENDA.BOOTH.CONTROL.displayMessage(data.message,
                            function() {
                                window.location = '..';
                            });
                    }
                    else if (data.status == 'duplicate') {
                        waitMessage.remove();
                        REFERENDA.BOOTH.CONTROL.displayMessage(data.message,
                            function() {
                                window.location = '..';
                            });
                    }
                },
                // something's broken - display an error
                error: function (data) {
                    REFERENDA.BOOTH.CONTROL.displayMessage('The server encountered an error while attempting to log you in. Please try again in a few moments. If the problem persists, <a href="..">contact the administrator</a>.');
                    $('#login_frame .wait').remove();
                }
           });
        }
    },

    navigateToNextPanel: function() {
        var races = REFERENDA.BOOTH.SESSION.election.eligibleRaces;

        if (REFERENDA.BOOTH.CONTROL.currentPanel == 'finalize') {
            REFERENDA.BOOTH.CONTROL.navigateToPanel(races[0]);
        }
        else {
            var i = 0;
            while (i < races.length && races[i] != REFERENDA.BOOTH.CONTROL.currentPanel) {
                i++;
            }

            if (i+1 == races.length) REFERENDA.BOOTH.CONTROL.navigateToPanel('finalize');
            else REFERENDA.BOOTH.CONTROL.navigateToPanel(races[i+1]);
        }
    },
    
    navigateToPanel: function(panelSlug) {
        if (panelSlug != this.currentPanel) {
            $.scrollTo({top:'0px'}, 200);
            $(document).oneTime(300, 'scroll', function() {
                        $(this.container).find('#progress_' + REFERENDA.BOOTH.CONTROL.currentPanel).removeClass('current');
                        $(this.container).find('#panel_' + REFERENDA.BOOTH.CONTROL.currentPanel).hide();
                        $(this.container).find('#panel_' + panelSlug).show();
                        REFERENDA.BOOTH.CONTROL.currentPanel = panelSlug;
                        $(this.container).find('#progress_' + panelSlug).addClass('current');
                    });
        }

    },

    /* Updates the ballot by scanning for currently selected candidates */
    updateBallot: function(raceSlug) {
        // update a single race
        if (raceSlug != undefined) {
            var answers = [];
            $(this.container).find('#panel_' + raceSlug).find('li.candidate.selected').each(function() {
                        var candidateSlug = $(this).find('.info input').val();
                        answers[answers.length] = candidateSlug;
                    });

            var raceControl = $(this.container).find('#progress_' + raceSlug);
            if (answers.length == 0) {
                $(raceControl).removeClass('in-progress').removeClass('completed');
            }
            else if (answers.length == REFERENDA.BOOTH.SESSION.getRace(raceSlug).numChoices) {
                $(raceControl).addClass('completed').removeClass('in-progress');
            }
            else {
                $(raceControl).addClass('in-progress').removeClass('completed');
            }

            REFERENDA.BOOTH.BALLOT.answers[raceSlug].length = 0;
            for (var i = 0; i < answers.length; i++) {
                REFERENDA.BOOTH.BALLOT.answers[raceSlug][i] = answers[i];
            }
        }
        // update all races
        else {
            for (var race in REFERENDA.BOOTH.SESSION.election.eligibleRaces) {
                REFERENDA.BOOTH.CONTROL.updateBallot(REFERENDA.BOOTH.SESSION.election.eligibleRaces[race]);
            }
        }

        // update final ballot choices
        var finalBallotPane = $(this.container).find('#final_ballot');
        finalBallotPane.empty();

        for (var race in REFERENDA.BOOTH.BALLOT.answers) {
            var answers = REFERENDA.BOOTH.BALLOT.answers[race];
            var answerString = '';

            for (var answer in answers) {
                if (answerString == '') answerString = answers[answer];
                else answerString = answerString + ', ' + answers[answer];
            }

            finalBallotPane.append('<p><strong>' + REFERENDA.BOOTH.SESSION.election.raceMap[race].name + '</strong>: ' + answerString);
        }
    }
});

/* 
 * Initializes the voting booth and assigns it an element to use for its
 * presentation
 */
REFERENDA.BOOTH.setup = function(element) {
    //FIXME sets up as REFERENDA.BOOTH.CONTROL
    REFERENDA.BOOTH.CONTROL = new REFERENDA.BOOTH.Controller(element);
    REFERENDA.BOOTH.CONTROL.displayLogin();
};
