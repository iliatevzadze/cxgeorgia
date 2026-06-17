"use client";

import { useState, type FormEvent } from "react";

import { useTranslations } from "next-intl";

import { Link, useRouter } from "@/i18n/navigation";

import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/lib/api/errors";

export function LoginForm() {
  const t = useTranslations("auth.login");
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await login({ email, password });
      router.push("/account");
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage(t("genericError"));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h1>{t("title")}</h1>
      <p className="auth-form-description">{t("description")}</p>

      {errorMessage ? (
        <p className="auth-form-error" role="alert">
          {errorMessage}
        </p>
      ) : null}

      <label className="auth-field">
        <span>{t("emailLabel")}</span>
        <input
          type="email"
          name="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
      </label>

      <label className="auth-field">
        <span>{t("passwordLabel")}</span>
        <input
          type="password"
          name="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </label>

      <button type="submit" className="auth-submit" disabled={isSubmitting}>
        {isSubmitting ? t("submitting") : t("submit")}
      </button>

      <p className="auth-form-footer">
        {t("noAccount")}{" "}
        <Link href="/register">{t("registerLink")}</Link>
      </p>
    </form>
  );
}
