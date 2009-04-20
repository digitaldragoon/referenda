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
