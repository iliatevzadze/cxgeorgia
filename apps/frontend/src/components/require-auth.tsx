"use client";

import { useEffect, type ReactNode } from "react";

import { useTranslations } from "next-intl";

import { useRouter } from "@/i18n/navigation";

import { useAuth } from "@/hooks/use-auth";

type RequireAuthProps = {
  children: ReactNode;
};

export function RequireAuth({ children }: RequireAuthProps) {
  const t = useTranslations("auth.common");
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return <p className="auth-status">{t("loading")}</p>;
  }

  if (!isAuthenticated) {
    return null;
  }

  return children;
}
