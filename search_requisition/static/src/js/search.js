odoo.define('search_requisition.search_requisition', function(require) {
    // The goal of this file is to contain JS hacks related to allowing
    "use strict";

    var ListRenderer = require('web.ListRenderer');
    var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
    var core = require('web.core');
    var relational_fields = require('web.relational_fields');
    var fieldRegistry = require('web.field_registry');
    var QWeb = core.qweb;
    var FieldsearchRequisitions = ListRenderer.extend({
        events: _.extend({
            'keyup .oe_search_input': '_onKeyUp'
        }, ListRenderer.prototype.events),


        /**
         * We want to add .o_section_and_note_list_view on the table to have stronger CSS.
         *
         * @override
         * @private
         */
        _renderView: function() {
            var self = this;
            var def = this._super();
            self.$('.o_list_table').addClass('o_section_and_note_list_view');
            if (self.arch.tag == 'tree') {
                var search = '<input type="text" class="oe_search_input mt-2 ml-5 pl-5" placeholder="Search...">';
                var row_count = '<span class="oe_row_count">Total Row: ' + '</span>';
                self.$el.find('table').addClass('oe_table_search');
                var $search = $(search).css('border', '1px solid #ccc').css('width', '50%').css('border-radius', '10px').css('margin-top', '-32px').css('height', '30px');
                var $row_count = $(row_count).css('float', 'right').css('margin-right', '30rem').css('margin-top', '4px').css('color', '#666666');
                self.$el.prepend($search);
                self.$el.prepend($row_count);
            }
            return def;
        },

        /**
         * @private
         * @param {keyEvent} event
         */
        _onKeyUp: function(event) {
            var value = $(event.currentTarget).val().toLowerCase();
            var count_row = 0;
            var $el = $(this.$el)
            $(".oe_table_search tr:not(:first)").filter(function() {
                $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
                count_row = $(this).text().toLowerCase().indexOf(value) > -1 ? count_row + 1 : count_row
            });
            $el.find('.oe_row_count').text('')
            $el.find('.oe_row_count').text('Total Row: ' + count_row)
        },
    });
    var SearchFieldOne2Many = FieldOne2Many.extend({
        /**
         * We want to use our custom renderer for the list.
         *
         * @override
         */
        _getRenderer: function() {

            if (this.view.arch.tag === 'tree') {
                return FieldsearchRequisitions;
            }
            return this._super.apply(this, arguments);
        },
    });

    fieldRegistry.add('search_requisition', SearchFieldOne2Many);
});