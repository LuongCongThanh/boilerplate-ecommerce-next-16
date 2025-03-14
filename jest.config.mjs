/** @type {import('jest').Config} */
const config = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testEnvironment: "jest-environment-jsdom",
  transform: {
    "^.+\\.(ts|tsx)$": "ts-jest", // Transform TypeScript with ts-jest
    "^.+\\.(css|less|sass|scss)$": "jest-transform-stub",
    "^.+\\.(svg|png|jpg|jpeg|gif)$": "jest-transform-stub",
  },
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "\\.(css|less|sass|scss)$": "identity-obj-proxy",
    "\\.(jpg|jpeg|png|gif|webp|svg)$": "<rootDir>/__mocks__/fileMock.js",
    "^next-navigation-guard$": "<rootDir>/__mocks__/next-navigation-guard.ts",
  },
  transformIgnorePatterns: [
    "node_modules/(?!(shadcn|shadcn-ui|tailwindcss|rc-.+?))/",
  ],
  collectCoverage: true,
  collectCoverageFrom: [
    "app/**/*.{js,jsx,ts,tsx}",
    "components/**/*.{js,jsx,ts,tsx}",
    "src/**/*.{js,jsx,ts,tsx}",
    "pages/**/*.{js,jsx,ts,tsx}",
    "hooks/**/*.{js,jsx,ts,tsx}",
    "utils/**/*.{js,jsx,ts,tsx}",
    "!<rootDir>/**/*.d.ts",
  ],
  coverageDirectory: "coverage",
  coverageReporters: ["html", "text", "lcov", "json"],
  testResultsProcessor: "jest-sonar-reporter",
};

export default config;
