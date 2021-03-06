/**
    S3Filter Static JS Code
*/

S3.search = {};

// Module pattern to hide internal vars
(function () {

    /**
     * pendingTargets: targets which were invisible during last filter-submit
     */
    var pendingTargets = {};

    /**
     * quoteValue: add quotes to values which contain commas, escape quotes
     */
    var quoteValue = function(value) {
        if (value) {
            var result = value.replace(/\"/, '\\"');
            if (result.search(/\,/) != -1) {
                result = '"' + result + '"';
            }
            return result
        } else {
            return (value);
        }
    }

    /**
     * getCurrentFilters: retrieve all current filters
     */
    var getCurrentFilters = function(form) {

        form = typeof form !== 'undefined' ? form : $('body');

        var queries = [];

        // Text widgets
        form.find('.text-filter:visible').each(function() {

            var id = $(this).attr('id');

            var url_var = $('#' + id + '-data').val(),
                value = $(this).val();
            if (value) {
                var values = value.split(' '), v;
                for (var i=0; i < values.length; i++) {
                    v = '*' + values[i] + '*';
                    queries.push(url_var + '=' + quoteValue(v));
                }
            }
        });

        // Options widgets
        form.find('.ui-multiselect:visible').prev(
                  '.options-filter.multiselect-filter-widget,' +
                  '.options-filter.groupedopts-filter-widget')
        .add(
        form.find('.options-filter:visible,' +
                  '.options-filter.groupedopts-filter-widget.active,' +
                  '.options-filter.multiselect-filter-widget.active,' +
                  '.options-filter.multiselect-filter-bootstrap.active'))
        .each(function() {
            var id = $(this).attr('id');
            var url_var = $('#' + id + '-data').val();
            var operator = $("input:radio[name='" + id + "_filter']:checked").val();
            var contains = /__contains$/;
            var anyof = /__anyof$/;
            if (operator == 'any' && url_var.match(contains)) {
                url_var = url_var.replace(contains, '__anyof');
            } else if (operator == 'all' && url_var.match(anyof)) {
                url_var = url_var.replace(anyof, '__contains');
            }
            if (this.tagName.toLowerCase() == 'select') {
                // Standard SELECT
                value = '';
                values = $(this).val();
                if (values) {
                    for (i=0; i < values.length; i++) {
                        v = quoteValue(values[i]);
                        if (value === '') {
                            value = v;
                        } else {
                            value = value + ',' + v;
                        }
                    }
                }
            } else {
                // Checkboxes widget
                var value = '';
                $("input[name='" + id + "']:checked").each(function() {
                    if (value === '') {
                        value = quoteValue($(this).val());
                    } else {
                        value = value + ',' + quoteValue($(this).val());
                    }
                });
            }
            if (value !== '') {
                queries.push(url_var + '=' + value);
            }
        });

        // Numerical range widgets -- each widget has two inputs.
        form.find('.range-filter-input:visible').each(function() {
            var id = $(this).attr('id');
            var url_var = $('#' + id + '-data').val();
            var value = $(this).val();
            if (value) {
                queries.push(url_var + '=' + value);
            }
        });

        // Date(time) range widgets -- each widget has two inputs.
        form.find('.date-filter-input:visible').each(function() {
            var id = $(this).attr('id'), value = $(this).val();
            var url_var = $('#' + id + '-data').val(), dt, dtstr;
            var pad = function (val, len) {
                val = String(val);
                len = len || 2;
                while (val.length < len) val = "0" + val;
                return val;
            };
            var iso = function(dt) {
                return dt.getFullYear() + '-' +
                       pad(dt.getMonth()+1, 2) + '-' +
                       pad(dt.getDate(), 2) + 'T' +
                       pad(dt.getHours(), 2) + ':' +
                       pad(dt.getMinutes(), 2) + ':' +
                       pad(dt.getSeconds(), 2);
            };
            if (value) {
                if ($(this).hasClass('datetimepicker')) {
                    if ($(this).hasClass('hide-time')) {
                        dt = $(this).datepicker('getDate');
                        op = id.split('-').pop();
                        if (op == 'le' || op == 'gt') {
                            dt.setHours(23, 59, 59, 0);
                        } else {
                            dt.setHours(0, 0, 0, 0);
                        }
                    } else {
                        dt = $(this).datetimepicker('getDate');
                    }
                    dt_str = iso(dt);
                    queries.push(url_var + '=' + dt_str);
                } else {
                    dt = Date.parse(value);
                    if (isNaN(dt)) {
                        // Unsupported format (e.g. US MM-DD-YYYY), pass
                        // as string, and hope the server can parse this
                        dt_str = '"'+ value + '"';
                    } else {
                        dt_str = iso(new Date(dt));
                    }
                    queries.push(url_var + '=' + dt_str);
                }
            }
        });

        // Location widgets
        form.find('.ui-multiselect:visible').prev(
          '.location-filter.multiselect-filter-widget,' +
          '.location-filter.groupedopts-filter-widget')
        .add(
        form.find('.location-filter:visible,' +
          '.location-filter.multiselect-filter-widget.active,' +
          '.location-filter.multiselect-filter-bootstrap.active'))
        .each(function() {
            var id = $(this).attr('id');
            var url_var = $('#' + id + '-data').val();
            var operator = $("input:radio[name='" + id + "_filter']:checked").val();
            if (this.tagName.toLowerCase() == 'select') {
                // Standard SELECT
                value = '';
                values = $(this).val();
                if (values) {
                    for (i=0; i < values.length; i++) {
                        v = quoteValue(values[i]);
                        if (value === '') {
                            value = v;
                        } else {
                            value = value + ',' + v;
                        }
                    }
                }
            } else {
                // Checkboxes widget
                var value = '';
                $("input[name='" + id + "']:checked").each(function() {
                    if (value === '') {
                        value = quoteValue($(this).val());
                    } else {
                        value = value + ',' + quoteValue($(this).val());
                    }
                });
            }
            if (value !== '') {
                queries.push(url_var + '=' + value);
            }
        });

        // Other widgets go here...

        // return queries to caller
        return queries;
    };
    // Pass to global scope to be called by s3.jquery.ui.pivottable.js
    S3.search.getCurrentFilters = getCurrentFilters;

    /**
     * Update a variable in the query part of the filter-submit URL
     */
    var updateFilterSubmitURL = function(form, name, value) {
        
        var submit_url = $('#' + form).find('input.filter-submit-url[type="hidden"]');

        if (submit_url.length) {
            
            submit_url = submit_url.first();
            
            var url = $(submit_url).val();
            
            var url_parts = url.split('?'), update_url, query, vars=[];

            if (url_parts.length > 1) {
                
                var qstr = url_parts[1];
                var a = qstr.split('&'), b, c;
                for (i=0; i<a.length; i++) {
                    var b = a[i].split('=');
                    if (b.length > 1) {
                        c = decodeURIComponent(b[0]);
                        if (c != name) {
                            vars.push(b[0] + '=' + b[1]);
                        }
                    }
                }
                vars.push(name + '=' + value);
                
                query = vars.join('&');
                update_url = url_parts[0];
                if (query) {
                    update_url = update_url + '?' + query;
                }
            } else {
                update_url = url + '?' + name + '=' + value;
            }
            $(submit_url).val(update_url);
        }
    }

    /**
     * filterURL: add filters to a URL
     *
     * Note: this removes+replaces all existing filters in the URL query,
     *       but leaves other vars untouched
     */
    var filterURL = function(url, queries) {

        if (undefined === queries) {
            queries = getCurrentFilters();
        }
        // Construct the URL
        var url_parts = url.split('?'),
            url_query = queries.join('&');
        if (url_parts.length > 1) {
            var qstr = url_parts[1],
                query = {};
            var a = qstr.split('&'),
                b, v, i, len;
            for (i=0, len=a.length; i < len; i++) {
                b = a[i].split('=');
                if (b.length > 1 && b[0].search(/\./) == -1) {
                    query[decodeURIComponent(b[0])] = decodeURIComponent(b[1]);
                }
            }
            for (i=0, len=queries.length; i < len; i++) {
                v = queries[i].split('=');
                if (v.length > 1) {
                    query[v[0]] = v[1];
                }
            }
            var url_queries = [], url_query;
            for (v in query) {
                url_queries.push(v + '=' + query[v]);
            }
            url_query = url_queries.join('&');
        }
        var filtered_url = url_parts[0];
        if (url_query) {
            filtered_url = filtered_url + '?' + url_query;
        }
        return filtered_url;
    };
    // Pass to global scope to be called by S3.gis.refreshLayer()
    S3.search.filterURL = filterURL;

    /**
     * updateOptions: Update the options of all filter widgets
     */
    var updateOptions = function(options) {

        for (filter_id in options) {
            var widget = $('#' + filter_id);

            if (widget.length) {
                var newopts = options[filter_id];

                // OptionsFilter
                if ($(widget).hasClass('options-filter')) {
                    if ($(widget)[0].tagName.toLowerCase() == 'select') {
                        // Standard SELECT
                        var selected = $(widget).val(),
                            s=[], opts='', group, item, value, label, tooltip;

                        // Update HTML
                        if (newopts.hasOwnProperty('empty')) {

                            // @todo: implement

                        } else

                        if (newopts.hasOwnProperty('groups')) {
                            for (var i=0, len=newopts.groups.length; i < len; i++) {
                                group = newopts.groups[i];
                                if (group.label) {
                                    opts += '<optgroup label="' + group.label + '">';
                                }
                                for (var j=0, lenj=group.items.length; j < lenj; j++) {
                                    item = group.items[j];
                                    value = item[0].toString();
                                    if (selected && $.inArray(value, selected) >= 0) {
                                        s.push(value);
                                    }
                                    opts += '<option value="' + value + '"';
                                    tooltip = item[3];
                                    if (tooltip) {
                                        opts += ' title="' + tooltip + '"';
                                    }
                                    label = item[1];
                                    opts += '>' + label + '</option>';
                                }
                                if (group.label) {
                                    opts += '</optgroup>';
                                }
                            }

                        } else {
                            for (var i=0, len=newopts.length; i < len; i++) {
                                item = newopts[i];
                                value = item[0].toString();
                                label = item[1];
                                if (selected && $.inArray(value, selected) >= 0) {
                                    s.push(value);
                                }
                                opts += '<option value="' + value + '">' + label + '</option>';
                            }
                        }
                        $(widget).html(opts);

                        // Update SELECTed value
                        if (s) {
                            $(widget).val(s);
                        }

                        // Refresh UI widgets
                        if (widget.hasClass('groupedopts-filter-widget') && typeof widget.groupedopts != 'undefined') {
                            widget.groupedopts('refresh');
                        } else
                        if (widget.hasClass('multiselect-filter-widget') && typeof widget.multiselect != 'undefined') {
                            widget.multiselect('refresh');
                        }

                    } else {
                        // other widget types of options filter (e.g. grouped_checkboxes)
                    }

                } else {
                    // @todo: other filter types (e.g. S3LocationFilter)
                }
            }
        }
    };

    /**
     * ajaxUpdateOptions: Ajax-update the options in a filter form
     *
     * In global scope as called from s3.popup.js
     */
    S3.search.ajaxUpdateOptions = function(form) {

        // Ajax-load the item
        var ajaxurl = $(form).find('input.filter-ajax-url');
        if (ajaxurl.length) {
            ajaxurl = $(ajaxurl[0]).val();
        }
        $.ajax({
            'url': ajaxurl,
            'dataType': 'json'
        }).done(function(data) {
            updateOptions(data);
        }).fail(function(jqXHR, textStatus, errorThrown) {
            if (errorThrown == 'UNAUTHORIZED') {
                msg = i18n.gis_requires_login;
            } else {
                msg = jqXHR.responseText;
            }
            console.log(msg);
        });
    };

    /**
     * updatePendingTargets: update all targets which were hidden during
     *                       last filter-submit, reload page if required
     */
    var updatePendingTargets = function(form) {
        
        var url = $('#' + form).find('input.filter-submit-url[type="hidden"]')
                               .first().val(),
            targets = pendingTargets,
            target_id,
            target_data,
            needs_reload,
            queries,
            t,
            visible;

        // Clear the list
        pendingTargets = {};

        // Inspect the targets
        for (target_id in targets) {

            t = $('#' + target_id);

            if (!t.is(':visible')) {
                visible = false;
            } else {
                visible = true;
            }

            target_data = targets[target_id];

            needs_reload = target_data['needs_reload'];
            if (visible) {
                if (needs_reload) {
                    // reload immediately
                    queries = getCurrentFilters();
                    url = filterURL(url, queries);
                    window.location.href = url;
                }
            } else {
                // re-schedule for later
                pendingTargets[target_id] = target_data;
            }
        }

        // Ajax-update all visible targets
        for (target_id in targets) {
            t = $('#' + target_id);
            if (!t.is(':visible')) {
                continue
            }
            target_data = targets[target_id];
            t = $('#' + target_id);
            if (t.hasClass('dl')) {
                dlAjaxReload(target_id, target_data['queries']);
            } else if (t.hasClass('dataTable')) {
                t.dataTable().fnReloadAjax(target_data['ajaxurl']);
            } else if (t.hasClass('map_wrapper')) {
                S3.gis.refreshLayer('search_results');
            }
        }
    }

    /**
     * Set up the Tabs for an S3Summary page
     * - in global scope as called from outside
     *
     * Parameters:
     * form - {String} ID of the form to be made into Tabs
     * active_tab - {Integer} Which Section is active to start with
     */
    S3.search.summary_tabs = function(form, active_tab) {
        // Initialise jQueryUI Tabs
        $('#summary-tabs').tabs({
            active: active_tab,
            activate: function(event, ui) {
                // Unhide the section (.ui-tab's display: block overrides anyway but hey ;)
                $(ui.newPanel).removeClass('hide');
                // A New Tab has been selected
                if (ui.newTab.length) {
                    // Update the Filter Query URL to show which tab is active
                    updateFilterSubmitURL(form, 't', $(ui.newTab).index());
                }
                // Find any Map widgets in this section
                var maps = $(ui.newPanel).find('.map_wrapper');
                var gis = S3.gis;
                for (var i=0; i < maps.length; i++) {
                    var map_id = maps[i].attributes['id'].value;
                    if (undefined === gis.maps[map_id]) {
                        // Instantiate the map (can't be done when the DIV is hidden)
                        var options = gis.options[map_id];
                        gis.show_map(map_id, options);
                    }
                }
                // Update all just-unhidden widgets which have pending updates
                updatePendingTargets(form);
            }
        });
    }

    /**
     * Initialise Maps for an S3Summary page
     * - in global scope as called from callback to Map Loader
     */
    S3.search.summary_maps = function() {
        // Find any Map widgets in the initially active tab
        var maps = $('#summary-sections').find('.map_wrapper');
        for (var i=0; i < maps.length; i++) {
            var map = maps[i];
            if (!map.hidden) {
                var gis = S3.gis;
                var map_id = map.attributes['id'].value;
                if (undefined === gis.maps[map_id]) {
                    // Instantiate the map (can't be done when the DIV is hidden)
                    var options = gis.options[map_id];
                    gis.show_map(map_id, options);
                    // @ToDo: Check for default filter status? (e.g. manually-typed vars)
                    // Refresh the Search Layer with the current Filter options
                    //gis.refreshLayer('search_results');
                }
            }
        }
    }

    /**
     * document-ready script
     */
    $(document).ready(function() {

        // Mark active, otherwise submit can't find them
        $('.multiselect-filter-widget:visible').addClass('active');
        $('.groupedopts-filter-widget:visible').addClass('active');

        $('.multiselect-filter-widget').each(function() {
            if ($(this).find('option').length > 5) {
                $(this).multiselect({
                    selectedList: 5
                }).multiselectfilter();
            } else {
                $(this).multiselect({
                    selectedList: 5
                });
            }
        });

        if (typeof($.fn.multiselect_bs) != 'undefined') {
            // Alternative with bootstrap-multiselect (note the hack for the fn-name):
            $('.multiselect-filter-bootstrap:visible').addClass('active');
            $('.multiselect-filter-bootstrap').multiselect_bs();
        }

        // Hierarchical Location Filter
        $('.location-filter').on('change', function() {
            var name = this.name;
            var values = $('#' + name).val();
            var base = name.slice(0, -1);
            var level = parseInt(name.slice(-1));
            var hierarchy = S3.location_filter_hierarchy;
            // Initialise vars in a way in which we can access them via dynamic names
            this.options1 = [];
            this.options2 = [];
            this.options3 = [];
            this.options4 = [];
            this.options5 = [];
            var new_level;
            if (hierarchy.hasOwnProperty('L' + level)) {
                // Top-level
                var _hierarchy = hierarchy['L' + level];
                for (opt in _hierarchy) {
                    if (_hierarchy.hasOwnProperty(opt)) {
                        if (values === null) {
                            // Show all Options
                            for (option in _hierarchy[opt]) {
                                if (_hierarchy[opt].hasOwnProperty(option)) {
                                    new_level = level + 1;
                                    this['options' + new_level].push(option);
                                    if (typeof(_hierarchy[opt][option]) === 'object') {
                                        var __hierarchy = _hierarchy[opt][option];
                                        for (_opt in __hierarchy) {
                                            if (__hierarchy.hasOwnProperty(_opt)) {
                                                new_level = level + 2;
                                                this['options' + new_level].push(_opt);
                                                // @ToDo: Greater recursion
                                                //if (typeof(__hierarchy[_opt]) === 'object') {
                                                //}
                                            }
                                        }
                                    }
                                }
                            }
                        } else {
                            for (i in values) {
                                if (values[i] === opt) {
                                    for (option in _hierarchy[opt]) {
                                        if (_hierarchy[opt].hasOwnProperty(option)) {
                                            new_level = level + 1;
                                            this['options' + new_level].push(option);
                                            if (typeof(_hierarchy[opt][option]) === 'object') {
                                                var __hierarchy = _hierarchy[opt][option];
                                                for (_opt in __hierarchy) {
                                                    if (__hierarchy.hasOwnProperty(_opt)) {
                                                        new_level = level + 2;
                                                        this['options' + new_level].push(_opt);
                                                        // @ToDo: Greater recursion
                                                        //if (typeof(__hierarchy[_opt]) === 'object') {
                                                        //}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } else if (hierarchy.hasOwnProperty('L' + (level - 1))) {
                // Nested 1 in
                var _hierarchy = hierarchy['L' + (level - 1)];
                // Read higher level
                var _values = $('#' + base + (level - 1)).val();
                for (opt in _hierarchy) {
                    if (_hierarchy.hasOwnProperty(opt)) {
                        /* Only needed if not hiding
                        if (_values === null) {
                        } else { */
                        for (var i in _values) {
                            if (_values[i] === opt) {
                                for (option in _hierarchy[opt]) {
                                    if (_hierarchy[opt].hasOwnProperty(option)) {
                                        if (values === null) {
                                            // Show all subsequent Options
                                            for (option in _hierarchy[opt]) {
                                                if (_hierarchy[opt].hasOwnProperty(option)) {
                                                    var __hierarchy = _hierarchy[opt][option];
                                                    for (_opt in __hierarchy) {
                                                        if (__hierarchy.hasOwnProperty(_opt)) {
                                                            new_level = level + 1;
                                                            this['options' + new_level].push(_opt);
                                                            // @ToDo: Greater recursion
                                                            //if (typeof(__hierarchy[_opt]) === 'object') {
                                                            //}
                                                        }
                                                    }
                                                }
                                            }
                                        } else {
                                            for (i in values) {
                                                if (values[i] === option) {
                                                    var __hierarchy = _hierarchy[opt][option];
                                                    for (_opt in __hierarchy) {
                                                        if (__hierarchy.hasOwnProperty(_opt)) {
                                                            new_level = level + 1;
                                                            this['options' + new_level].push(_opt);
                                                            // @ToDo: Greater recursion
                                                            //if (typeof(__hierarchy[_opt]) === 'object') {
                                                            //}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } else if (hierarchy.hasOwnProperty('L' + (level - 2))) {
                // @ToDo
            }
            for (var l = level + 1; l <= 5; l++) {
                var select = $('#' + base + l);
                if (typeof(select) != 'undefined') {
                    var options = this['options' + l];
                    options.sort();
                    _options = '';
                    for (i in options) {
                        if (options.hasOwnProperty(i)) {
                            _options += '<option value="' + options[i] + '">' + options[i] + '</option>';
                        }
                    }
                    select.html(_options);
                    select.multiselect('refresh');
                    if (l === (level + 1)) {
                        if (values) {
                            // Show next level down (if hidden)
                            select.next('button').removeClass('hidden').show();
                            // @ToDo: Hide subsequent levels (if configured to do so)
                        } else {
                            // @ToDo: Hide next levels down (if configured to do so)
                            //select.next('button').hide();
                        }
                    }
                }
            }
        });

        // Filter-form submission
        $('.filter-submit').click(function() {
            var url = $(this).nextAll('input.filter-submit-url[type="hidden"]').val(),
                queries = getCurrentFilters();

            if ($(this).hasClass('filter-ajax')) {
                // Ajax-refresh the target objects

                // Get the target IDs
                var target = $(this).nextAll('input.filter-submit-target[type="hidden"]')
                                    .val();

                // Clear the list
                pendingTargets = {};

                var targets = target.split(' '),
                    needs_reload,
                    dt_ajaxurl = {},
                    ajaxurl,
                    settings,
                    config,
                    i,
                    t,
                    target_id,
                    visible;

                // Inspect the targets
                for (i=0; i < targets.length; i++) {
                    target_id = targets[i];
                    t = $('#' + target_id);

                    if (!t.is(':visible')) {
                        visible = false;
                    } else {
                        visible = true;
                    }
                    
                    needs_reload = false;
                    ajaxurl = null;
                    
                    if (t.hasClass('dl')) {
                        // data lists do not need page reload
                        needs_reload = false;
                    } else if (t.hasClass('dataTable')) {
                        // data tables need page reload if no AjaxURL configured
                        config = $('input#' + targets[i] + '_configurations');
                        if (config.length) {
                            settings = JSON.parse($(config).val());
                            ajaxurl = settings['ajaxUrl'];
                            if (typeof ajaxurl != 'undefined') {
                                ajaxurl = filterURL(ajaxurl, queries);
                            } else {
                                ajaxurl = null;
                            }
                        }
                        if (ajaxurl) {
                            dt_ajaxurl[targets[i]] = ajaxurl;
                            needs_reload = false;
                        } else {
                            needs_reload = true;
                        }
                    } else if (t.hasClass('map_wrapper')) {
                        // maps do not need page reload
                        needs_reload = false;
                    } else {
                        // all other targets need page reload
                        if (visible) {
                            // reload immediately
                            url = filterURL(url, queries);
                            window.location.href = url;
                        } else {
                            // mark the need for a reload later
                            needs_reload = true;
                        }
                    }

                    if (!visible) {
                        // schedule for later
                        pendingTargets[target_id] = {
                            needs_reload: needs_reload,
                            ajaxurl: ajaxurl,
                            queries: queries
                        };
                    }
                }

                // Ajax-update all visible targets
                for (i=0; i < targets.length; i++) {
                    target_id = targets[i]
                    t = $('#' + target_id);
                    if (!t.is(':visible')) {
                        continue;
                    } else if (t.hasClass('dl')) {
                        dlAjaxReload(target_id, queries);
                    } else if (t.hasClass('dataTable')) {
                        t.dataTable().fnReloadAjax(dt_ajaxurl[target_id]);
                    } else if (t.hasClass('map_wrapper')) {
                        S3.gis.refreshLayer('search_results', queries);
                    }
                }
            } else {
                // Reload the page
                url = filterURL(url, queries);
                window.location.href = url;
            }
        });
    });

}());
// END ========================================================================