odoo.define('wepelo_equipment.EditableListRendererWepelo', function (require) {
"use strict";

/**
 * Editable List renderer
 *
 * The list renderer is reasonably complex, so we split it in two files. This
 * file simply 'includes' the basic ListRenderer to add all the necessary
 * behaviors to enable editing records.
 *
 * Unlike Odoo v10 and before, this list renderer is independant from the form
 * view. It uses the same widgets, but the code is totally stand alone.
 */
var ListRenderer = require('web.ListRenderer');

ListRenderer.include({
    // remove resets the default widths computation now that the table is visible
       _getColumnWidth: function (column) {
        if (column.attrs.width) {
            return column.attrs.width;
        }
        const fieldsInfo = this.state.fieldsInfo.list;
        const name = column.attrs.name;
        if (!fieldsInfo[name]) {
            // Unnamed columns get default value
            return '1';
        }
        const widget = fieldsInfo[name].Widget.prototype;
        if ('widthInList' in widget) {
            return widget.widthInList;
        }
        const field = this.state.fields[name];
        if (!field) {
            // this is not a field. Probably a button or something of unknown
            // width.
            return '1';
        }
        const fixedWidths = {
            boolean: '50px',
            date: '146px',
            datetime: '146px',
            float: '92px',
            integer: '74px',
            monetary: '104px',
        };
        let type = field.type;
        if (fieldsInfo[name].widget in fixedWidths) {
            type = fieldsInfo[name].widget;
        }
        return fixedWidths[type] || '1';
    }

});

});
