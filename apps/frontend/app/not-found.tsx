import Link from "next/link";

export default function NotFound() {
  return (
    <html lang="en">
      <body className="not-found">
        <main>
          <h1>404</h1>
          <p>Page not found.</p>
          <Link href="/ka">Go to Georgian CX Platform</Link>
        </main>
      </body>
    </html>
  );
}
