import "@/styles/globals.css";
import { AuthProvider } from "@/context/AuthContext";

export const metadata = {
  title: "AI PM Boss",
  description: "The World's First Autonomous AI Project Manager for Software Teams",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Mono&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-background text-on-surface font-body min-h-screen antialiased">
        <div className="grain-overlay" />
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
