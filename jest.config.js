module.exports = {
  setupFilesAfterEnv: ["./jest.setup.js"],
  testEnvironment: "jest-environment-jsdom",
  transform: {
    "^.+\\.(css|less|sass|scss)$": "jest-transform-stub",
    "^.+\\.(svg|png|jpg|jpeg|gif)$": "jest-transform-stub",
  },
  moduleNameMapper: {
    "\\.(css|less|sass|scss)$": "identity-obj-proxy",
    "\\.(png|jpg|jpeg|gif)$": "jest-transform-stub",
    "\\.(jpg|jpeg|png|gif|webp|svg)$": "<rootDir>/__mocks__/fileMock.ts",
    "^@/(.*)$": "<rootDir>/$1",
    "\\.svg$": "<rootDir>/__mocks__/svgMock.ts",
    "^next-navigation-guard$": "<rootDir>/__mocks__/next-navigation-guard.ts",
  },
  transformIgnorePatterns: [
    "node_modules/(?!(shadcn|shadcn-ui|tailwindcss|rc-.+?/)",
  ],
  collectCoverage: true, // Enable coverage collection
  collectCoverageFrom: [
    "app/**/*.{js,jsx,ts,tsx}",
    "components/**/*.{js,jsx,ts,tsx}",
    "configs/**/*.{js,jsx,ts,tsx}",
    "services/**/*.{js,jsx,ts,tsx}",
    "recoil/**/*.{js,jsx,ts,tsx}",
    "shared/**/*.{js,jsx,ts,tsx}",
    "utils/**/*.{js,jsx,ts,tsx}",
    "!<rootDir>/**/*.d.ts",
  ],
  coverageDirectory: "coverage", // Directory to output coverage reports
  coverageReporters: ["html", "text", "lcov", "json"],
  testResultsProcessor: "jest-sonar-reporter",
};
//  "node_modules/(?!(antd|@ant-design|rc-.+?|/)"