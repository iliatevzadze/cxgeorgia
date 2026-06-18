import assert from "node:assert/strict";
import { test } from "node:test";

import {
  formatAssignmentEndpoint,
  formatCaseCreatedSummary,
  formatChangedFieldsSummary,
  formatCommentActivitySummary,
  formatFromToSummary,
  getActivityMetadataSummary,
} from "../src/lib/cases/activity-display";

test("formatFromToSummary renders from and to values", () => {
  const summary = formatFromToSummary(
    { from: "open", to: "pending" },
    String,
  );
  assert.equal(summary, "open → pending");
});

test("formatAssignmentEndpoint renders null as unassigned label", () => {
  assert.equal(formatAssignmentEndpoint(null, "Unassigned"), "Unassigned");
  assert.equal(
    formatAssignmentEndpoint("user-1", "Unassigned"),
    "user-1",
  );
});

test("formatChangedFieldsSummary joins changed field names", () => {
  const summary = formatChangedFieldsSummary({
    changed_fields: ["title", "description"],
  });
  assert.equal(summary, "title, description");
});

test("formatCaseCreatedSummary includes available created metadata", () => {
  const summary = formatCaseCreatedSummary(
    {
      title: "Support request",
      status: "open",
      priority: "normal",
      source: "email",
    },
    (key, value) => `${key}:${String(value)}`,
  );
  assert.equal(
    summary,
    "title:Support request · status:open · priority:normal · source:email",
  );
});

test("formatCommentActivitySummary renders internal or public visibility", () => {
  assert.equal(
    formatCommentActivitySummary({ is_internal: true }, "Internal", "Public"),
    "Internal",
  );
  assert.equal(
    formatCommentActivitySummary({ is_internal: false }, "Internal", "Public"),
    "Public",
  );
});

test("getActivityMetadataSummary renders status and priority changes", () => {
  const options = {
    unassignedLabel: "Unassigned",
    internalLabel: "Internal",
    publicLabel: "Public",
    formatEnumValue: (_field: string, value: unknown) => String(value),
    formatCreatedField: (key: string, value: unknown) =>
      `${key}:${String(value)}`,
  };

  assert.equal(
    getActivityMetadataSummary(
      {
        activity_type: "status_changed",
        metadata: { from: "open", to: "pending" },
      },
      options,
    ),
    "open → pending",
  );
  assert.equal(
    getActivityMetadataSummary(
      {
        activity_type: "priority_changed",
        metadata: { from: "normal", to: "high" },
      },
      options,
    ),
    "normal → high",
  );
});

test("getActivityMetadataSummary renders assignment and case updated metadata", () => {
  const options = {
    unassignedLabel: "Unassigned",
    internalLabel: "Internal",
    publicLabel: "Public",
    formatEnumValue: (_field: string, value: unknown) => String(value),
    formatCreatedField: (key: string, value: unknown) =>
      `${key}:${String(value)}`,
  };

  assert.equal(
    getActivityMetadataSummary(
      {
        activity_type: "assignment_changed",
        metadata: { from: null, to: "user-1" },
      },
      options,
    ),
    "Unassigned → user-1",
  );
  assert.equal(
    getActivityMetadataSummary(
      {
        activity_type: "case_updated",
        metadata: { changed_fields: ["title"] },
      },
      options,
    ),
    "title",
  );
});
