import { describe, expect, it, vi, beforeEach } from "vitest";
import { formSubmissionService } from "#/api/form-submission-service/form-submission-service.api";

const { mockPost } = vi.hoisted(() => ({ mockPost: vi.fn() }));
vi.mock("#/api/open-hands-axios", () => ({
  openHands: { post: mockPost },
}));

describe("formSubmissionService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("submitEnterpriseLead", () => {
    const mockFormData = {
      requestType: "saas" as const,
      name: "John Doe",
      company: "Acme Corp",
      email: "john@acme.com",
      message: "Interested in enterprise plan.",
    };

    const mockResponse = {
      id: "test-submission-id",
      status: "pending",
      created_at: "2025-03-19T00:00:00Z",
    };

    it("should call the correct endpoint with correct payload", async () => {
      mockPost.mockResolvedValue({ data: mockResponse });

      await formSubmissionService.submitEnterpriseLead(mockFormData);

      expect(mockPost).toHaveBeenCalledTimes(1);
      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/forms/submit",
        {
          form_type: "enterprise_lead",
          answers: {
            request_type: "saas",
            name: "John Doe",
            company: "Acme Corp",
            email: "john@acme.com",
            message: "Interested in enterprise plan.",
          },
        },
        { withCredentials: true },
      );
    });

    it("should return the response data", async () => {
      mockPost.mockResolvedValue({ data: mockResponse });

      const result =
        await formSubmissionService.submitEnterpriseLead(mockFormData);

      expect(result).toEqual(mockResponse);
    });

    it("should handle self-hosted request type", async () => {
      mockPost.mockResolvedValue({ data: mockResponse });

      const selfHostedFormData = {
        ...mockFormData,
        requestType: "self-hosted" as const,
      };

      await formSubmissionService.submitEnterpriseLead(selfHostedFormData);

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/forms/submit",
        expect.objectContaining({
          answers: expect.objectContaining({
            request_type: "self-hosted",
          }),
        }),
        { withCredentials: true },
      );
    });

    it("should propagate errors from the API", async () => {
      const mockError = new Error("Network error");
      mockPost.mockRejectedValue(mockError);

      await expect(
        formSubmissionService.submitEnterpriseLead(mockFormData),
      ).rejects.toThrow("Network error");
    });
  });
});
