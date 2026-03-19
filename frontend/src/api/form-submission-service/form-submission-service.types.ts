export type RequestType = "saas" | "self-hosted";

export interface EnterpriseLeadFormData {
  requestType: RequestType;
  name: string;
  company: string;
  email: string;
  message: string;
}

export interface FormSubmissionRequest {
  form_type: string;
  answers: Record<string, unknown>;
}

export interface FormSubmissionResponse {
  id: string;
  status: string;
  created_at: string;
}
