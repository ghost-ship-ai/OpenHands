import { useQuery } from "@tanstack/react-query";
import { organizationService } from "#/api/organization-service/organization-service.api";
import { useSelectedOrganizationId } from "#/context/use-selected-organization";
import { useConfig } from "./use-config";

export const useOrganizationUsage = () => {
  const { organizationId } = useSelectedOrganizationId();
  const { data: config } = useConfig();

  const isSaas = config?.app_mode === "saas";

  return useQuery({
    queryKey: ["organizations", organizationId, "usage"],
    queryFn: () =>
      organizationService.getOrganizationUsage({ orgId: organizationId! }),
    enabled: isSaas && !!organizationId,
  });
};
