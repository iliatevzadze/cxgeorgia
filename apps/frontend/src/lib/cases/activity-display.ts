import type { CaseActivityRead, CaseActivityType } from "./types";

export function formatAssignmentEndpoint(
  value: unknown,
  unassignedLabel: string,
): string {
  if (value === null || value === undefined || value === "") {
    return unassignedLabel;
  }
  return String(value);
}

export function formatFromToSummary(
  metadata: Record<string, unknown>,
  formatValue: (value: unknown) => string,
): string | null {
  if (!("from" in metadata) || !("to" in metadata)) {
    return null;
  }
  const from = formatValue(metadata.from);
  const to = formatValue(metadata.to);
  return `${from} → ${to}`;
}

export function formatChangedFieldsSummary(
  metadata: Record<string, unknown>,
): string | null {
  const fields = metadata.changed_fields;
  if (!Array.isArray(fields) || fields.length === 0) {
    return null;
  }
  return fields.map(String).join(", ");
}

export function formatCaseCreatedSummary(
  metadata: Record<string, unknown>,
  formatField: (key: string, value: unknown) => string,
): string | null {
  const parts: string[] = [];
  for (const key of ["title", "status", "priority", "source"]) {
    if (key in metadata && metadata[key] !== undefined && metadata[key] !== null) {
      parts.push(formatField(key, metadata[key]));
    }
  }
  return parts.length > 0 ? parts.join(" · ") : null;
}

export function formatCommentActivitySummary(
  metadata: Record<string, unknown>,
  internalLabel: string,
  publicLabel: string,
): string | null {
  if (!("is_internal" in metadata)) {
    return null;
  }
  return metadata.is_internal ? internalLabel : publicLabel;
}

export function formatTagActivitySummary(
  metadata: Record<string, unknown>,
): string | null {
  const parts: string[] = [];
  if ("tag_name" in metadata && metadata.tag_name) {
    parts.push(String(metadata.tag_name));
  }
  if ("tag_slug" in metadata && metadata.tag_slug) {
    parts.push(String(metadata.tag_slug));
  }
  return parts.length > 0 ? parts.join(" · ") : null;
}

export function getActivityMetadataSummary(
  activity: Pick<CaseActivityRead, "activity_type" | "metadata">,
  options: {
    unassignedLabel: string;
    internalLabel: string;
    publicLabel: string;
    formatEnumValue: (field: string, value: unknown) => string;
    formatCreatedField: (key: string, value: unknown) => string;
  },
): string | null {
  const { metadata, activity_type: activityType } = activity;

  switch (activityType as CaseActivityType) {
    case "status_changed":
    case "priority_changed":
      return formatFromToSummary(metadata, (value) =>
        options.formatEnumValue(activityType, value),
      );
    case "assignment_changed":
      return formatFromToSummary(metadata, (value) =>
        formatAssignmentEndpoint(value, options.unassignedLabel),
      );
    case "case_updated":
      return formatChangedFieldsSummary(metadata);
    case "case_created":
      return formatCaseCreatedSummary(metadata, options.formatCreatedField);
    case "comment_created":
    case "comment_deleted":
      return formatCommentActivitySummary(
        metadata,
        options.internalLabel,
        options.publicLabel,
      );
    case "tag_attached":
    case "tag_detached":
      return formatTagActivitySummary(metadata);
    default:
      return null;
  }
}
