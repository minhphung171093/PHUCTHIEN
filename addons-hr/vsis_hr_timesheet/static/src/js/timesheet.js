
openerp.gs_mkp_timesheet = function(instance) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

    instance.gs_mkp_timesheet.GSWeeklyTimesheet = instance.web.form.FormWidget.extend(instance.web.form.ReinitializeWidgetMixin, {
        events: {
            //"click .oe_timesheet_weekly_employee a": "go_to_employee",
        },
        init: function() {
            this._super.apply(this, arguments);
            this.set({
                sheets: [],
                date_to: false,
                date_from: false,
                department_id: false,
                time_normal_id: false,
                rate_normal_id: false,
                time_ot_id: false,
                rate_ot_id: false,
                default_wk_time: 8,
            });
            this.visible_status = {};
            this.status_all = {};
            this.status_2ids = {};
            this.updating = false;
            this.get_default_data();
            this.field_manager.on("field_changed:timesheet_ids", this, this.query_sheets);
            this.field_manager.on("field_changed:date_from", this, function() {
                this.set({"date_from": instance.web.str_to_date(this.field_manager.get_field_value("date_from"))});
            });
            this.field_manager.on("field_changed:date_to", this, function() {
                this.set({"date_to": instance.web.str_to_date(this.field_manager.get_field_value("date_to"))});
            });
            this.field_manager.on("field_changed:user_id", this, function() {
                this.set({"user_id": this.field_manager.get_field_value("user_id")});
            });
            this.field_manager.on("field_changed:department_id", this, function() {
                this.set({"department_id": this.field_manager.get_field_value("department_id")});
            });
            this.on("change:sheets", this, this.update_sheets);
            this.res_o2m_drop = new instance.web.DropMisordered();
            this.render_drop = new instance.web.DropMisordered();
            this.description_line = _t("/");
            this.view.on("gs_pre_save", this, this.gs_pre_save_parent);
        },
        go_to_employee: function(event) {
            var id = JSON.parse($(event.target).data("id"));
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "hr.employee",
                res_id: id,
                views: [[false, 'form']],
                target: 'current'
            });
        },
        get_default_data: function() {
            var self = this;
            new instance.web.Model(this.view.model).call("get_default_analytic_account", ["TIME_NORMAL",
                    new instance.web.CompoundContext()]).then(function(result) {
                if (result) {
                    self.set({rate_normal_id: result[0]});
                    if (result[1]){
                        self.set({time_normal_id: result[1]});
                    }
                }
            });
            new instance.web.Model(this.view.model).call("get_default_analytic_account", ["TIME_OT150",
                    new instance.web.CompoundContext()]).then(function(result) {
                if (result) {
                    self.set({rate_ot_id: result[0]});
                    if (result[1]){
                        self.set({time_ot_id: result[1]});
                    }
                }
            });
            new instance.web.Model("gs.hr.timesheet.status").call("search", [[]],
                    {context: this.build_context()}).then(function(ids) {
                new instance.web.Model("gs.hr.timesheet.status").call("name_get", [ids,
                        new instance.web.CompoundContext()]).then(function(result) {
                    _.each(result, function(el) {
                        self.status_all[el[0]] = el[1];
                        self.status_2ids[el[1]] = el[0];
                    });
                });
            });
        },
        gs_pre_save_parent: function() {
            var self = this;
            if (self.timesheet_changed)
                self.sync();
        },
        query_sheets: function() {
            var self = this;
            if (self.updating)
                return;
            var commands = this.field_manager.get_field_value("timesheet_ids");
            if (commands.length <= 0)
                return;
            this.res_o2m_drop.add(new instance.web.Model(this.view.model).call("resolve_2many_commands", ["timesheet_ids", commands, [],
                    new instance.web.CompoundContext()]))
                .done(function(result) {
                self.querying = true;
                self.set({sheets: result});
                self.querying = false;
            });
        },
        update_sheets: function() {
            var self = this;
            if (self.querying)
                return;
            self.updating = true;
            self.field_manager.set_values({timesheet_ids: self.get("sheets")}).done(function() {
                self.updating = false;
            });
        },
        initialize_field: function() {
            instance.web.form.ReinitializeWidgetMixin.initialize_field.call(this);
            var self = this;
            self.on("change:sheets", self, self.gs_initialize_content);
            self.on("change:date_to", self, self.gs_initialize_content);
            self.on("change:date_from", self, self.gs_initialize_content);
            //self.on("change:user_id", self, self.gs_initialize_content);
            self.on("change:department_id", self, self.gs_initialize_content);
        },
        reinitialize: function() {
            instance.web.form.ReinitializeWidgetMixin.reinitialize.call(this);
            this.gs_initialize_content();
        },
        gs_initialize_content: function() {
            var self = this;
            if (self.setting)
                return;
            // don't render anything until we have date_to and date_from
            if (!self.get("date_to") || !self.get("date_from") || !self.get('department_id') || !self.get('time_normal_id'))
                return;
            this.destroy_content();

            // it's important to use those vars to avoid race conditions
            var dates;
            var employees;
            var employee_ids;
            var saved_employees;
            var employee_names;
            var default_get;

            var ismanager = true;
            new instance.web.Model("hr.department").call("read", [self.get('department_id'),['name','member_ids','manager_id'],
                new instance.web.CompoundContext({'user_id': self.get('user_id')})]).then(function(result) {
                /* Check login user is manager, but you should check one time when open timesheet
                if (!result['manager_id']){
                    ismanager = false;
                    return;
                }
                if (typeof(result['manager_id']) === "object")
                    result['manager_id'] = result['manager_id'][0];
                new instance.web.Model("hr.employee").call("read", [result['manager_id'],['user_id']]).then(function(emps) {
                    if (typeof(emps['user_id']) === "object")
                        emps['user_id'] = emps['user_id'][0];
                    if (emps['user_id'] !== self.get('user_id')){
                        ismanager = false;
                        return;
                    }
                }); */
                employee_ids = result['member_ids'];
                new instance.web.Model("hr.employee").call("name_get", [result['member_ids'],
                    new instance.web.CompoundContext()]).then(function(result) {
                        employee_names = {};
                        _.each(result, function(el) {
                            employee_names[el[0]] = el[1];
                        });
                    });
                });
            if (!ismanager)
                return;
            return this.render_drop.add(new instance.web.Model("hr.analytic.timesheet").call("default_get", [
                ['account_id','general_account_id', 'employee_id', 'journal_id','date','name','user_id','product_id','product_uom_id','to_invoice','amount','unit_amount','timesheet_status'],
                new instance.web.CompoundContext({'user_id': self.get('user_id')})]).then(function(result) {
                default_get = result;
                // calculating dates
                dates = [];
                var start = self.get("date_from");
                var end = self.get("date_to");
                while (start <= end) {
                    dates.push(start);
                    start = start.clone().addDays(1);
                }

                saved_employees = _(self.get("sheets")).chain().map(function(el) {
                    // much simpler to use only the id in all cases
                    if (typeof(el.account_id) === "object")
                        el.account_id = el.account_id[0];
                    if (typeof(el.user_id) === "object")
                        el.user_id = el.user_id[0];
                    if (typeof(el.timesheet_status) === "object")
                        el.timesheet_status = el.timesheet_status[0];
                    if (typeof(el.employee_id) === "object")
                        el.employee_id = el.employee_id[0];
                    employee_ids = _.without(employee_ids, el.employee_id)
                    return el;
                })
                .groupBy("employee_id").value();

                return new instance.web.Model("hr.analytic.timesheet").call("on_change_account_id", [[], self.get("time_normal_id")]).then(function(res) {
                    employee_defaults = _.extend({}, default_get, res.value);
                    employees = _(saved_employees).chain().map(function(lines, emp_id) {
                        emp_id = emp_id === "false" ? false :  Number(emp_id);
                        var index = _.groupBy(lines, "date");
                        var days = _.map(dates, function(date) {
                            var acc_groups = _.groupBy(index[instance.web.date_to_str(date)], "account_id");
                            var day = {day: date, account: self.get("time_normal_id"), lines: acc_groups[self.get("time_normal_id")] || []};
                            if (day.lines.length === 0) {
                                day.lines.unshift(_.extend(_.clone(employee_defaults), {
                                    name: self.description_line,
                                    unit_amount: 0,
                                    date: instance.web.date_to_str(date),
                                    employee_id: emp_id,
                                    to_invoice: self.get("rate_normal_id"),
                                    account_id: self.get("time_normal_id"),
                                    timesheet_status: false,
                                }));
                            }
                            day.main_status = day.lines[0].timesheet_status ? self.status_all[day.lines[0].timesheet_status] : false;

                            var day_ot = {day: date, account: self.get("time_ot_id"), lines: acc_groups[self.get("time_ot_id")] || []};
                            if (day_ot.lines.length === 0) {
                                day_ot.lines.unshift(_.extend(_.clone(employee_defaults), {
                                    name: self.description_line,
                                    unit_amount: 0,
                                    date: instance.web.date_to_str(date),
                                    employee_id: emp_id,
                                    to_invoice: self.get("rate_ot_id"),
                                    account_id: self.get("time_ot_id"),
                                    timesheet_status: false,
                                }));
                            }
                            day_ot.main_status = day_ot.lines[0].timesheet_status ? self.status_all[day_ot.lines[0].timesheet_status] : false;
                            day.ot = day_ot;
                            return day;
                        });
                        return {employee: emp_id, days: days, employee_defaults: employee_defaults};
                    }).value();

                    new_employees = _(employee_ids).chain().map(function(el) {
                        var days = _.map(dates, function(date) {
                            var day = {day: date, account: self.get("time_normal_id"), lines: []};
                            day.lines.unshift(_.extend(_.clone(employee_defaults), {
                                    name: self.description_line,
                                    unit_amount: 0,
                                    date: instance.web.date_to_str(date),
                                    employee_id: el,
                                    to_invoice: self.get("rate_normal_id"),
                                    account_id: self.get("time_normal_id"),
                                    timesheet_status: false,
                                }));
                            day.main_status = false;

                            var day_ot = {day: date, account: self.get("time_ot_id"), lines: []};
                            day_ot.lines.unshift(_.extend(_.clone(employee_defaults), {
                                    name: self.description_line,
                                    unit_amount: 0,
                                    date: instance.web.date_to_str(date),
                                    employee_id: el,
                                    to_invoice: self.get("rate_ot_id"),
                                    account_id: self.get("time_ot_id"),
                                    timesheet_status: false,
                                }));
                            day_ot.main_status = false;
                            day.ot = day_ot;
                            return day;
                        });
                        return {employee: el, days: days, employee_defaults: employee_defaults};
                    }).value();
                    employees = employees.concat(new_employees);
                });

            })).then(function(result) {
                // we put all the gathered data in self, then we render
                self.dates = dates;
                self.default_get = default_get;
                self.employees = employees;
                self.employee_names = employee_names;
                //real rendering
                self.display_data();
                self.register_filter_event();
            });
        },
        destroy_content: function() {
            if (this.dfm) {
                this.dfm.destroy();
                this.dfm = undefined;
            }
        },
        register_filter_event: function() {
            var self = this;
            // date filter
            _.each(self.dates, function(date) {
                //self.visible_status[date] = 'ALL';
                self.get_select_date(date).change(function() {
                    //console.debug(date.toString('yyMMdd') + " changed");
                    self.visible_status[date] = $('#oe-timesheet-date-filter-' + date.toString('yyMMdd') + ' option:selected').val();
                    //console.debug(self.visible_status[date]);
                    self.display_data();
                    self.register_filter_event();
                });
            });
        },
        display_data: function() {
            var self = this;
            self.timesheet_changed = false;
            self.$el.html(QWeb.render("gs_mkp_timesheet.GSWeeklyTimesheet", {widget: self}));
            _.each(self.employees, function(employee) {
                _.each(_.range(employee.days.length), function(day_count) {
                    var sum_day_box = self.sum_box_emp(employee, day_count);
                    var is_default_wk = (sum_day_box === self.get('default_wk_time'));
                    var curr_status = (is_default_wk ? "X" : self.get_display_box_emp(employee, day_count));
                    var curr_value = (is_default_wk ? "X" : sum_day_box);
                    if (curr_status === 'V')
                        curr_value = 'V';
                    if (!self.get('effective_readonly')) {
                        self.get_box_emp(employee, day_count).val(curr_value).change(function() {
                            var in_char = $(this).val().toUpperCase();
                            var num;
                            var override_status = employee.days[day_count].lines[0].timesheet_status;
                            if (in_char === 'X') {
                                num = self.get('default_wk_time');
                            } else if (in_char === 'V'){
                                num = 0;
                                override_status = self.status_2ids['V'];
                            } else {
                                num = Number(in_char);
                            }

                            if (isNaN(num)) {
                                $(this).val(sum_day_box);
                            } else {
                                if (num === self.get('default_wk_time'))
                                    override_status = self.status_2ids['X'];
                                employee.days[day_count].lines[0].unit_amount = num;
                                employee.days[day_count].lines[0].timesheet_status = override_status;
                                self.display_totals();
                                //self.sync();
                            }
                            if (!self.timesheet_changed)
                                self.timesheet_changed = true;
                        });
                        self.get_box_emp_ot(employee, day_count).val(self.sum_box_emp_ot(employee, day_count)).change(function() {
                            var num = Number($(this).val());
                            if (isNaN(num)) {
                                $(this).val(self.sum_box_emp_ot(employee, day_count));
                            } else {
                                employee.days[day_count].ot.lines[0].unit_amount += num - self.sum_box_emp_ot(employee, day_count);
                                self.display_totals();
                                //self.sync();
                            }
                            if (!self.timesheet_changed)
                                self.timesheet_changed = true;
                        });
                    } else {
                        self.get_box_emp(employee, day_count).html(curr_status);
                        self.get_box_emp_ot(employee, day_count).html(self.ts_format(self.sum_box_emp_ot(employee, day_count)));
                    }
                    if (self.visible_status[employee.days[day_count].day])
                        if ((self.visible_status[employee.days[day_count].day] !== 'ALL') &&
                            (curr_status !== self.visible_status[employee.days[day_count].day])) {
                            self.get_row_emp(employee.employee).hide();
                            //console.debug('hided employee=' + employee.employee + '@day='+ employee.days[day_count].day + '@value=' + curr_status);
                        }
                });
            });
            self.display_totals();
        },
        get_select_date: function(date) {
            return this.$('#oe-timesheet-date-filter-' + date.toString('yyMMdd'));
        },
        get_row_emp: function(employee_id) {
            return this.$('#oe-timesheet-employee-row-' + employee_id);
        },
        get_box_emp: function(employee, day_count) {
            return this.$('[data-employee="' + employee.employee + '"][data-account="' + this.get("time_normal_id") + '"][data-day-count="' + day_count + '"]');
        },
        get_box_emp_ot: function(employee, day_count) {
            return this.$('[data-employee-ot="' + employee.employee + '"][data-account-ot="' + this.get("time_ot_id") + '"][data-day-count-ot="' + day_count + '"]');
        },
        get_total_emp: function(employee) {
            return this.$('[data-employee-total="' + employee.employee + '"]');
        },
        get_total_emp_ot: function(employee) {
            return this.$('[data-employee-total-ot="' + employee.employee + '"]');
        },
        get_day_total: function(day_count) {
            return this.$('[data-day-total="' + day_count + '"]');
        },
        get_day_total_ot: function(day_count) {
            return this.$('[data-day-total-ot="' + day_count + '"]');
        },
        get_super_total: function() {
            return this.$('.oe_timesheet_weekly_supertotal');
        },
        get_super_total_ot: function() {
            return this.$('.oe_timesheet_weekly_supertotal_ot');
        },
        sum_box_emp: function(employee, day_count) {
            var line_total = 0;
            _.each(employee.days[day_count].lines, function(line) {
                line_total += line.unit_amount;
            });
            return line_total;
        },
        sum_box_emp_ot: function(employee, day_count) {
            var line_total = 0;
            _.each(employee.days[day_count].ot.lines, function(line) {
                line_total += line.unit_amount;
            });
            return line_total;
        },
        get_display_box_emp: function(employee, day_count) {
            var self = this;
            if (employee.days[day_count].main_status) {
                return employee.days[day_count].main_status;
            } else {
                var line_total = 0;
                _.each(employee.days[day_count].lines, function(line) {
                    line_total += line.unit_amount;
                });
                return self.ts_format(line_total);
            }
        },
        display_totals: function() {
            var self = this;
            var day_tots = _.map(_.range(self.dates.length), function() { return 0 });
            var day_tots_ot = _.map(_.range(self.dates.length), function() { return 0 });
            var super_tot = 0;
            var super_tot_ot = 0;
            _.each(self.employees, function(employee) {
                var acc_tot = 0;
                var acc_tot_ot = 0;
                _.each(_.range(self.dates.length), function(day_count) {
                    var sum = self.sum_box_emp(employee, day_count);
                    var sum_ot = self.sum_box_emp_ot(employee, day_count);
                    acc_tot += sum;
                    acc_tot_ot += sum_ot;
                    day_tots[day_count] += sum;
                    day_tots_ot[day_count] += sum_ot;
                    super_tot += sum;
                    super_tot_ot += sum_ot;
                });
                self.get_total_emp(employee).html(self.ts_format(acc_tot));
                self.get_total_emp_ot(employee).html(self.ts_format(acc_tot_ot));
            });
            _.each(_.range(self.dates.length), function(day_count) {
                self.get_day_total(day_count).html(self.ts_format(day_tots[day_count]));
                self.get_day_total_ot(day_count).html(self.ts_format(day_tots_ot[day_count]));
            });
            self.get_super_total().html(self.ts_format(super_tot));
            self.get_super_total_ot().html(self.ts_format(super_tot_ot));
        },
        sync: function() {
            //console.debug('syncing..');
            var self = this;
            self.setting = true;
            self.set({sheets: this.generate_o2m_value()});
            self.setting = false;
        },
        ts_format: function(f_value) {
            if (f_value=== 0)
                return 0
            else
                return instance.web.format_value(f_value, {"type": 'float_time'})
        },
        generate_o2m_value: function() {
            var self = this;
            var ops = [];

            _.each(self.employees, function(employee) {
                var auth_keys = _.extend(_.clone(employee.employee_defaults), {
                    name: true, unit_amount: true, date: true, account_id:true, employee_id:true, to_invoice:true, timesheet_status:true,
                });
                _.each(employee.days, function(day) {
                    _.each(day.lines, function(line) {
                        if ((line.unit_amount !== 0) || line.timesheet_status) {
                            var tmp = _.clone(line);
                            tmp.id = undefined;
                            _.each(line, function(v, k) {
                                if (v instanceof Array) {
                                    tmp[k] = v[0];
                                }
                            });
                            _.each(_.keys(tmp), function(key) {
                                if (auth_keys[key] === undefined) {
                                    tmp[key] = undefined;
                                }
                            });
                            ops.push(tmp);
                        }
                    });
                    _.each(day.ot.lines, function(line) {
                        if (line.unit_amount !== 0) {
                            var tmp = _.clone(line);
                            tmp.id = undefined;
                            _.each(line, function(v, k) {
                                if (v instanceof Array) {
                                    tmp[k] = v[0];
                                }
                            });
                            _.each(_.keys(tmp), function(key) {
                                if (auth_keys[key] === undefined) {
                                    tmp[key] = undefined;
                                }
                            });
                            ops.push(tmp);
                        }
                    });
                });
            });

            return ops;
        },
    });

    instance.web.form.custom_widgets.add('gs_weekly_timesheet', 'instance.gs_mkp_timesheet.GSWeeklyTimesheet');

    // TODO: we can not sync each time has a change on timesheet, so we sync before saving
    // Here is a trick to override on_button_save function of formview object to trigger gs_pre_save event before do the save
    instance.web.FormView.include({
        on_button_save: function () {
            this.trigger("gs_pre_save");
            return this._super();
        },
    })
};
