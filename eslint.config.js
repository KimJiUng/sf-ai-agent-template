import lwc from "@salesforce/eslint-config-lwc/recommended";
import importPlugin from "eslint-plugin-import";

export default [
  ...lwc,
  {
    plugins: {
      import: importPlugin,
    },
    rules: {
      "no-console": "warn",
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    },
  },
  {
    ignores: [
      "**/node_modules/**",
      "**/.sfdx/**",
      "**/.sf/**",
      "**/logs/**",
      "**/output/**",
      "**/tmp/**",
    ],
  },
];
