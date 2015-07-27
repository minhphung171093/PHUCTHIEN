openerp.web_search_range_date = function (instance) {
	var QWeb = instance.web.qweb;
	_t = instance.web._t;
	instance.web.SearchView.include({
        start: function() {
            var result = this._super();
            var self = this;
            self.search_on = "name";
            self.fields_selection = [];
            var filter_array = [];
            if (self.dataset!=null && self.dataset.context.search_by_field_date){
            	filter_array = self.dataset.context.search_by_field_date;
            }
            this.dataset.call('fields_get', [false, {}]).done(function (fields) {
                $.each(fields, function (value) {
                    if((fields[value].type == "datetime" || fields[value].type == "date") && filter_array.indexOf(value)>= 0){
//                    	
                        fields[value].name = value;
                    	self.fields_selection.push(fields[value]);
                    }
                })
                if(self.fields_selection.length){
                    $('.field_selection_column').append((QWeb.render('field-selection', {widget: self})));
                    $(".search_from_date").change(function(){
                        var to_date = $(".search_to_date").val()
                        console.log('to date: ' + to_date)
                        console.log('from date: ' + $(this).val());
                        if (to_date) {
                            self.to_date =  to_date;
                            self.from_date =  $(this).val();
                            self.field_name_selection = $('#field_name_selection').val()
                            self.do_search();
                        }

                    })
                    $(".search_to_date").change(function(){
                        var from_date = $(".search_from_date").val()
                        console.log('from date: ' + from_date)
                        console.log('to date: ' + $(this).val());
                        if (from_date) {
                            self.from_date =  from_date;
                            self.to_date =  $(this).val();
                            self.field_name_selection = $('#field_name_selection').val()
                            $(this).toggleClass('enabled');
                            self.do_search();
                        }
                    })
                    $(".clear_filter").click(function () {
                        self.from_date =  "01/01/2000";
                        self.to_date =  "01/01/2020";
                        $(this).toggleClass('enabled');
                        self.do_search();

                    });
                    $('#field_name_selection').change(function () {
                        self.field_name_selection = $('#field_name_selection').val();
                        var to_date = $(".search_to_date").val()
                        var from_date = $(".search_from_date").val()
                        if (to_date && from_date) {
                            self.from_date =  from_date;
                            self.to_date =  to_date;
                            $('.to_date').toggleClass('.enabled');
                            self.do_search();
                        }
                    })
                }else{
                	$('.search_filter').live().hide();
                }
            });
            return result;
        },
        
        search_filter: function(){
            var filter_domain = [];
            var self = this;

            if (self.from_date && self.to_date && self.field_name_selection) {
                //filter_domain.push("[('" + self.field_name_selection +"'" + "',>=, '" + self.from_date + "),"+ "(" +self.field_name_selection+ ',<=,' + self.to_date + ")" + "]")
                filter_domain.push("[('" + self.field_name_selection + "', '>=', '" + self.from_date + "'),"+"('" + self.field_name_selection + "', '<=', '" + self.to_date + "')]")

            }

            if (filter_domain.length) {
                var filter_or_domain = [];
                for (i = 0; i < filter_domain.length-1; i++) {
                    filter_or_domain.push("['|']");
                }
                return filter_or_domain.concat(filter_domain || []);
            }
            return false;
        },
        build_search_data: function () {
            var result = this._super();
            var filter_domain = this.search_filter();
            if (filter_domain)
                result['domains'] = filter_domain.concat(result.domains || []);
            return result;
        },
        do_search: function (_query, options) {
        	return this._super();
        },
    });
	
    instance.web.ViewManager.include({
        switch_mode: function(view_type, no_store, view_options) {
            var view = this.views[view_type];
            var self = this;
            var result = this._super(view_type, no_store, view_options);
            if (this.searchview && this.active_view != "form") {
            	var filter_array = [];
            	if (self.action!=null && self.action.context.search_by_field_date){
                	filter_array = self.action.context.search_by_field_date;
                }
                if ((view.controller.searchable === false || this.searchview.options.hidden)  || this.active_view == "form" || filter_array.length<=0){
                    $('.search_filter').live().hide();
                }else
                    $('.search_filter').show();
            }
            else{
                $('.search_filter').live().hide();
            }
            return result;
        },
    });
    instance.web.FormView.include({
        load_defaults: function () {
            if($('.search_filter'))
                $('.search_filter').hide();
            return this._super();
        },
    });
};

// vim:et fdc=0 fdl=0 foldnestmax=3 fdm=syntax:
