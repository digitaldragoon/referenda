/* The super-namespace */
REFERENDA = {};

/* An object which keeps track of a race */
REFERENDA.Race = Class.extend({
    init: function(data) {
        this.name = data.fields['name'];
        this.slug = data.fields['slug'];
        this.numChoices = data.fields['num_choices'];
    }
});

REFERENDA.Template = Class.extend({
    init: function(template_path) {
        this.content = $('<div></div>');
        this.content.setTemplateURL('templates/' + template_path + '/', undefined, {filter_data: false});
    },
        
    getContents: function() {
        return $(this.content.html());
    },

    processTemplate: function(data) {
        this.content.processTemplate(data);
    }
});

/* An object which keeps track of an election */
REFERENDA.Election = Class.extend({
    init: function(data) {
        this.races = [];
        this.raceMap = {};  // maps slugs to objects
        for (var race in data['races']) {
            race = data['races'][race];
            var racesLength = this.races.length;
            this.races[racesLength] = new REFERENDA.Race(race);
            this.raceMap[race.fields['slug']] = this.races[racesLength];
        }

        this.eligibleRaces = [];
        for (var race in data['eligibleRaces']) {
            race = data['eligibleRaces'][race];
            this.eligibleRaces[this.eligibleRaces.length] = race.fields['slug'];
        }

        this.pk = ElGamal.PublicKey.fromJSONObject($.evalJSON(data['pk']));
    },

    getRace: function(slug) {
        return this.raceMap[slug];
    }
});

/* Library methods */

/* Create a wait message - designed to be used with a spinning "busy" icon*/
REFERENDA.createWaitMessage = function(message) {
        var wait = $(document.createElement('p')).addClass('wait').text(message);
        wait.done = function(appendMessage) {
            this.removeClass('wait');
            if (appendMessage != undefined) {
                this.text(this.text() + appendMessage);
            }
        }

        return wait;
};
