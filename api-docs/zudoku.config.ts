import type { ZudokuConfig } from "zudoku";

const config: ZudokuConfig = {
  site: {
    title: "TatvaCare CRM API",
    showPoweredBy: false,
  },
  basePath: "/docs",
  navigation: [
    {
      type: "category",
      label: "Documentation",
      icon: "book",
      items: [
        { type: "category", label: "Start here", items: ["introduction", "welcome", "quickstart"] },
        { type: "category", label: "Frappe in plain English", items: ["frappe-doctypes", "frappe-child-tables", "frappe-rest-api", "frappe-discovery", "frappe-permissions"] },
        { type: "category", label: "Architecture", items: ["concepts"] },
        { type: "category", label: "Channels", items: ["whatsapp", "telephony"] },
        { type: "category", label: "Administration", items: ["users", "roles-and-permissions"] },
        { type: "category", label: "Reference", items: ["errors", "operations", "tags"] },
      ],
    },
    { type: "link", to: "/api", label: "API Reference", icon: "code" },
  ],
  redirects: [{ from: "/", to: "/introduction" }],
  apis: {
    type: "file",
    input: "./openapi.json",
    path: "/api",
  },
  docs: {
    files: "/pages/**/*.{md,mdx}",
  },
};

export default config;
