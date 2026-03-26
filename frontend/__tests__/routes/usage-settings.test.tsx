import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import UsageSettingsScreen from "#/routes/usage-settings";
import { OrganizationUsage } from "#/types/org";

const mockUseOrganizationUsage = vi.fn();

vi.mock("#/hooks/query/use-organization-usage", () => ({
  useOrganizationUsage: () => mockUseOrganizationUsage(),
}));

vi.mock("react-i18next", async () => {
  const actual =
    await vi.importActual<typeof import("react-i18next")>("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          SETTINGS$NAV_USAGE: "Usage",
          USAGE$PAGE_DESCRIPTION: "Usage page description",
          USAGE$AVERAGE_COST_TITLE: "Average cost per conversation (30 days)",
          USAGE$TOTAL_CONVERSATIONS_TITLE: "Total conversations",
          USAGE$TREND_TITLE: "30-day conversation trend",
          USAGE$TREND_DESCRIPTION: "Daily conversation volume for the last 30 days.",
          USAGE$TOP_REPOSITORIES_TITLE: "Top repositories",
          USAGE$TOP_REPOSITORIES_DESCRIPTION:
            "Repositories with the most conversations in this workspace.",
          USAGE$NO_REPOSITORIES: "No repository data available yet.",
          USAGE$NO_REPOSITORY_LABEL: "No repository",
          USAGE$EMPTY_TITLE: "No conversations yet",
          USAGE$EMPTY_DESCRIPTION:
            "Usage metrics will appear here after conversations are created in this workspace.",
          USAGE$ERROR_DESCRIPTION:
            "We could not load usage metrics right now. Please try again.",
          ERROR$GENERIC: "An error occurred",
        };
        return translations[key] || key;
      },
      i18n: {
        changeLanguage: vi.fn(),
      },
    }),
  };
});

const renderScreen = () => {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <UsageSettingsScreen />
    </QueryClientProvider>,
  );
};

const usageData: OrganizationUsage = {
  summary: {
    average_cost_per_conversation_last_30_days: 1.25,
    total_conversations: 9,
  },
  daily_conversations: [
    { date: "2026-03-24", conversation_count: 2 },
    { date: "2026-03-25", conversation_count: 3 },
    { date: "2026-03-26", conversation_count: 4 },
  ],
  top_repositories: [
    { repository: "No repository", conversation_count: 5 },
    { repository: "openhands/backend", conversation_count: 4 },
  ],
};

describe("UsageSettingsScreen", () => {
  it("renders loading state", () => {
    mockUseOrganizationUsage.mockReturnValue({
      isLoading: true,
      isError: false,
      data: undefined,
    });

    renderScreen();

    expect(screen.getByTestId("usage-loading-state")).toBeInTheDocument();
  });

  it("renders usage metrics and charts", () => {
    mockUseOrganizationUsage.mockReturnValue({
      isLoading: false,
      isError: false,
      data: usageData,
    });

    renderScreen();

    expect(screen.getByTestId("usage-settings-screen")).toBeInTheDocument();
    expect(screen.getByText("Usage")).toBeInTheDocument();
    expect(
      screen.getByText("Average cost per conversation (30 days)"),
    ).toBeInTheDocument();
    expect(screen.getByText("$1.25")).toBeInTheDocument();
    expect(screen.getByText("Total conversations")).toBeInTheDocument();
    expect(screen.getByText("9")).toBeInTheDocument();
    expect(screen.getByText("No repository")).toBeInTheDocument();
    expect(screen.getByText("openhands/backend")).toBeInTheDocument();
  });

  it("renders empty state when there is no usage data yet", () => {
    mockUseOrganizationUsage.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        ...usageData,
        summary: {
          average_cost_per_conversation_last_30_days: 0,
          total_conversations: 0,
        },
        top_repositories: [],
      },
    });

    renderScreen();

    expect(screen.getByTestId("usage-empty-state")).toBeInTheDocument();
    expect(screen.getByText("No conversations yet")).toBeInTheDocument();
  });

  it("renders error state", () => {
    mockUseOrganizationUsage.mockReturnValue({
      isLoading: false,
      isError: true,
      data: undefined,
    });

    renderScreen();

    expect(screen.getByTestId("usage-error-state")).toBeInTheDocument();
    expect(screen.getByText("An error occurred")).toBeInTheDocument();
  });
});
