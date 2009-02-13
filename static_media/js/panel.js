/* Slide panel in and out */
$(document).ready(function() {
        var panel = $('#advanced-panel');
        panel.data('state', 'closed');

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
});
