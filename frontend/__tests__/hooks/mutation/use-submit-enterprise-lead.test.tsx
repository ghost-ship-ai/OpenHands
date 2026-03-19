import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { formSubmissionService } from "#/api/form-submission-service/form-submission-service.api";
import { useSubmitEnterpriseLead } from "#/hooks/mutation/use-submit-enterprise-lead";

vi.mock("#/api/form-submission-service/form-submission-service.api");

describe("useSubmitEnterpriseLead", () => {
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

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should call submitEnterpriseLead with correct data", async () => {
    vi.mocked(formSubmissionService.submitEnterpriseLead).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useSubmitEnterpriseLead(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    });

    result.current.mutate(mockFormData);

    await waitFor(() => {
      expect(
        formSubmissionService.submitEnterpriseLead,
      ).toHaveBeenCalledWith(mockFormData);
    });
  });

  it("should return success state after successful submission", async () => {
    vi.mocked(formSubmissionService.submitEnterpriseLead).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useSubmitEnterpriseLead(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    });

    result.current.mutate(mockFormData);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
      expect(result.current.data).toEqual(mockResponse);
    });
  });

  it("should return error state after failed submission", async () => {
    const mockError = new Error("Network error");
    vi.mocked(formSubmissionService.submitEnterpriseLead).mockRejectedValue(
      mockError,
    );

    const { result } = renderHook(() => useSubmitEnterpriseLead(), {
      wrapper: ({ children }) => (
        <QueryClientProvider
          client={
            new QueryClient({
              defaultOptions: {
                mutations: {
                  retry: false,
                },
              },
            })
          }
        >
          {children}
        </QueryClientProvider>
      ),
    });

    result.current.mutate(mockFormData);

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
      expect(result.current.error).toBe(mockError);
    });
  });

  it("should call submitEnterpriseLead with self-hosted request type", async () => {
    vi.mocked(formSubmissionService.submitEnterpriseLead).mockResolvedValue(
      mockResponse,
    );

    const selfHostedFormData = {
      ...mockFormData,
      requestType: "self-hosted" as const,
    };

    const { result } = renderHook(() => useSubmitEnterpriseLead(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    });

    result.current.mutate(selfHostedFormData);

    await waitFor(() => {
      expect(
        formSubmissionService.submitEnterpriseLead,
      ).toHaveBeenCalledWith(selfHostedFormData);
    });
  });

  it("should be in pending state while submitting", async () => {
    // Create a promise that we can control
    let resolvePromise: (value: typeof mockResponse) => void;
    const controlledPromise = new Promise<typeof mockResponse>((resolve) => {
      resolvePromise = resolve;
    });

    vi.mocked(formSubmissionService.submitEnterpriseLead).mockReturnValue(
      controlledPromise,
    );

    const { result } = renderHook(() => useSubmitEnterpriseLead(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    });

    result.current.mutate(mockFormData);

    await waitFor(() => {
      expect(result.current.isPending).toBe(true);
    });

    // Resolve the promise
    resolvePromise!(mockResponse);

    await waitFor(() => {
      expect(result.current.isPending).toBe(false);
      expect(result.current.isSuccess).toBe(true);
    });
  });
});
