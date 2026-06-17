"use client";

import { useState, type FormEvent } from "react";

import { useTranslations } from "next-intl";

import { Link, useRouter } from "@/i18n/navigation";

import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/lib/api/errors";

export function RegisterForm() {
  const t = useTranslations("auth.register");
  const router = useRouter();
  const { register } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await register({
        email,
        password,
        full_name: fullName.trim() || null,
      });
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
        <span>{t("fullNameLabel")}</span>
        <input
          type="text"
          name="fullName"
          autoComplete="name"
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
        />
      </label>

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
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <small>{t("passwordHint")}</small>
      </label>

      <button type="submit" className="auth-submit" disabled={isSubmitting}>
        {isSubmitting ? t("submitting") : t("submit")}
      </button>

      <p className="auth-form-footer">
        {t("hasAccount")}{" "}
        <Link href="/login">{t("loginLink")}</Link>
      </p>
    </form>
  );
}
