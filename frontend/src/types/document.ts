export type DocumentType = "id_proof" | "income_proof" | "bank_statement";

export type DocumentStatus = "uploaded" | "ocr_failed" | "verified" | "rejected";

export interface DocumentSummary {
  id: string;
  loan_application_id: string;
  document_type: DocumentType;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  status: DocumentStatus;
  ocr_confidence: number | null;
  uploaded_at: string;
  verified_by: string | null;
  verifier_name: string | null;
  verified_at: string | null;
  verification_notes: string | null;
}

export interface DocumentDetail extends DocumentSummary {
  ocr_raw_text: string | null;
  ocr_extracted_fields: Record<string, unknown> | null;
  ocr_error_message: string | null;
}

export interface DocumentVerifyPayload {
  status: "verified" | "rejected";
  notes?: string;
}