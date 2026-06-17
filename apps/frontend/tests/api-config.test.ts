import assert from "node:assert/strict";
import { test } from "node:test";

import { apiUrl, getApiBaseUrl } from "../src/lib/api/config";

test("getApiBaseUrl returns empty string when NEXT_PUBLIC_API_URL is unset", () => {
  const original = process.env.NEXT_PUBLIC_API_URL;
  delete process.env.NEXT_PUBLIC_API_URL;

  try {
    assert.equal(getApiBaseUrl(), "");
  } finally {
    if (original === undefined) {
      delete process.env.NEXT_PUBLIC_API_URL;
    } else {
      process.env.NEXT_PUBLIC_API_URL = original;
    }
  }
});

test("getApiBaseUrl trims trailing slash from configured URL", () => {
  const original = process.env.NEXT_PUBLIC_API_URL;
  process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000/";

  try {
    assert.equal(getApiBaseUrl(), "http://localhost:8000");
  } finally {
    if (original === undefined) {
      delete process.env.NEXT_PUBLIC_API_URL;
    } else {
      process.env.NEXT_PUBLIC_API_URL = original;
    }
  }
});

test("apiUrl builds relative paths when base URL is empty", () => {
  const original = process.env.NEXT_PUBLIC_API_URL;
  delete process.env.NEXT_PUBLIC_API_URL;

  try {
    assert.equal(apiUrl("/api/v1/auth/login"), "/api/v1/auth/login");
  } finally {
    if (original === undefined) {
      delete process.env.NEXT_PUBLIC_API_URL;
    } else {
      process.env.NEXT_PUBLIC_API_URL = original;
    }
  }
});

test("apiUrl builds absolute paths when base URL is configured", () => {
  const original = process.env.NEXT_PUBLIC_API_URL;
  process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";

  try {
    assert.equal(
      apiUrl("/api/v1/auth/login"),
      "http://localhost:8000/api/v1/auth/login",
    );
  } finally {
    if (original === undefined) {
      delete process.env.NEXT_PUBLIC_API_URL;
    } else {
      process.env.NEXT_PUBLIC_API_URL = original;
    }
  }
});
