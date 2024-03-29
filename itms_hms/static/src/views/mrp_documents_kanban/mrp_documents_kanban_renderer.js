/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { HMSPatientDocumentsKanbanRecord } from "@itms_hms/views/mrp_documents_kanban/mrp_documents_kanban_record";
import { FileUploadProgressContainer } from "@web/core/file_upload/file_upload_progress_container";
import { FileUploadProgressKanbanRecord } from "@web/core/file_upload/file_upload_progress_record";

export class HMSPatientDocumentsKanbanRenderer extends KanbanRenderer {
    setup() {
        super.setup();
        this.fileUploadService = useService("file_upload");
    }
}

HMSPatientDocumentsKanbanRenderer.components = {
    ...KanbanRenderer.components,
    FileUploadProgressContainer,
    FileUploadProgressKanbanRecord,
    KanbanRecord: HMSPatientDocumentsKanbanRecord,
};
HMSPatientDocumentsKanbanRenderer.template = "itms_hms.HMSPatientDocumentsKanbanRenderer";
