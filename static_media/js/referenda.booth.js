REFERENDA.BOOTH = {};

/* Object which holds ballot information. */
REFERENDA.BOOTH.Ballot = Class.extend({
    /* Creates an empty ballot */
    init: function() {
        this.answers = [];
    },

    /* Computes the contents of this ballot from the booth data */
    computeFromBooth: function(booth) {
        //FIXME
    },

    /* Encrypts this ballot with the provided key */
    encryptWithKey: function(key) {
        //FIXME
    },

    /* Seals this ballot by dumping plaintext data from memory */
    seal: function() {
        //FIXME
    }
});

/*
 * Holds the session state.
 */
REFERENDA.BOOTH.Session = Class.extend({
    fromJSON: function(jsonString) {
        //FIXME
    },
});

/* The object which controls the voting booth (navigation, data gathering, etc.) */
REFERENDA.BOOTH.Controller = Class.extend({
    init: function(element) {
        this._element = element;
        this.TEMPLATES = {};

        // setup templats
        this.createTemplate('LOGIN_FRAME', 'templates/login_frame/');
    },

    /* Activates the nav links on the progress panel. */
    activate_nav_links: function() {
        control = this;

        $('#progress-frame').data('current', 'setup');

        /* Add navigation hook to each link */
        $('#progress-frame li a').each(function() {
                    $(this).closest('li').click(function() {
                        var id = $(this).closest('li').attr('id').split('_')[1];
                        control.navigate_to_panel(id);
                    });
                });

        /* "complete" setup tab */
        $('#progress_setup').removeClass('in-progress').addClass('completed');
    },
   
    /* Activate the selection and deselection of candidates. */
    activate_candidate_selection: function() {
        control = this;

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
    
    },

    /* Activate the "Cast Vote" buttons, which runs a check to see if the user has used up all of their votes, and then navigates to the next panel. */
    activate_cast_vote_buttons: function() {
        control = this;

        $('.race .button.castvote').click(function() {
            /* check to ensure all votes are accounted for */
            if (control.race_choices_left($(this).closest('div.race')) > 0){
                /* "continue" button */
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
    },

    createTemplate: function(name, template_path) {
        this.TEMPLATES[name] = $('<div></div>');
        this.TEMPLATES[name].setTemplateURL(template_path);
        this.TEMPLATES[name].getContents = function() {
                    return $(this.html());
                };
    },

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

        // watermark fields
        contents.find('#login_user_id').watermark('username');
        contents.find('#login_password').watermark('password');

        $(this._element).append(contents);

        contents.find('#login_user_id').focus();
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
