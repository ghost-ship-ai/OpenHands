import { useMutation } from "@tanstack/react-query";
import { formSubmissionService } from "#/api/form-submission-service/form-submission-service.api";
import { EnterpriseLeadFormData } from "#/api/form-submission-service/form-submission-service.types";

/**
 * Hook for submitting enterprise lead capture forms.
 * Handles the API call and provides loading/error states.
 */
export const useSubmitEnterpriseLead = () =>
  useMutation({
    mutationFn: (formData: EnterpriseLeadFormData) =>
      formSubmissionService.submitEnterpriseLead(formData),
  });
