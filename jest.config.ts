import type { Config } from 'jest';
import nextJest from 'next/jest.js';

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

const config: Config = {
  coverageProvider: 'v8',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['./jest.setup.ts'],
  transform: {
    "^.+\\.(js|jsx|ts|tsx)$": ["@swc/jest", {
      jsc: {
        transform: {
          react: {
            runtime: "automatic"
          }
        },
        parser: {
          syntax: "typescript",
          tsx: true,
          decorators: false,
          dynamicImport: false
        }
      }
    }],
  },
  moduleNameMapper: {
    // Handle CSS imports (with CSS modules)
    "^.+\\.module\\.(css|sass|scss)$": "identity-obj-proxy",
    
    // Handle CSS imports (without CSS modules)
    "^.+\\.(css|sass|scss)$": "<rootDir>/__mocks__/styleMock.js",
    
    // Handle image imports
    "\\.(jpg|jpeg|png|gif|webp)$": "<rootDir>/__mocks__/fileMock.ts",
    
    // Handle SVG imports
    "\\.svg$": "<rootDir>/__mocks__/svgMock.ts",
    
    // Handle module path aliases
    "^@/(.*)$": "<rootDir>/src/$1",
    
    // Mock next-navigation-guard
    "^next-navigation-guard$": "<rootDir>/__mocks__/next-navigation-guard.ts",
  },
  transformIgnorePatterns: [
    "/node_modules/(?!(@radix-ui|@shadcn|shadcn-ui|tailwindcss|rc-.+?))/",
  ],
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/_*.{js,jsx,ts,tsx}',
    '!src/**/index.{js,jsx,ts,tsx}',
    '!**/node_modules/**',
  ],
  coverageDirectory: "coverage",
  coverageReporters: ["html", "text", "lcov", "json"],
  testResultsProcessor: "jest-sonar-reporter",
  extensionsToTreatAsEsm: ['.ts', '.tsx'],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  testMatch: ['**/__tests__/**/*.test.[jt]s?(x)', '**/?(*.)+(test).[jt]s?(x)'],
  testPathIgnorePatterns: ['<rootDir>/node_modules/', '<rootDir>/.next/'],
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname',
  ],};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
export default createJestConfig(config)