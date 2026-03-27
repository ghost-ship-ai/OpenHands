import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";

const mockCapture = vi.fn();
vi.mock("posthog-js/react", () => ({
  usePostHog: vi.fn(() => ({
    capture: mockCapture,
  })),
}));

import { useClientAnalytics } from "#/hooks/use-client-analytics";

describe("useClientAnalytics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("trackSaasSelfhostedInquiry calls posthog.capture with correct event and location", () => {
    const { result } = renderHook(() => useClientAnalytics());
    result.current.trackSaasSelfhostedInquiry({ location: "home_page" });

    expect(mockCapture).toHaveBeenCalledOnce();
    expect(mockCapture).toHaveBeenCalledWith("saas_selfhosted_inquiry", {
      location: "home_page",
    });
  });

  it("trackEnterpriseLeadFormSubmitted calls posthog.capture with correct event and form data", () => {
    const { result } = renderHook(() => useClientAnalytics());
    result.current.trackEnterpriseLeadFormSubmitted({
      requestType: "self-hosted",
      name: "Jane Doe",
      company: "Acme Corp",
      email: "jane@acme.com",
      message: "Interested in on-prem",
    });

    expect(mockCapture).toHaveBeenCalledOnce();
    expect(mockCapture).toHaveBeenCalledWith(
      "enterprise_lead_form_submitted",
      {
        request_type: "self-hosted",
        name: "Jane Doe",
        company: "Acme Corp",
        email: "jane@acme.com",
        message: "Interested in on-prem",
      },
    );
  });

  it("does not throw when posthog is null", async () => {
    const posthogReact = await import("posthog-js/react");
    vi.mocked(posthogReact.usePostHog).mockReturnValueOnce(null as any);

    const { result } = renderHook(() => useClientAnalytics());
    expect(() =>
      result.current.trackSaasSelfhostedInquiry({ location: "login_page" }),
    ).not.toThrow();
    expect(mockCapture).not.toHaveBeenCalled();
  });
});
