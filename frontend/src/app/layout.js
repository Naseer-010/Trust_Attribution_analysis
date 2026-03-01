import "./globals.css";

export const metadata = {
  title: "Human–AI Trust Experimentation Engine",
  description:
    "Modular platform for studying trust calibration in AI-assisted decision systems. GSoC 2026.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <div className="app-container">{children}</div>
      </body>
    </html>
  );
}
