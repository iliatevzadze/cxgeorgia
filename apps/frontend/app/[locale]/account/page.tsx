import { setRequestLocale } from "next-intl/server";

import { AccountPanel } from "@/components/account-panel";

type AccountPageProps = {
  params: Promise<{ locale: string }>;
};

export default async function AccountPage({ params }: AccountPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <main className="page auth-page">
      <AccountPanel />
    </main>
  );
}
