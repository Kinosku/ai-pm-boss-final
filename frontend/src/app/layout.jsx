import "../styles/globals.css";

export const metadata = {
  title: "AI PM Boss",
  description: "AI-powered project management system",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        {/* Google Fonts */}
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Sans&family=Space+Mono&family=Space+Grotesk&display=swap"
          rel="stylesheet"
        />

        {/* Material Icons */}
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined"
          rel="stylesheet"
        />
      </head>

      <body>{children}</body>
    </html>
  );
}