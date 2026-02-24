import { useMutation } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router";
import AuthService from "#/api/auth-service/auth-service.api";
import { displayErrorToast } from "#/utils/custom-toast-handlers";

type SubmitOnboardingArgs = {
  selections: Record<string, string>;
};

export const useSubmitOnboarding = () => {
  const location = useLocation();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async ({ selections }: SubmitOnboardingArgs) => {
      const searchParams = new URLSearchParams(location.search);
      const redirectUrl = searchParams.get("redirect_url") || "/";
      // Mark onboarding as complete
      const response = await AuthService.completeOnboarding(redirectUrl);
      // TODO: persist user responses
      return { selections, redirect_url: response.redirect_url };
    },
    onSuccess: (data) => {
      const finalRedirectUrl = data.redirect_url;
      // Check if the redirect URL is an external URL (starts with http or https)
      if (
        finalRedirectUrl.startsWith("http://") ||
        finalRedirectUrl.startsWith("https://")
      ) {
        // For external URLs, redirect using window.location
        window.location.href = finalRedirectUrl;
      } else {
        // For internal routes, use navigate
        navigate(finalRedirectUrl);
      }
    },
    onError: (error) => {
      displayErrorToast(error.message);
      window.location.href = "/";
    },
  });
};
