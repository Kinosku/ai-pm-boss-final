import "../styles/globals.css";
import { AuthProvider } from "../context/AuthContext";

export const metadata = {
  title: "AI PM Boss",
  description: "Autonomous AI Project Manager",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
