REFERENDA.TRUSTEE = {};

REFERENDA.TRUSTEE.Session = Class.extend({
    generateKeypair: function() {
        var elgamalParams = ElGamal.Params.fromJSONObject(REFERENDA_ELGAMAL_JSON_PARAMS);

        try {
            var secretKey = elgamalParams.generate();
        } catch (e) {
            REFERENDA.TRUSTEE.CONTROL.displayMessage(e);
        }

        $(REFERENDA.TRUSTEE.CONTROL.container).find('#enc_public_key').val($.toJSON(secretKey.pk));
        $(REFERENDA.TRUSTEE.CONTROL.container).find('#enc_secret_key').val($.toJSON(secretKey));
    }
});

REFERENDA.TRUSTEE.Controller = Class.extend({
    init: function(element) {
        this.isLoggedIn = false;
        this.container = element;
        this.currentPane = 'nav-pane';
        this.TEMPLATES = {};

        this.TEMPLATES.LOGIN_FRAME = new REFERENDA.Template('login_frame');
        this.TEMPLATES.MESSAGE_ALERT = new REFERENDA.Template('message_alert');
        this.TEMPLATES.CONTROL_PANE = new REFERENDA.Template('control_pane');
    },

    /* Activates all controls on the trustee pane */
    activateControlPane: function() {
        $('#trustee-nav li.approve a').not('.disabled').click(function() {
                REFERENDA.TRUSTEE.CONTROL.navigateToPane('approve-pane');
            });

        $('#trustee-nav li.vote a').not('.disabled').click(function() {
                REFERENDA.TRUSTEE.CONTROL.navigateToPane('vote-pane');
            });

        $('#trustee-nav li.tally a').not('.disabled').click(function() {
                REFERENDA.TRUSTEE.CONTROL.navigateToPane('tally-pane');
            });

        $('.nav-link').click(function() {
                REFERENDA.TRUSTEE.CONTROL.navigateToNavPane();
            });

        $('#secretkey').keyup(function(e) {
                if (e.keyCode != 8 && e.keyCode != 46) {
                    try {
                        var key = ElGamal.SecretKey.fromJSONObject($.secureEvalJSON($('#secretkey').val()));
                    } catch (e) {
                        REFERENDA.TRUSTEE.CONTROL.displayMessage('The key you entered was not a valid secret key.');
                        return;
                    }

                    var tallybutton = $('<a class="button tally">Tally Now</a>');
                    tallybutton.click(function() {REFERENDA.TRUSTEE.CONTROL.tallyVotes();});
                    $('#secretkey').css('display', 'none');
                    $('#tally-pane .center').append(tallybutton);

                }
            });
    },

    /* Bring up a modal confirmation dialog */
    displayConfirmation: function(message, continueCallback, cancelCallback) {
        var template = REFERENDA.TRUSTEE.CONTROL.TEMPLATES.MESSAGE_CONFIRM;
        template.processTemplate({message: message});
        var messagePane = template.getContents();

        if (continueCallback != undefined)
            $(messagePane).find('.button.continue').click(continueCallback);

        if (cancelCallback != undefined)
            $(messagePane).find('.button.cancel').click(cancelCallback);

        $(messagePane).modal({close: false});
        messagePane.find('a.button.continue').focus();
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
                    REFERENDA.TRUSTEE.CONTROL.login(user_id, password);
                });
        

        // watermark fields
        contents.find('#login_user_id').watermark('username');
        contents.find('#login_password').watermark('password');

        $(this.container).html(contents);

        contents.find('#login_user_id').focus();
    },

    /* Bring up a modal alert message */
    displayMessage: function(message, callback) {
        var template = REFERENDA.TRUSTEE.CONTROL.TEMPLATES.MESSAGE_ALERT;
        template.processTemplate({message: message});
        var messagePane = template.getContents();

        if (callback != undefined) {
            $(messagePane).find('.simplemodal-close').click(callback);
        }

        $(messagePane).modal({close: false});
        messagePane.find('a.button.continue').focus();
    },

    loadControlPane: function() {
        var pane = REFERENDA.TRUSTEE.CONTROL.TEMPLATES.CONTROL_PANE;
        pane.processTemplate();
        pane = pane.getContents();

        $(this.container).html(pane);

        REFERENDA.TRUSTEE.CONTROL.activateControlPane();
    },

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
                        REFERENDA.TRUSTEE.CONTROL.races = data['races'];
                        REFERENDA.TRUSTEE.CONTROL.isLoggedIn = true;
                        REFERENDA.TRUSTEE.CONTROL.loadControlPane();
                    }
                    else if (data.status == 'invalid') {
                        waitMessage.remove();
                        REFERENDA.TRUSTEE.CONTROL.displayMessage(data.message);
                    }
                    else if (data.status == 'unavailable') {
                        waitMessage.remove();
                        REFERENDA.TRUSTEE.CONTROL.displayMessage(data.message);
                    }
                    else if (data.status == 'forbidden') {
                        waitMessage.remove();
                        REFERENDA.TRUSTEE.CONTROL.displayMessage(data.message,
                            function() {
                                window.location = '..';
                            });
                    }
                    else if (data.status == 'duplicate') {
                        waitMessage.remove();
                        REFERENDA.TRUSTEE.CONTROL.displayMessage(data.message,
                            function() {
                                window.location = '..';
                            });
                    }
                },
                // something's broken - display an error
                error: function (data) {
                    REFERENDA.TRUSTEE.CONTROL.displayMessage('The server encountered an error while attempting to log you in. Please try again in a few moments. If the problem persists, <a href="..">contact the administrator</a>.');
                    $('#login_frame .wait').remove();
                }
           });
        }
    },

    navigateToPane: function(pane_id) {
        //$('#' + this.currentPane).css('display', 'none');    
        //$('#' + pane_id).css('display', 'block');
        $('#' + this.currentPane).slideLeftHide();
        $(document).oneTime(200, undefined, function() {$('#' + pane_id).slideRightShow() });
        this.currentPane = pane_id;
    },

    navigateToNavPane: function() {
        $('#' + this.currentPane).slideRightHide();
        $(document).oneTime(200, undefined, function() {$('#nav-pane').slideLeftShow();});
        this.currentPane = 'nav-pane';
    },

    tallyVotes: function() {
        var wait = REFERENDA.createWaitMessage('Decrypting votes...');

        var sk = ElGamal.SecretKey.fromJSONObject($.secureEvalJSON($('#secretkey').val()));
        
        $('#tally-pane .button.tally').remove();
        $('#tally-pane .center').append(wait);

        var DATA = {};

        // get votes
        $.getJSON('../bulletinboard.json',
                function(data) {
                    // calculate workload
                    var numTicks = 0;
                    for (race in data) {
                        for (ballot in data[race]) {
                            var realBallot = $.secureEvalJSON(data[race][ballot][1].replace(/u?\'/g,'"'));
                            numTicks += realBallot['answers'].length + 1;
                        }
                    }

                    var progress = REFERENDA.createProgressBar(numTicks);
                    $('#tally-pane .center').append(progress);

                    for (race in data) {
                        DATA[race] = new Array();

                        for (ballot in data[race]) {
                            var decryptedBallot = {};
                            decryptedBallot['answers'] = new Array();

                            var jsonBallot = $.secureEvalJSON(data[race][ballot][1].replace(/u?\'/g,'"'));
                                
                            // decrypt receipt
                            var receiptCiphertext = ElGamal.Ciphertext.fromJSONObject(jsonBallot['receipt'], sk.pk)
                            var decryptionFactor = [sk.decryptionFactor(receiptCiphertext)];
                            decryptedBallot['receipt'] = receiptCiphertext.decrypt(decryptionFactor).getM();

                            progress.tick()


                            for (answer in jsonBallot['answers']) {
                                var ciphertext = ElGamal.Ciphertext.fromJSONObject(jsonBallot['answers'][answer], sk.pk);
                                var factors = [sk.decryptionFactor(ciphertext)];
                                var plaintext = ciphertext.decrypt(factors);

                                decryptedBallot['answers'][decryptedBallot['answers'].length] = plaintext.getM();

                                progress.tick();

                            }

                            DATA[race][DATA[race].length] = decryptedBallot;
                        }
                    }
    
                    wait.done('done!');
                    REFERENDA.TRUSTEE.CONTROL.submitVotes(DATA);
                });


    },

    submitVotes: function(data) {
        request_data = {data: $.toJSON(data)};

        $.ajax({
                type: 'POST',
                url: './submit/',
                data: request_data,
                dataType: 'json',
                success: function(data) {
                    REFERENDA.TRUSTEE.CONTROL.displayMessage(data);
                },
                error: function(data) {
                    REFERENDA.TRUSTEE.CONTROL.displayMessage('error!');
                }
            });
    }

});


/* 
 * Initializes the voting booth and assigns it an element to use for its
 * presentation
 */
REFERENDA.TRUSTEE.setup = function(element) {
    //sets up as REFERENDA.TRUSTEE.CONTROL
    REFERENDA.TRUSTEE.CONTROL = new REFERENDA.TRUSTEE.Controller(element);
    REFERENDA.TRUSTEE.CONTROL.displayLogin();
};
