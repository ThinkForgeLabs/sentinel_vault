import js from "@eslint/js";

export default [
  js.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      "no-unused-vars": "warn",
    },
  },
];