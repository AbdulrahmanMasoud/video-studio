import Link from "next/link";

export default function NotFound() {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui", padding: 40 }}>
        <h1>404</h1>
        <p>Page not found.</p>
        <Link href="/en">Home</Link>
      </body>
    </html>
  );
}
