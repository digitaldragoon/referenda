(function($){
	$.extend($.fn, {
		slideLeftShow: function(speed,callback){
			return this.animate({width: "show"}, speed, callback);
		},
		slideLeftHide: function(speed,callback){
			return this.animate({width: "hide"}, speed, callback);
		},
		slideLeftToggle: function(speed,callback){
			return this.animate({width: "toggle"}, speed, callback);
		},
		slideRightShow: function(speed,callback){
			return this.animate({width:"show"},{
				step: function(now, data){
					var w = Math.ceil(now);
					if(typeof(data.origLeft) == 'undefined'){
						var position = $(this).css('position');
						if(position=='static')
						{
							$(this).css('position','relative');
						}
						data.origPos = position;
						data.origLeft = data.end+parseInt($(this).css('left'))||0;
					}
					$(this).css({left:data.origLeft-(data.start+w)});
					if(w==data.end)$(this).css('position',data.origPos);
				},
				duration: speed,
				complete: callback
			});
		},
		slideRightHide: function(speed,callback){
			return this.animate({width:"hide"},{
				step: function(now, data){
					var w = Math.ceil(now);
					if(typeof(data.origLeft) == 'undefined')
					{
						var position = $(this).css('position');
						if(position=='static')
						{
							$(this).css('position','relative');
						}
						data.origPos = position;
						data.origLeft = parseInt($(this).css('left'))||0;
					}
					$(this).css({left:data.origLeft+(data.start-w)});
					if(w==0)$(this).css({left:data.origLeft, position:data.origPos});
				},
				duration: speed,
				complete: callback
			});
		},
		slideRightToggle: function(speed,callback){
			return this.animate({width:"toggle"},{
				step: function(now, data){
					var w = Math.ceil(now);
					if(typeof(data.origLeft) == 'undefined'){
						var position = $(this).css('position');
						if(position=='static')
						{
							$(this).css('position','relative');
						}
						data.origPos = position;
						data.origLeft = data.end+parseInt($(this).css('left'))||0;
					}
					if(data.start == 0)
					{
						if(w==data.end)$(this).css('position',data.origPos);
						$(this).css({left:data.origLeft-(data.start+w)});
					}else{
						$(this).css({left:data.origLeft+(data.start-w)});
						if(w==0)$(this).css({left:data.origLeft, position:data.origPos});
					}
				},
				duration: speed,
				complete: callback
			});
		}
	});
})(jQuery);