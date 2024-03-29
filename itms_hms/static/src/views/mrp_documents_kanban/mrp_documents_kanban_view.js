/** @odoo-module **/

import { registry } from "@web/core/registry";

import { kanbanView } from "@web/views/kanban/kanban_view";
import { MrpDocumentsKanbanController } from "@itms_hms/views/mrp_documents_kanban/mrp_documents_kanban_controller";
import { HMSPatientDocumentsKanbanRenderer } from "@itms_hms/views/mrp_documents_kanban/mrp_documents_kanban_renderer";

export const patientDocumentsKanbanView = {
    ...kanbanView,
    Controller: MrpDocumentsKanbanController,
    Renderer: HMSPatientDocumentsKanbanRenderer,
    buttonTemplate: "itms_hms.PatientDocumentsKanbanView.Buttons",
};

registry.category("views").add("patient_documents_kanban", patientDocumentsKanbanView);
