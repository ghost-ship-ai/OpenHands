import React from "react";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";

import { BrandButton } from "#/components/features/settings/brand-button";
import { OptionalTag } from "#/components/features/settings/optional-tag";
import { SettingsDropdownInput } from "#/components/features/settings/settings-dropdown-input";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";
import { LlmSettingsInputsSkeleton } from "#/components/features/settings/llm-settings/llm-settings-inputs-skeleton";
import { ModelSelector } from "#/components/shared/modals/settings/model-selector";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { usePermission } from "#/hooks/organizations/use-permissions";
import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { useConfig } from "#/hooks/query/use-config";
import { useMe } from "#/hooks/query/use-me";
import { useSettings } from "#/hooks/query/use-settings";
import { I18nKey } from "#/i18n/declaration";
import { SettingsFieldSchema } from "#/types/settings";
import { HelpLink } from "#/ui/help-link";
import { Typography } from "#/ui/typography";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { createPermissionGuard } from "#/utils/org/permission-guard";
import { organizeModelsAndProviders } from "#/utils/organize-models-and-providers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import {
  buildInitialSettingsFormValues,
  buildSdkSettingsPayload,
  getVisibleSettingsSections,
  hasAdvancedSettings,
  hasMinorSettings,
  inferInitialView,
  SettingsDirtyState,
  SettingsFormValues,
  type SettingsView,
} from "#/utils/sdk-settings-schema";
import { cn } from "#/utils/utils";

// ---------------------------------------------------------------------------
// Help links – UI-only mapping from field keys to user-facing guidance.
// ---------------------------------------------------------------------------
const FIELD_HELP_LINKS: Record<
  string,
  { text: string; linkText: string; href: string }
> = {
  "llm.api_key": {
    text: "Don't know your API key?",
    linkText: "Click here for instructions.",
    href: "https://docs.all-hands.dev/usage/local-setup#getting-an-api-key",
  },
};

// ---------------------------------------------------------------------------
// Generic schema field renderer
// ---------------------------------------------------------------------------
function FieldHelp({ field }: { field: SettingsFieldSchema }) {
  const helpLink = FIELD_HELP_LINKS[field.key];

  return (
    <>
      {field.description ? (
        <Typography.Paragraph className="text-tertiary-alt text-xs leading-5">
          {field.description}
        </Typography.Paragraph>
      ) : null}
      {helpLink ? (
        <HelpLink
          testId={`help-link-${field.key}`}
          text={helpLink.text}
          linkText={helpLink.linkText}
          href={helpLink.href}
          size="settings"
          linkColor="white"
        />
      ) : null}
    </>
  );
}

function isSelectField(field: SettingsFieldSchema): boolean {
  return field.choices.length > 0;
}

function isBooleanField(field: SettingsFieldSchema): boolean {
  return field.value_type === "boolean" && !isSelectField(field);
}

function isJsonField(field: SettingsFieldSchema): boolean {
  return field.value_type === "array" || field.value_type === "object";
}

function getInputType(
  field: SettingsFieldSchema,
): React.HTMLInputTypeAttribute {
  if (field.secret) {
    return "password";
  }
  if (field.value_type === "integer" || field.value_type === "number") {
    return "number";
  }
  return "text";
}

