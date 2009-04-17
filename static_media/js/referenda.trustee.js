REFERENDA.TRUSTEE = {}

REFERENDA.TRUSTEE.Controller = Class.extend({
    init: function() {
        this.TEMPLATES = {};


    }
});



    generateKeypair: function() {
        var elgamalParams = ElGamal.Params.fromJSONObject(REFERENDA_ELGAMAL_JSON_PARAMS);

        try {
            var secretKey = elgamalParams.generate();
        } catch (e) {
            REFERENDA.BOOTH.CONTROL.displayMessage(e);
        }

        $(REFERENDA.BOOTH.CONTROL.container).find('#enc_public_key').val($.toJSON(secretKey.pk));
        $(REFERENDA.BOOTH.CONTROL.container).find('#enc_secret_key').val($.toJSON(secretKey));
    },
