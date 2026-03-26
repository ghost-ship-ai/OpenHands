import { redirect } from "react-router";
import OptionService from "#/api/option-service/option-service.api";
import { WebClientConfig } from "#/api/option-service/option.types";
import { queryClient } from "#/query-client-config";
import { getSelectedOrganizationIdFromStore } from "#/stores/selected-organization-store";
import { getFirstAvailablePath } from "#/utils/settings-utils";
import { getActiveOrganizationUser } from "./permission-checks";
import { PermissionKey, rolePermissions } from "./permissions";
import { canAccessUsageDashboard } from "./usage-access";

/**
 * Helper to get config, using cache or fetching if needed.
 */
async function getConfig(): Promise<WebClientConfig | undefined> {
  let config = queryClient.getQueryData<WebClientConfig>(["web-client-config"]);
  if (!config) {
    config = await OptionService.getConfig();
    queryClient.setQueryData<WebClientConfig>(["web-client-config"], config);
  }
  return config;
}

/**
 * Gets the appropriate fallback path for permission denied scenarios.
 * Respects feature flags to avoid redirecting to hidden pages.
 */
async function getPermissionDeniedFallback(): Promise<string> {
  const config = await getConfig();

  const isSaas = config?.app_mode === "saas";
  const featureFlags = config?.feature_flags;

  // Get first available path that respects feature flags
  const fallbackPath = getFirstAvailablePath(isSaas, featureFlags);
  return fallbackPath ?? "/settings";
}

/**
 * Creates a clientLoader guard that checks if the user has the required permission.
 * Redirects to the first available settings page if permission is denied.
 *
 * In OSS mode, permission checks are bypassed since there are no user roles.
 *
 * @param requiredPermission - The permission key to check
 * @param customRedirectPath - Optional custom path to redirect to (will still respect feature flags if not provided)
 * @returns A clientLoader function that can be exported from route files
 */
export const createPermissionGuard =
  (requiredPermission: PermissionKey, customRedirectPath?: string) =>
  async ({ request }: { request: Request }) => {
    // Get config to check app_mode
    const config = await getConfig();

    // In OSS mode, skip permission checks - all settings are accessible
    if (config?.app_mode === "oss") {
      return null;
    }

    const user = await getActiveOrganizationUser();

    const url = new URL(request.url);
    const currentPath = url.pathname;

    // Helper to get redirect response, avoiding infinite loops
    const getRedirectResponse = async () => {
      const redirectPath =
        customRedirectPath ?? (await getPermissionDeniedFallback());
      // Don't redirect to the same path to avoid infinite loops
      if (redirectPath === currentPath) {
        return null;
      }
      return redirect(redirectPath);
    };

    if (!user) {
      return getRedirectResponse();
    }

    const userRole = user.role ?? "member";

    if (!rolePermissions[userRole].includes(requiredPermission)) {
      return getRedirectResponse();
    }

    return null;
  };

export const createUsageDashboardGuard =
  (customRedirectPath?: string) =>
  async ({ request }: { request: Request }) => {
    const config = await getConfig();

    if (config?.app_mode === "oss") {
      return null;
    }

    const user = await getActiveOrganizationUser();
    const organizationsData = queryClient.getQueryData<{
      items: Array<{ id: string; is_personal?: boolean }>;
      currentOrgId: string | null;
    }>(["organizations"]);
    const selectedOrgId =
      getSelectedOrganizationIdFromStore() ??
      organizationsData?.currentOrgId ??
      user?.org_id;
    const selectedOrg = organizationsData?.items?.find(
      (organization) => organization.id === selectedOrgId,
    );

    const url = new URL(request.url);
    const currentPath = url.pathname;
    const redirectPath =
      customRedirectPath ?? (await getPermissionDeniedFallback());

    if (redirectPath === currentPath) {
      return null;
    }

    if (!user || !canAccessUsageDashboard(selectedOrg, user.role)) {
      return redirect(redirectPath);
    }

    return null;
  };
