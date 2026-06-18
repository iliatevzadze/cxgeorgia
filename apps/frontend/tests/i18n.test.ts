import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");

function collectKeys(
  value: unknown,
  prefix = "",
): string[] {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return prefix ? [prefix] : [];
  }

  return Object.entries(value as Record<string, unknown>).flatMap(
    ([key, nested]) => {
      const path = prefix ? `${prefix}.${key}` : key;
      if (
        nested !== null &&
        typeof nested === "object" &&
        !Array.isArray(nested)
      ) {
        return collectKeys(nested, path);
      }
      return [path];
    },
  );
}

const ka = JSON.parse(
  readFileSync(join(rootDir, "messages/ka.json"), "utf-8"),
) as Record<string, unknown>;
const en = JSON.parse(
  readFileSync(join(rootDir, "messages/en.json"), "utf-8"),
) as Record<string, unknown>;

const kaKeys = collectKeys(ka).sort();
const enKeys = collectKeys(en).sort();

const requiredNamespaces = ["metadata", "home", "locale", "auth", "workspaces"];

test("both locale files include required top-level namespaces", () => {
  for (const namespace of requiredNamespaces) {
    assert.ok(namespace in ka, `ka.json missing namespace: ${namespace}`);
    assert.ok(namespace in en, `en.json missing namespace: ${namespace}`);
  }
});

test("ka.json and en.json have matching keys", () => {
  assert.deepEqual(
    kaKeys,
    enKeys,
    `Key mismatch.\nOnly in ka: ${kaKeys.filter((k) => !enKeys.includes(k)).join(", ")}\nOnly in en: ${enKeys.filter((k) => !kaKeys.includes(k)).join(", ")}`,
  );
});

test("required home keys exist in both locales", () => {
  const requiredHomeKeys = [
    "home.phase",
    "home.title",
    "home.subtitle",
    "home.description",
    "home.statusLabel",
    "home.statusValue",
    "home.backendLabel",
    "home.backendValue",
    "home.infrastructureLabel",
    "home.infrastructureValue",
    "home.notBuiltTitle",
    "home.notBuiltDashboard",
    "home.notBuiltCases",
    "home.notBuiltIntegrations",
    "home.language",
  ];

  for (const key of requiredHomeKeys) {
    assert.ok(kaKeys.includes(key), `ka.json missing key: ${key}`);
    assert.ok(enKeys.includes(key), `en.json missing key: ${key}`);
  }
});

