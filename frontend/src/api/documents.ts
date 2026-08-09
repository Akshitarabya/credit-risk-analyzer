import apiClient from "@/api/client";
import type {
  DocumentDetail,
  DocumentSummary,
  DocumentType,
  DocumentVerifyPayload,
} from "@/types/document";

export async function uploadDocument(
  loanApplicationId: string,
  documentType: DocumentType,
  file: File
): Promise<DocumentSummary> {
  const formData = new FormData();
  formData.append("document_type", documentType);
  formData.append("file", file);

  const { data } = await apiClient.post<DocumentSummary>(
    `/loans/${loanApplicationId}/documents`,
    formData,
    {
      // The apiClient instance sets a default "Content-Type: application/json"
      // header. For a FormData body, the browser needs to set its own
      // multipart boundary — explicitly unsetting Content-Type here (rather
      // than hardcoding "multipart/form-data", which would be missing the
      // required boundary parameter) lets the browser generate it correctly.
      headers: { "Content-Type": undefined },
    }
  );
  return data;
}

export async function fetchDocuments(loanApplicationId: string): Promise<DocumentSummary[]> {
  const { data } = await apiClient.get<DocumentSummary[]>(`/loans/${loanApplicationId}/documents`);
  return data;
}

export async function fetchDocument(
  loanApplicationId: string,
  documentId: string
): Promise<DocumentDetail> {
  const { data } = await apiClient.get<DocumentDetail>(
    `/loans/${loanApplicationId}/documents/${documentId}`
  );
  return data;
}

export async function deleteDocument(loanApplicationId: string, documentId: string): Promise<void> {
  await apiClient.delete(`/loans/${loanApplicationId}/documents/${documentId}`);
}

export async function verifyDocument(
  loanApplicationId: string,
  documentId: string,
  payload: DocumentVerifyPayload
): Promise<DocumentSummary> {
  const { data } = await apiClient.patch<DocumentSummary>(
    `/loans/${loanApplicationId}/documents/${documentId}/verify`,
    payload
  );
  return data;
}

/**
 * Builds the authenticated download URL for a document's file. Note this
 * alone isn't enough to actually fetch it from a plain <img>/<a> tag, since
 * the backend requires a Bearer token — see DocumentUploadCard/Verification
 * Panel for how this is fetched with auth and turned into a blob URL.
 */
export function getDocumentFileUrl(loanApplicationId: string, documentId: string): string {
  const baseURL = apiClient.defaults.baseURL ?? "";
  return `${baseURL}/loans/${loanApplicationId}/documents/${documentId}/file`;
}

export async function fetchDocumentFileBlob(
  loanApplicationId: string,
  documentId: string
): Promise<Blob> {
  const { data } = await apiClient.get(`/loans/${loanApplicationId}/documents/${documentId}/file`, {
    responseType: "blob",
  });
  return data;
}