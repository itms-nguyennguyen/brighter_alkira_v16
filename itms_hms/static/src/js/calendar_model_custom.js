/** @odoo-module **/
import { CalendarModel } from "@web/views/calendar/calendar_model";
import { patch, unpatch } from "@web/core/utils/patch";

patch(CalendarModel.prototype, "doctor_appointment_booking_advance_axis.CalendarModel", {
    setup() {
        console.log('patch setup');
        this._super(...arguments);
    },
    async loadFilterSection(fieldName, filterInfo, previousSection) {
        const { filterFieldName, writeFieldName, writeResModel } = filterInfo;
        const fields = [writeFieldName, filterFieldName].filter(Boolean);
        const rawFilters = await this.fetchFilters(writeResModel, fields);
        const previousFilters = previousSection ? previousSection.filters : [];

        const filters = rawFilters.map((rawFilter) => {
            const previousRecordFilter = previousFilters.find(
                (f) => f.type === "record" && f.recordId === rawFilter.id
            );
            return this.makeFilterRecord(filterInfo, previousRecordFilter, rawFilter);
        });

        const field = this.meta.fields[fieldName];
        const isUserOrPartner = ["res.users", "res.partner"].includes(field.relation);
        if (isUserOrPartner) {
            const previousUserFilter = previousFilters.find((f) => f.type === "user");
            filters.push(
                this.makeFilterUser(filterInfo, previousUserFilter, fieldName, rawFilters)
            );
        }
        const previousAllFilter = previousFilters.find((f) => f.type === "all");
        const is_mmanager = this.user.hasGroup('itms_hms.group_calendar_admin').then(hasGroup => {
            if(hasGroup){
                filters.push(this.makeFilterAll(previousAllFilter, isUserOrPartner));
            }
        });
        // filters.push(this.makeFilterAll(previousAllFilter, isUserOrPartner));

        return {
            label: filterInfo.label,
            fieldName,
            filters,
            avatar: {
                field: filterInfo.avatarFieldName,
                model: filterInfo.resModel,
            },
            hasAvatar: !!filterInfo.avatarFieldName,
            write: {
                field: writeFieldName,
                model: writeResModel,
            },
            canCollapse: filters.length > 2,
            canAddFilter: !!filterInfo.writeResModel,
        };
    },

});