test("required workspace keys exist in both locales", () => {
  const requiredWorkspaceKeys = [
    "workspaces.nav.myWorkspaces",
    "workspaces.nav.createWorkspace",
    "workspaces.list.title",
    "workspaces.list.description",
    "workspaces.list.empty",
    "workspaces.list.createLink",
    "workspaces.list.loading",
    "workspaces.list.error",
    "workspaces.list.roleLabel",
    "workspaces.list.statusLabel",
    "workspaces.list.openLink",
    "workspaces.create.title",
    "workspaces.create.description",
    "workspaces.create.nameLabel",
    "workspaces.create.namePlaceholder",
    "workspaces.create.submit",
    "workspaces.create.success",
    "workspaces.create.error",
    "workspaces.create.backToList",
    "workspaces.create.openWorkspace",
    "workspaces.detail.title",
    "workspaces.detail.description",
    "workspaces.detail.slugLabel",
    "workspaces.detail.statusLabel",
    "workspaces.detail.roleLabel",
    "workspaces.detail.membershipsLink",
    "workspaces.detail.openAppLink",
    "workspaces.detail.backToList",
    "workspaces.detail.loading",
    "workspaces.detail.error",
    "workspaces.memberships.title",
    "workspaces.memberships.description",
    "workspaces.memberships.userId",
    "workspaces.memberships.role",
    "workspaces.memberships.status",
    "workspaces.memberships.loading",
    "workspaces.memberships.error",
    "workspaces.memberships.backToWorkspace",
    "workspaces.common.loading",
    "workspaces.common.loadError",
    "workspaces.common.notFound",
    "workspaces.common.accessDenied",
    "workspaces.app.shell.label",
    "workspaces.app.shell.statusLabel",
    "workspaces.app.shell.roleLabel",
    "workspaces.app.shell.accountNav",
    "workspaces.app.shell.account",
    "workspaces.app.shell.allWorkspaces",
    "workspaces.app.shell.logout",
    "workspaces.app.shell.workspaceDetail",
    "workspaces.app.shell.backToWorkspaces",
    "workspaces.app.nav.label",
    "workspaces.app.nav.home",
    "workspaces.app.nav.dashboard",
    "workspaces.app.nav.cases",
    "workspaces.app.nav.customers",
    "workspaces.app.nav.settings",
    "workspaces.app.home.title",
    "workspaces.app.home.description",
    "workspaces.app.home.ready",
    "workspaces.app.home.notBuiltTitle",
    "workspaces.app.home.notBuiltDashboard",
    "workspaces.app.home.notBuiltCases",
    "workspaces.app.home.notBuiltCustomers",
    "workspaces.app.home.notBuiltIntegrations",
    "workspaces.app.cases.title",
    "workspaces.app.cases.description",
    "workspaces.app.cases.loading",
    "workspaces.app.cases.error",
    "workspaces.app.cases.emptyTitle",
    "workspaces.app.cases.emptyMessage",
    "workspaces.app.cases.titleLabel",
    "workspaces.app.cases.statusLabel",
    "workspaces.app.cases.priorityLabel",
    "workspaces.app.cases.sourceLabel",
    "workspaces.app.cases.customerLabel",
    "workspaces.app.cases.createdAtLabel",
    "workspaces.app.cases.noCustomer",
    "workspaces.app.cases.create.title",
    "workspaces.app.cases.create.description",
    "workspaces.app.cases.create.titleLabel",
    "workspaces.app.cases.create.titlePlaceholder",
    "workspaces.app.cases.create.descriptionLabel",
    "workspaces.app.cases.create.priorityLabel",
    "workspaces.app.cases.create.sourceLabel",
    "workspaces.app.cases.create.customerNameLabel",
    "workspaces.app.cases.create.customerEmailLabel",
    "workspaces.app.cases.create.externalReferenceLabel",
    "workspaces.app.cases.create.submit",
    "workspaces.app.cases.create.submitting",
    "workspaces.app.cases.create.success",
    "workspaces.app.cases.create.error",
    "workspaces.app.cases.create.titleRequired",
    "workspaces.app.cases.create.priorityOptions.low",
    "workspaces.app.cases.create.priorityOptions.normal",
    "workspaces.app.cases.create.priorityOptions.high",
    "workspaces.app.cases.create.priorityOptions.urgent",
    "workspaces.app.cases.create.sourceOptions.manual",
    "workspaces.app.cases.create.sourceOptions.email",
    "workspaces.app.cases.create.sourceOptions.chat",
    "workspaces.app.cases.create.sourceOptions.phone",
    "workspaces.app.cases.create.sourceOptions.web",
    "workspaces.app.cases.create.sourceOptions.import",
    "workspaces.app.cases.detail.description",
    "workspaces.app.cases.detail.loading",
    "workspaces.app.cases.detail.error",
    "workspaces.app.cases.detail.backToCases",
    "workspaces.app.cases.detail.titleLabel",
    "workspaces.app.cases.detail.descriptionLabel",
    "workspaces.app.cases.detail.statusLabel",
    "workspaces.app.cases.detail.priorityLabel",
    "workspaces.app.cases.detail.sourceLabel",
    "workspaces.app.cases.detail.customerNameLabel",
    "workspaces.app.cases.detail.customerEmailLabel",
    "workspaces.app.cases.detail.externalReferenceLabel",
    "workspaces.app.cases.detail.createdByLabel",
    "workspaces.app.cases.detail.assignedToLabel",
    "workspaces.app.cases.detail.createdAtLabel",
    "workspaces.app.cases.detail.updatedAtLabel",
    "workspaces.app.cases.detail.noValue",
    "workspaces.app.cases.detail.updateTitle",
    "workspaces.app.cases.detail.updateDescription",
    "workspaces.app.cases.detail.submit",
    "workspaces.app.cases.detail.submitting",
    "workspaces.app.cases.detail.success",
    "workspaces.app.cases.detail.updateError",
    "workspaces.app.cases.detail.validationError",
    "workspaces.app.cases.detail.titleRequired",
    "workspaces.app.cases.detail.noChanges",
    "workspaces.app.cases.detail.assignmentTitle",
    "workspaces.app.cases.detail.assignmentDescription",
    "workspaces.app.cases.detail.assignmentLabel",
    "workspaces.app.cases.detail.assignmentUnassigned",
    "workspaces.app.cases.detail.assignmentSave",
    "workspaces.app.cases.detail.assignmentSaving",
    "workspaces.app.cases.detail.assignmentSuccess",
    "workspaces.app.cases.detail.assignmentError",
    "workspaces.app.cases.detail.assignmentValidationError",
    "workspaces.app.cases.detail.assignmentNoChanges",
    "workspaces.app.cases.detail.assignmentLoading",
    "workspaces.app.cases.detail.membershipsLoadError",
    "workspaces.app.cases.detail.assignmentMembersEmpty",
    "workspaces.app.cases.detail.commentsTitle",
    "workspaces.app.cases.detail.commentsDescription",
    "workspaces.app.cases.detail.commentsLoading",
    "workspaces.app.cases.detail.commentsLoadError",
    "workspaces.app.cases.detail.commentsEmpty",
    "workspaces.app.cases.detail.commentBodyLabel",
    "workspaces.app.cases.detail.commentInternalLabel",
    "workspaces.app.cases.detail.commentSubmit",
    "workspaces.app.cases.detail.commentSubmitting",
    "workspaces.app.cases.detail.commentCreateSuccess",
    "workspaces.app.cases.detail.commentCreateError",
    "workspaces.app.cases.detail.commentValidationError",
    "workspaces.app.cases.detail.commentBodyRequired",
    "workspaces.app.cases.detail.commentAuthorLabel",
    "workspaces.app.cases.detail.commentVisibilityLabel",
    "workspaces.app.cases.detail.commentVisibilityInternal",
    "workspaces.app.cases.detail.commentVisibilityPublic",
    "workspaces.app.cases.detail.commentDeleteButton",
    "workspaces.app.cases.detail.commentConfirmDeleteButton",
    "workspaces.app.cases.detail.commentCancelDeleteButton",
    "workspaces.app.cases.detail.commentDeleting",
    "workspaces.app.cases.detail.commentDeleteError",
    "workspaces.app.cases.detail.commentDeleteNotFound",
    "workspaces.app.cases.detail.commentEditButton",
    "workspaces.app.cases.detail.commentEditSave",
    "workspaces.app.cases.detail.commentCancelEditButton",
    "workspaces.app.cases.detail.commentEditSaving",
    "workspaces.app.cases.detail.commentEditSuccess",
    "workspaces.app.cases.detail.commentEditError",
    "workspaces.app.cases.detail.tagsTitle",
    "workspaces.app.cases.detail.tagsDescription",
    "workspaces.app.cases.detail.tagsLoading",
    "workspaces.app.cases.detail.tagsLoadError",
    "workspaces.app.cases.detail.tagsEmpty",
    "workspaces.app.cases.detail.tagAttachLabel",
    "workspaces.app.cases.detail.tagAttachPlaceholder",
    "workspaces.app.cases.detail.tagAttachButton",
    "workspaces.app.cases.detail.tagAttaching",
    "workspaces.app.cases.detail.tagAttachSuccess",
    "workspaces.app.cases.detail.tagAttachError",
    "workspaces.app.cases.detail.tagDetachButton",
    "workspaces.app.cases.detail.tagDetaching",
    "workspaces.app.cases.detail.tagDetachSuccess",
    "workspaces.app.cases.detail.tagDetachError",
    "workspaces.app.cases.detail.tagCreateNameLabel",
    "workspaces.app.cases.detail.tagCreateSlugLabel",
    "workspaces.app.cases.detail.tagCreateColorLabel",
    "workspaces.app.cases.detail.tagCreateButton",
    "workspaces.app.cases.detail.tagCreating",
    "workspaces.app.cases.detail.tagCreateAttachSuccess",
    "workspaces.app.cases.detail.tagCreateError",
    "workspaces.app.cases.detail.tagFieldsRequired",
    "workspaces.app.cases.detail.tagDuplicateSlugError",
    "workspaces.app.cases.detail.tagValidationError",
    "workspaces.app.cases.detail.activitiesTitle",
    "workspaces.app.cases.detail.activitiesDescription",
    "workspaces.app.cases.detail.activitiesLoading",
    "workspaces.app.cases.detail.activitiesLoadError",
    "workspaces.app.cases.detail.activitiesEmpty",
    "workspaces.app.cases.detail.activityCreatedFieldTitle",
    "workspaces.app.cases.detail.activityTypeLabels.case_created",
    "workspaces.app.cases.detail.activityTypeLabels.case_updated",
    "workspaces.app.cases.detail.activityTypeLabels.status_changed",
    "workspaces.app.cases.detail.activityTypeLabels.priority_changed",
    "workspaces.app.cases.detail.activityTypeLabels.assignment_changed",
    "workspaces.app.cases.detail.activityTypeLabels.comment_created",
    "workspaces.app.cases.detail.activityTypeLabels.comment_deleted",
    "workspaces.app.cases.detail.deleteTitle",
    "workspaces.app.cases.detail.deleteWarning",
    "workspaces.app.cases.detail.deleteButton",
    "workspaces.app.cases.detail.confirmDeleteButton",
    "workspaces.app.cases.detail.cancelDeleteButton",
    "workspaces.app.cases.detail.deleting",
    "workspaces.app.cases.detail.deleteError",
    "workspaces.app.cases.detail.deleteNotFound",
    "workspaces.app.cases.detail.statusOptions.open",
    "workspaces.app.cases.detail.statusOptions.pending",
    "workspaces.app.cases.detail.statusOptions.resolved",
    "workspaces.app.cases.detail.statusOptions.closed",
    "workspaces.app.cases.detail.priorityOptions.low",
    "workspaces.app.cases.detail.priorityOptions.normal",
    "workspaces.app.cases.detail.priorityOptions.high",
    "workspaces.app.cases.detail.priorityOptions.urgent",
    "workspaces.app.cases.detail.sourceOptions.manual",
    "workspaces.app.cases.detail.sourceOptions.email",
    "workspaces.app.cases.detail.sourceOptions.chat",
    "workspaces.app.cases.detail.sourceOptions.phone",
    "workspaces.app.cases.detail.sourceOptions.web",
    "workspaces.app.cases.detail.sourceOptions.import",
    "workspaces.app.placeholders.dashboard.title",
    "workspaces.app.placeholders.dashboard.description",
    "workspaces.app.placeholders.dashboard.notImplemented",
    "workspaces.app.placeholders.dashboard.future",
    "workspaces.app.placeholders.cases.title",
    "workspaces.app.placeholders.cases.description",
    "workspaces.app.placeholders.cases.notImplemented",
    "workspaces.app.placeholders.cases.future",
    "workspaces.app.placeholders.customers.title",
    "workspaces.app.placeholders.customers.description",
    "workspaces.app.placeholders.customers.notImplemented",
    "workspaces.app.placeholders.customers.future",
    "workspaces.app.placeholders.settings.title",
    "workspaces.app.placeholders.settings.description",
    "workspaces.app.placeholders.settings.notImplemented",
    "workspaces.app.placeholders.settings.future",
  ];

  for (const key of requiredWorkspaceKeys) {
    assert.ok(kaKeys.includes(key), `ka.json missing key: ${key}`);
    assert.ok(enKeys.includes(key), `en.json missing key: ${key}`);
  }
});