function SchemaField({
  field,
  value,
  isDisabled,
  onChange,
}: {
  field: SettingsFieldSchema;
  value: string | boolean;
  isDisabled: boolean;
  onChange: (value: string | boolean) => void;
}) {
  if (isBooleanField(field)) {
    return (
      <div className="flex flex-col gap-1.5">
        <SettingsSwitch
          testId={`sdk-settings-${field.key}`}
          isToggled={Boolean(value)}
          isDisabled={isDisabled}
          onToggle={onChange}
        >
          {field.label}
        </SettingsSwitch>
        <FieldHelp field={field} />
      </div>
    );
  }

  if (isSelectField(field)) {
    return (
      <div className="flex flex-col gap-1.5">
        <SettingsDropdownInput
          testId={`sdk-settings-${field.key}`}
          name={field.key}
          label={field.label}
          items={field.choices.map((choice) => ({
            key: String(choice.value),
            label: choice.label,
          }))}
          selectedKey={value === "" ? undefined : String(value)}
          isClearable={!field.required}
          required={field.required}
          showOptionalTag={!field.required}
          isDisabled={isDisabled}
          onSelectionChange={(selectedKey) =>
            onChange(String(selectedKey ?? ""))
          }
        />
        <FieldHelp field={field} />
      </div>
    );
  }

  if (isJsonField(field)) {
    return (
      <label className="flex flex-col gap-2.5 w-full">
        <div className="flex items-center gap-2">
          <span className="text-sm">{field.label}</span>
          {!field.required ? <OptionalTag /> : null}
        </div>
        <textarea
          data-testid={`sdk-settings-${field.key}`}
          name={field.key}
          value={String(value ?? "")}
          required={field.required}
          disabled={isDisabled}
          onChange={(event) => onChange(event.target.value)}
          className={cn(
            "bg-tertiary border border-[#717888] min-h-32 w-full rounded-sm p-2 font-mono text-sm",
            "placeholder:italic placeholder:text-tertiary-alt",
            "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
          )}
        />
        <FieldHelp field={field} />
      </label>
    );
  }

  return (
    <div className="flex flex-col gap-1.5">
      <SettingsInput
        testId={`sdk-settings-${field.key}`}
        name={field.key}
        label={field.label}
        type={getInputType(field)}
        value={String(value ?? "")}
        required={field.required}
        showOptionalTag={!field.required}
        isDisabled={isDisabled}
        onChange={onChange}
        className="w-full"
      />
      <FieldHelp field={field} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// View tier toggle
// ---------------------------------------------------------------------------
function ViewToggle({
  view,
  setView,
  showAdvanced,
  showAll,
}: {
  view: SettingsView;
  setView: (v: SettingsView) => void;
  showAdvanced: boolean;
  showAll: boolean;
}) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center gap-2 mb-6">
      <BrandButton
        testId="llm-settings-basic-toggle"
        variant={view === "basic" ? "primary" : "secondary"}
        type="button"
        onClick={() => setView("basic")}
      >
        {t(I18nKey.SETTINGS$BASIC)}
      </BrandButton>
      {showAdvanced ? (
        <BrandButton
          testId="llm-settings-advanced-toggle"
          variant={view === "advanced" ? "primary" : "secondary"}
          type="button"
          onClick={() => setView("advanced")}
        >
          {t(I18nKey.SETTINGS$ADVANCED)}
        </BrandButton>
      ) : null}
      {showAll ? (
        <BrandButton
          testId="llm-settings-all-toggle"
          variant={view === "all" ? "primary" : "secondary"}
          type="button"
          onClick={() => setView("all")}
        >
          {t(I18nKey.SETTINGS$ALL)}
        </BrandButton>
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Specially-rendered critical fields (llm.model, llm.api_key, llm.base_url)
// ---------------------------------------------------------------------------
function CriticalFields({
  models,
  values,
  isDisabled,
  onChange,
}: {
  models: string[];
  values: SettingsFormValues;
  isDisabled: boolean;
  onChange: (key: string, value: string | boolean) => void;
}) {
  const currentModel = String(values["llm.model"] ?? "");
  const currentApiKey = String(values["llm.api_key"] ?? "");
  const currentBaseUrl = String(values["llm.base_url"] ?? "");
  const isApiKeySet = currentApiKey === "<hidden>" || currentApiKey.length > 0;
  const apiKeyHelp = FIELD_HELP_LINKS["llm.api_key"];

  return (
    <div className="flex flex-col gap-4">
      <ModelSelector
        models={organizeModelsAndProviders(models)}
        currentModel={currentModel || undefined}
        isDisabled={isDisabled}
        onChange={(_provider, model) => {
          if (model !== null) {
            onChange("llm.model", model);
          }
        }}
      />

      <SettingsInput
        testId="sdk-settings-llm.api_key"
        name="llm.api_key"
        label="API Key"
        type="password"
        value={currentApiKey}
        required={false}
        showOptionalTag
        isDisabled={isDisabled}
        placeholder={isApiKeySet ? "<hidden>" : ""}
        onChange={(val) => onChange("llm.api_key", val)}
        className="w-full"
      />
      {apiKeyHelp ? (
        <HelpLink
          testId="help-link-llm.api_key"
          text={apiKeyHelp.text}
          linkText={apiKeyHelp.linkText}
          href={apiKeyHelp.href}
          size="settings"
          linkColor="white"
        />
      ) : null}

      <SettingsInput
        testId="sdk-settings-llm.base_url"
        name="llm.base_url"
        label="Base URL"
        type="text"
        value={currentBaseUrl}
        required={false}
        showOptionalTag
        isDisabled={isDisabled}
        onChange={(val) => onChange("llm.base_url", val)}
        className="w-full"
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------
function LlmSettingsScreen() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { mutate: saveSettings, isPending } = useSaveSettings();
  const { data: settings, isLoading, isFetching } = useSettings();
  const { data: config } = useConfig();
  const { data: me } = useMe();
  const { data: aiConfigOptions } = useAIConfigOptions();
  const { hasPermission } = usePermission(me?.role ?? "member");

  const isOssMode = config?.app_mode === "oss";
  const isReadOnly = isOssMode ? false : !hasPermission("edit_llm_settings");

  const [view, setView] = React.useState<SettingsView>("basic");
  const [values, setValues] = React.useState<SettingsFormValues>({});
  const [dirty, setDirty] = React.useState<SettingsDirtyState>({});

  const schema = settings?.sdk_settings_schema ?? null;
  const showAdvanced = hasAdvancedSettings(schema);
  const showAll = hasMinorSettings(schema);

  React.useEffect(() => {
    const checkout = searchParams.get("checkout");

    if (checkout === "success") {
      displaySuccessToast(t(I18nKey.SUBSCRIPTION$SUCCESS));
      setSearchParams({});
    } else if (checkout === "cancel") {
      displayErrorToast(t(I18nKey.SUBSCRIPTION$FAILURE));
      setSearchParams({});
    }
  }, [searchParams, setSearchParams, t]);

  React.useEffect(() => {
    if (!settings?.sdk_settings_schema) {
      return;
    }

    setValues(buildInitialSettingsFormValues(settings));
    setDirty({});
    setView(inferInitialView(settings));
  }, [settings]);

  const visibleSections = React.useMemo(() => {
    if (!schema) {
      return [];
    }

    return getVisibleSettingsSections(schema, values, view);
  }, [schema, values, view]);

  const handleFieldChange = React.useCallback(
    (fieldKey: string, nextValue: string | boolean) => {
      setValues((previousValues) => ({
        ...previousValues,
        [fieldKey]: nextValue,
      }));
      setDirty((previousDirty) => ({
        ...previousDirty,
        [fieldKey]: true,
      }));
    },
    [],
  );

  const handleError = React.useCallback(
    (error: AxiosError) => {
      const errorMessage = retrieveAxiosErrorMessage(error);
      displayErrorToast(errorMessage || t(I18nKey.ERROR$GENERIC));
    },
    [t],
  );

  const handleSave = () => {
    if (!schema || isReadOnly) {
      return;
    }

    let payload: ReturnType<typeof buildSdkSettingsPayload>;
    try {
      payload = buildSdkSettingsPayload(schema, values, dirty);
    } catch (error) {
      displayErrorToast(
        error instanceof Error ? error.message : t(I18nKey.ERROR$GENERIC),
      );
      return;
    }

    if (Object.keys(payload).length === 0) {
      return;
    }

    saveSettings(payload, {
      onError: handleError,
      onSuccess: () => {
        displaySuccessToast(t(I18nKey.SETTINGS$SAVED_WARNING));
        setDirty({});
      },
    });
  };

  if (isLoading || isFetching) {
    return <LlmSettingsInputsSkeleton />;
  }

  if (!schema) {
    return (
      <Typography.Paragraph className="text-tertiary-alt">
        {t(I18nKey.SETTINGS$SDK_SCHEMA_UNAVAILABLE)}
      </Typography.Paragraph>
    );
  }

  if (Object.keys(values).length === 0) {
    return <LlmSettingsInputsSkeleton />;
  }

  return (
    <div data-testid="llm-settings-screen" className="h-full relative">
      <ViewToggle
        view={view}
        setView={setView}
        showAdvanced={showAdvanced}
        showAll={showAll}
      />

      <div className="flex flex-col gap-8 pb-20">
        {/* Specially-rendered critical fields */}
        <CriticalFields
          models={aiConfigOptions?.models ?? []}
          values={values}
          isDisabled={isReadOnly}
          onChange={handleFieldChange}
        />

        {/* Generic schema-driven sections */}
        {visibleSections.map((section) => (
          <section key={section.key} className="flex flex-col gap-4">
            <Typography.H3>{section.label}</Typography.H3>
            <div className="grid gap-4 xl:grid-cols-2">
              {section.fields.map((field) => (
                <SchemaField
                  key={field.key}
                  field={field}
                  value={values[field.key]}
                  isDisabled={isReadOnly}
                  onChange={(nextValue) =>
                    handleFieldChange(field.key, nextValue)
                  }
                />
              ))}
            </div>
          </section>
        ))}
      </div>

      {!isReadOnly ? (
        <div className="sticky bottom-0 bg-base py-4">
          <BrandButton
            testId="save-button"
            type="button"
            variant="primary"
            isDisabled={isPending || Object.keys(dirty).length === 0}
            onClick={handleSave}
          >
            {isPending
              ? t(I18nKey.SETTINGS$SAVING)
              : t(I18nKey.SETTINGS$SAVE_CHANGES)}
          </BrandButton>
        </div>
      ) : null}
    </div>
  );
}

export const clientLoader = createPermissionGuard("view_llm_settings");

export default LlmSettingsScreen;
