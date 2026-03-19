import { openHands } from "../open-hands-axios";
import {
  EnterpriseLeadFormData,
  FormSubmissionResponse,
} from "./form-submission-service.types";

/**
 * Form Submission Service API - Handles form submission endpoints
 */
export const formSubmissionService = {
  /**
   * Submit an enterprise lead capture form
   * @param formData - The form data containing requestType, name, company, email, and message
   * @returns The submission response with id, status, and created_at
   */
  submitEnterpriseLead: async (
    formData: EnterpriseLeadFormData,
  ): Promise<FormSubmissionResponse> => {
    const { data } = await openHands.post<FormSubmissionResponse>(
      "/api/v1/forms/submit",
      {
        form_type: "enterprise_lead",
        answers: {
          request_type: formData.requestType,
          name: formData.name,
          company: formData.company,
          email: formData.email,
          message: formData.message,
        },
      },
      { withCredentials: true },
    );
    return data;
  },
};
