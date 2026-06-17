export type WorkspaceAppSection =
  | "home"
  | "dashboard"
  | "cases"
  | "customers"
  | "settings";

export type WorkspaceAppPlaceholderSection = Exclude<
  WorkspaceAppSection,
  "home"
>;
